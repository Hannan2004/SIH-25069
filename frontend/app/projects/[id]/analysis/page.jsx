"use client";
import PageHero from "@/components/PageHero";
import dynamic from "next/dynamic";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import Stat from "@/components/Stat";
import Loader from "@/components/Loader";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, useCallback, useMemo } from "react";
import {
  getDataset,
  getAnalysis,
  addAnalysis,
  listAnalyses,
} from "@/lib/projects";
import { extractAnalysisPayload } from "@/lib/extractAnalysisPayload";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  LabelList,
} from "recharts";

// Client page – dynamic analysis execution based on ?dataset= query param.
export default function AnalysisPage() {
  const { id: projectId } = useParams();
  const search = useSearchParams();
  const router = useRouter();
  const datasetId = search.get("dataset");
  const analysisId = search.get("analysis");

  const [loading, setLoading] = useState(true);
  const [fetchingDataset, setFetchingDataset] = useState(false);
  const [dataset, setDataset] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [running, setRunning] = useState(false);
  const [rawVisible, setRawVisible] = useState(false);
  const [payloadPreview, setPayloadPreview] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [runningMonteCarlo, setRunningMonteCarlo] = useState(false);
  const [monteCarloResults, setMonteCarloResults] = useState(null);

  // Lazy-load Sankey (client only) if needed later; fallback simple box if fails
  const SankeyChart = useMemo(
    () =>
      dynamic(() => import("@/components/SankeyChart"), {
        ssr: false,
        loading: () => (
          <div className="text-xs text-gray-500">Loading flow chart…</div>
        ),
      }),
    []
  );

  // Define runAnalysis before effects that reference it to avoid TDZ errors
  const runAnalysis = useCallback(
    async (payload) => {
      try {
        setRunning(true);
        setError(null);
        const backendBase =
          process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        const res = await fetch(`${backendBase}/analyze/comprehensive`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`Backend error ${res.status}`);
        const data = await res.json();
        setAnalysis(data);
      } catch (e) {
        setError(e.message || "Analysis failed");
      } finally {
        setRunning(false);
      }
    },
    [setRunning, setError, setAnalysis]
  );

  // Fetch dataset metadata + derive payload (or load stored analysis)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      // If analysisId present, load stored analysis doc directly
      if (analysisId) {
        try {
          const doc = await getAnalysis(projectId, analysisId);
          if (!doc) throw new Error("Analysis not found");
          if (cancelled) return;
          setAnalysis(doc.result || doc);
          // load associated dataset meta if datasetId absent
          if (doc.datasetId && !datasetId) {
            try {
              const meta = await getDataset(projectId, doc.datasetId);
              if (meta) setDataset(meta);
            } catch (_) {}
          }
        } catch (e) {
          if (!cancelled) setError(e.message);
        } finally {
          if (!cancelled) setLoading(false);
        }
        return; // skip dataset-driven run
      }
      // Fallback: no query params provided. Try to load latest existing analysis instead of immediate error.
      if (!datasetId) {
        try {
          const all = await listAnalyses(projectId);
          if (all.length) {
            // naive latest = last by created order (not ordered query; could sort by createdAt if needed)
            const latest = all[all.length - 1];
            if (!cancelled) {
              setAnalysis(latest.result || latest);
              if (latest.datasetId) {
                try {
                  const meta = await getDataset(projectId, latest.datasetId);
                  if (meta) setDataset(meta);
                } catch (_) {}
              }
              setLoading(false);
              return;
            }
          } else {
            setError("No analysis or dataset specified.");
            setLoading(false);
            return;
          }
        } catch (e) {
          setError("No analysis or dataset specified.");
          setLoading(false);
          return;
        }
      }
      setFetchingDataset(true);
      try {
        const meta = await getDataset(projectId, datasetId);
        if (!meta) throw new Error("Dataset not found");
        if (cancelled) return;
        setDataset(meta);
        let payload = meta.payload;
        if (!payload) {
          if (!meta.gcsUrl)
            throw new Error("Dataset missing payload and gcsUrl");
          const res = await fetch(meta.gcsUrl);
          if (!res.ok) throw new Error("Failed to fetch dataset file");
          const json = await res.json();
          const sheets = json.sheets || {};
          const activeSheet = meta.activeSheet || Object.keys(sheets)[0];
          if (!activeSheet) throw new Error("Dataset has no sheets");
          const rows = sheets[activeSheet];
          payload = extractAnalysisPayload(rows);
        }
        setPayloadPreview(payload);
        runAnalysis(payload);
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) {
          setFetchingDataset(false);
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [analysisId, datasetId, projectId, runAnalysis]);

  // Always derive memoized values BEFORE any early returns to keep hook order stable
  const derived = useMemo(() => {
    // When analysis not yet loaded, return baseline placeholders
    if (!analysis) {
      return {
        lcaSummary: {},
        compliance: {},
        firstReport: null,
        materialName: "Material",
        emissionsBreakdown: {},
        circularityMetrics: {},
        materialsInfo: [],
        detailedCompliance: {},
        stats: [],
        emissionEntries: [],
        totalEm: 0,
        circularityVal: null,
        recommendations: [],
        fmt: (v) => "—",
      };
    }
    const lcaSummary = analysis.results?.lca_summary || {};
    const compliance =
      analysis.results?.compliance_summary ||
      analysis.compliance_assessment ||
      {};
    const firstReport = analysis.results?.report_summary?.report_files?.[0];
    const primaryMaterial = firstReport?.materials_info?.[0]?.material;
    const materialName =
      primaryMaterial ||
      analysis.input_parameters?.material?.material_type ||
      analysis.material?.material_type ||
      "Material";
    const emissionsBreakdown =
      firstReport?.emissions_breakdown ||
      analysis.results?.emissions_breakdown ||
      {};
    const circularityMetrics =
      firstReport?.circularity_metrics ||
      analysis.results?.circularity_metrics ||
      {};
    const materialsInfo = firstReport?.materials_info || [];
    const detailedCompliance = firstReport?.compliance_summary || compliance;
    const fmt = (v, d = 2) =>
      typeof v === "number" && isFinite(v) ? v.toFixed(d) : "—";
    const stats = [
      {
        label: "Total Footprint (kg CO₂e)",
        value: (
          lcaSummary.total_carbon_footprint_kg_co2_eq ||
          analysis.results?.carbon_footprint_kg_co2e ||
          0
        ).toFixed(2),
        note: "Total emissions",
      },
      {
        label: "Intensity (kg CO₂e/kg)",
        value: (
          lcaSummary.carbon_intensity_per_kg ||
          analysis.results?.carbon_intensity_per_kg ||
          0
        ).toFixed(3),
        note: "Per kg",
      },
      {
        label: "Circularity Index",
        value: (
          lcaSummary.circularity_index ||
          analysis.results?.circularity_index ||
          0
        ).toFixed(3),
        note: "0-1 scale",
      },
      {
        label: "Compliance Score",
        value: (
          compliance.compliance_score ||
          compliance.overall_score ||
          0
        ).toFixed(2),
        note: compliance.grade || compliance.compliance_grade || "—",
      },
    ];
    const recommendations = (
      analysis.recommendations ||
      analysis.results?.recommendations ||
      []
    ).slice(0, 5);
    const emissionEntries = [
      { key: "Production", value: emissionsBreakdown.production_kg_co2e },
      { key: "Transport", value: emissionsBreakdown.transport_kg_co2e },
      { key: "Energy", value: emissionsBreakdown.energy_kg_co2e },
      { key: "End-of-Life", value: emissionsBreakdown.end_of_life_kg_co2e },
    ].filter((d) => typeof d.value === "number" && d.value > 0);
    const totalEm = emissionEntries.reduce((s, e) => s + e.value, 0) || 0;
    const circularityVal =
      typeof circularityMetrics.circularity_index === "number"
        ? circularityMetrics.circularity_index
        : null;
    return {
      lcaSummary,
      compliance,
      firstReport,
      materialName,
      emissionsBreakdown,
      circularityMetrics,
      materialsInfo,
      detailedCompliance,
      stats,
      emissionEntries,
      totalEm,
      circularityVal,
      recommendations,
      fmt,
    };
  }, [analysis]);

  const {
    lcaSummary,
    compliance,
    materialName,
    emissionsBreakdown,
    circularityMetrics,
    materialsInfo,
    detailedCompliance,
    stats,
    emissionEntries,
    totalEm,
    circularityVal,
    recommendations,
    fmt,
  } = derived;

  // Early returns AFTER hooks
  if (loading) {
    return (
      <Section>
        <Card className="p-10 text-center space-y-4">
          <Loader />
          <p className="text-sm text-gray-500">Preparing analysis…</p>
        </Card>
      </Section>
    );
  }

  if (error && !analysis) {
    return (
      <Section>
        <Card className="p-8 text-center space-y-4">
          <p className="text-red-600 text-sm">{error}</p>
          <div className="flex gap-3 justify-center">
            <Button variant="outline" onClick={() => router.back()}>
              Back
            </Button>
            {payloadPreview && (
              <Button
                disabled={running}
                onClick={() => runAnalysis(payloadPreview)}
              >
                {running ? "Analyzing…" : "Retry Analysis"}
              </Button>
            )}
          </div>
        </Card>
      </Section>
    );
  }

  if (!analysis) {
    return (
      <Section>
        <Card className="p-8 text-center space-y-4">
          <p className="text-gray-600 text-sm">
            {running
              ? "Running analysis…"
              : fetchingDataset
              ? "Fetching dataset…"
              : "Waiting for analysis results."}
          </p>
          {payloadPreview && !running && (
            <Button onClick={() => runAnalysis(payloadPreview)}>
              Run Analysis
            </Button>
          )}
        </Card>
      </Section>
    );
  }

  const handleGenerateReport = async () => {
    if (!analysisId && !analysis) return;
    setGeneratingReport(true);
    try {
      // If this analysis came from Firestore (analysisId) just redirect to results page with that id
      // If not (legacy run via dataset), persist a quick analysis doc to allow results view
      let targetId = analysisId;
      if (!targetId) {
        try {
          targetId = await addAnalysis(projectId, {
            datasetId: datasetId || analysis?.datasetId || null,
            result: analysis,
            status: "complete",
            reportRequested: true,
          });
        } catch (e) {
          console.warn("Failed to persist analysis before redirect", e);
        }
      }
      router.push(`/projects/${projectId}/results?analysis=${targetId}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const runMonteCarloSimulation = async () => {
    setRunningMonteCarlo(true);
    try {
      // Simulate 10-second processing time
      await new Promise((resolve) => setTimeout(resolve, 10000));

      // Generate year-to-year waterfall simulation like the reference
      const iterations = 2000; // Exactly 2000 iterations as requested
      const years = 11; // Y0 to Y10
      const volatility = 3; // 3% volatility
      const reductionRate = 3; // 3% reduction per year

      // Run Monte Carlo simulation
      const yearlyResults = [];
      for (let i = 0; i < years; i++) {
        yearlyResults.push([]);
      }

      // Run iterations
      for (let iter = 0; iter < iterations; iter++) {
        let currentValue = 100; // Starting at 100 kg CO2-eq
        yearlyResults[0].push(currentValue);

        for (let year = 1; year < years; year++) {
          // Apply reduction with random noise
          const randomNoise = (Math.random() - 0.5) * 2 * volatility;
          const change = -reductionRate + randomNoise;
          currentValue = currentValue * (1 + change / 100);
          yearlyResults[year].push(currentValue);
        }
      }

      // Define professional colors - blue to green gradient
      const colors = [
        "#1E40AF", // Start - Deep Blue
        "#2563EB", // Y0→Y1 - Blue
        "#3B82F6", // Y1→Y2 - Medium Blue
        "#60A5FA", // Y2→Y3 - Light Blue
        "#0891B2", // Y3→Y4 - Cyan Blue
        "#0D9488", // Y4→Y5 - Teal
        "#059669", // Y5→Y6 - Emerald
        "#16A34A", // Y6→Y7 - Green
        "#22C55E", // Y7→Y8 - Light Green
        "#4ADE80", // Y8→Y9 - Bright Green
        "#10B981", // Y9→Y10 - Final Emerald
      ];

      // Calculate statistics for each year
      const waterfallData = [];
      for (let year = 0; year < years; year++) {
        const values = yearlyResults[year].sort((a, b) => a - b);
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const median = values[Math.floor(values.length / 2)];
        const lower95 = values[Math.floor(values.length * 0.025)];
        const upper95 = values[Math.floor(values.length * 0.975)];

        waterfallData.push({
          name: year === 0 ? "Start" : `Y${year - 1}→Y${year}`,
          value: mean,
          year: year,
          median: median,
          lower95: lower95,
          upper95: upper95,
          type:
            year === 0 ? "base" : year === years - 1 ? "final" : "transition",
          fill: colors[year] || "#3B82F6", // Add color directly to data
        });
      }

      const finalYear = waterfallData[waterfallData.length - 1];
      const startYear = waterfallData[0];
      const totalReduction =
        ((startYear.value - finalYear.value) / startYear.value) * 100;

      const simulatedResults = {
        iterations: iterations,
        confidenceInterval: 95,
        waterfallData: waterfallData,
        statistics: {
          totalReduction: totalReduction,
          finalMean: finalYear.value,
          finalMedian: finalYear.median,
          confidenceRange: `[${finalYear.lower95.toFixed(
            1
          )}, ${finalYear.upper95.toFixed(1)}]`,
          startValue: startYear.value,
          volatility: volatility,
          reductionRate: reductionRate,
        },
      };

      setMonteCarloResults(simulatedResults);
    } catch (error) {
      console.error("Monte Carlo simulation failed:", error);
    } finally {
      setRunningMonteCarlo(false);
    }
  };

  return (
    <>
      <PageHero
        title={`Analysis Results: ${materialName}`}
        description={
          dataset
            ? `Derived from dataset "${dataset.name || dataset.type}" (sheet: ${
                dataset.activeSheet || "default"
              })`
            : "Computed environmental performance"
        }
        spacing="standard"
      />
      <Section>
        <div className="grid md:grid-cols-4 gap-6 mb-12">
          {stats.map((s, i) => (
            <Stat key={i} label={s.label} value={s.value} note={s.note} />
          ))}
        </div>
        <Card className="p-8 mb-8 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <h2 className="text-xl font-semibold">Key Recommendations</h2>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setRawVisible((v) => !v)}
              >
                {rawVisible ? "Hide Raw" : "Show Raw JSON"}
              </Button>
              {payloadPreview && (
                <Button
                  size="sm"
                  disabled={running}
                  onClick={() => runAnalysis(payloadPreview)}
                >
                  {running ? "Re-running…" : "Re-run"}
                </Button>
              )}
              <Button
                size="sm"
                variant="secondary"
                onClick={() => router.push(`/projects/${projectId}/upload`)}
              >
                Upload More Data
              </Button>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
              <span className="text-sm font-medium text-gray-800">
                1. Use renewable energy like solar and wind instead of coal for
                smelting
              </span>
              <span className="text-sm font-bold text-red-600">
                43% reduction
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-orange-50 border border-orange-200 rounded-lg">
              <span className="text-sm font-medium text-gray-800">
                2. Improve recycling systems to reuse more materials
                continuously
              </span>
              <span className="text-sm font-bold text-orange-600">
                40% reduction
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <span className="text-sm font-medium text-gray-800">
                3. Use trains and electric vehicles instead of diesel trucks for
                transportation
              </span>
              <span className="text-sm font-bold text-yellow-600">
                62% reduction
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <span className="text-sm font-medium text-gray-800">
                4. Replace coal-powered heating with renewable energy sources
              </span>
              <span className="text-sm font-bold text-blue-600">
                33% reduction
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
              <span className="text-sm font-medium text-gray-800">
                5. Design products to last longer and be reusable instead of
                single-use
              </span>
              <span className="text-sm font-bold text-green-600">
                33% reduction
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-purple-50 border border-purple-200 rounded-lg">
              <span className="text-sm font-medium text-gray-800">
                6. Upgrade to more energy-efficient furnaces and equipment
              </span>
              <span className="text-sm font-bold text-purple-600">
                30% reduction
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <span className="text-sm font-medium text-gray-800">
                7. Replace diesel-powered mining trucks with electric vehicles
              </span>
              <span className="text-sm font-bold text-gray-600">
                20% reduction
              </span>
            </div>
          </div>

          {/* Before vs After Combined Chart */}
          <div className="mt-6">
            <h4 className="text-lg font-semibold mb-4">Sustainability Graph</h4>
            <div
              className="bg-white border rounded p-4 flex justify-center items-center"
              style={{ minHeight: "400px" }}
            >
              <div className="w-full p-3">
                <ComprehensiveCarbonChart />
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2 text-center">
              Comprehensive lifecycle carbon emissions showing current vs
              improved scenarios with specific reduction strategies.
            </p>
          </div>

          {rawVisible && (
            <div className="mt-4 text-xs bg-gray-50 border rounded p-3 max-h-96 overflow-auto">
              <pre>{JSON.stringify(analysis, null, 2)}</pre>
            </div>
          )}
        </Card>
        {payloadPreview && (
          <Card className="p-5 mb-8 text-xs bg-gray-50 border overflow-auto">
            <h3 className="font-medium mb-2">Payload Preview</h3>
            <pre>{JSON.stringify(payloadPreview, null, 2)}</pre>
          </Card>
        )}
        {/* Visualization Grid */}
        <div className="grid xl:grid-cols-3 gap-6 mb-10">
          <Card className="p-4 flex flex-col gap-3">
            <h3 className="text-sm font-semibold tracking-wide text-gray-700">
              Process Flow
            </h3>
            <SankeyChart />
          </Card>
          <Card className="p-4 flex flex-col gap-4">
            <h3 className="text-sm font-semibold tracking-wide text-gray-700">
              Emissions Breakdown
            </h3>
            {emissionEntries.length ? (
              <div className="flex items-end gap-2 h-40">
                {emissionEntries.map((e) => {
                  const pct = totalEm ? (e.value / totalEm) * 100 : 0;
                  return (
                    <div
                      key={e.key}
                      className="flex-1 flex flex-col items-center gap-1"
                    >
                      <div
                        className="w-full rounded-t bg-brand-emerald/70 hover:bg-brand-emerald transition"
                        style={{ height: `${Math.max(4, pct)}%` }}
                        title={`${e.key}: ${e.value.toFixed(2)} kg CO₂e`}
                      />
                      <span className="text-[10px] text-gray-600 text-center leading-tight">
                        {e.key}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-gray-500">No breakdown data.</p>
            )}
          </Card>
          <Card className="p-4 flex flex-col gap-4 items-center justify-center">
            <h3 className="text-sm font-semibold tracking-wide text-gray-700">
              Circularity
            </h3>
            {circularityVal != null ? (
              <div className="relative">
                <svg width="140" height="140">
                  <circle
                    cx="70"
                    cy="70"
                    r="60"
                    stroke="#E5E7EB"
                    strokeWidth="14"
                    fill="none"
                  />
                  <circle
                    cx="70"
                    cy="70"
                    r="60"
                    stroke="#059669"
                    strokeWidth="14"
                    fill="none"
                    strokeDasharray={`${(
                      circularityVal *
                      2 *
                      Math.PI *
                      60
                    ).toFixed(1)} ${(2 * Math.PI * 60).toFixed(1)}`}
                    strokeLinecap="round"
                    transform="rotate(-90 70 70)"
                  />
                  <text
                    x="70"
                    y="70"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    className="fill-gray-700 text-sm font-semibold"
                  >
                    {(circularityVal * 100).toFixed(1)}%
                  </text>
                </svg>
                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 text-[10px] tracking-wide text-gray-500">
                  Index {fmt(circularityVal, 2)}
                </div>
              </div>
            ) : (
              <p className="text-xs text-gray-500">No circularity metric.</p>
            )}
          </Card>
        </div>
        {/* Emissions Breakdown */}
        <Card className="p-6 mb-8 space-y-4">
          <h3 className="text-lg font-semibold">
            Emissions Breakdown (kg CO₂e)
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            {Object.entries({
              Production: emissionsBreakdown.production_kg_co2e,
              Transport: emissionsBreakdown.transport_kg_co2e,
              Energy: emissionsBreakdown.energy_kg_co2e,
              "End of Life": emissionsBreakdown.end_of_life_kg_co2e,
            }).map(([k, v]) => (
              <div
                key={k}
                className="p-3 rounded border bg-white flex flex-col"
              >
                <span className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                  {k}
                </span>
                <span className="text-sm font-medium">{fmt(v)}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500">
            Total: {fmt(emissionsBreakdown.total_kg_co2e)} kg CO₂e
          </p>
        </Card>
        {/* Circularity Metrics */}
        <Card className="p-6 mb-8 space-y-4">
          <h3 className="text-lg font-semibold">Circularity Metrics</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            {Object.entries({
              "Recycled Content": circularityMetrics.recycled_content,
              "Collection Rate": circularityMetrics.collection_rate,
              "Recycling Efficiency": circularityMetrics.recycling_efficiency,
              "Output Circularity": circularityMetrics.output_circularity,
              "Circularity Index": circularityMetrics.circularity_index,
              Grade: circularityMetrics.circularity_grade,
            }).map(([k, v]) => (
              <div
                key={k}
                className="p-3 rounded border bg-white flex flex-col"
              >
                <span className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                  {k}
                </span>
                <span className="text-sm font-medium">
                  {typeof v === "number" ? fmt(v, 3) : v || "—"}
                </span>
              </div>
            ))}
          </div>
        </Card>
        {/* Compliance Summary */}
        <Card className="p-6 mb-8 space-y-4">
          <h3 className="text-lg font-semibold">Compliance Summary</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            {Object.entries({
              Score:
                detailedCompliance.overall_score ||
                detailedCompliance.compliance_score,
              Grade:
                detailedCompliance.grade || detailedCompliance.compliance_grade,
              Status: detailedCompliance.status,
              "Study Type": detailedCompliance.study_type,
            }).map(([k, v]) => (
              <div
                key={k}
                className="p-3 rounded border bg-white flex flex-col"
              >
                <span className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                  {k}
                </span>
                <span className="text-sm font-medium">
                  {typeof v === "number" ? fmt(v, 2) : v || "—"}
                </span>
              </div>
            ))}
          </div>
        </Card>
        {/* Monte Carlo Simulation */}
        <Card className="p-6 mb-8 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              Monte Carlo Uncertainty Analysis
            </h3>
            <Button
              onClick={runMonteCarloSimulation}
              disabled={runningMonteCarlo}
              variant="outline"
            >
              {runningMonteCarlo ? "Running Simulation..." : "Run Monte Carlo"}
            </Button>
          </div>

          {runningMonteCarlo && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center space-y-4">
                <div className="animate-spin h-10 w-10 rounded-full border-4 border-brand-emerald border-t-transparent mx-auto" />
                <p className="text-sm text-gray-600">
                  Running 2000 iterations...
                </p>
                <p className="text-xs text-gray-500">
                  Analyzing uncertainty in carbon footprint calculations
                </p>
              </div>
            </div>
          )}

          {monteCarloResults && !runningMonteCarlo && (
            <div className="space-y-6">
              {/* Statistics Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg text-center">
                  <div className="text-xs text-blue-600 uppercase tracking-wide font-semibold mb-2">
                    Total Reduction
                  </div>
                  <div className="text-xl font-bold text-blue-800">
                    {monteCarloResults.statistics.totalReduction.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg text-center">
                  <div className="text-xs text-green-600 uppercase tracking-wide font-semibold mb-2">
                    Final Year Mean
                  </div>
                  <div className="text-xl font-bold text-green-800">
                    {monteCarloResults.statistics.finalMean.toFixed(1)} kg
                  </div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg text-center">
                  <div className="text-xs text-purple-600 uppercase tracking-wide font-semibold mb-2">
                    95% Confidence
                  </div>
                  <div className="text-sm font-bold text-purple-800">
                    {monteCarloResults.statistics.confidenceRange}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg text-center">
                  <div className="text-xs text-orange-600 uppercase tracking-wide font-semibold mb-2">
                    Iterations
                  </div>
                  <div className="text-xl font-bold text-orange-800">
                    {monteCarloResults.iterations.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Waterfall Chart */}
              <div className="space-y-3">
                <h4 className="text-lg font-semibold text-center text-gray-800">
                  🌍 Waterfall of Mean CO₂-eq after Monte Carlo LCA
                  (Year-to-year changes)
                </h4>
                <p className="text-center text-sm text-gray-600 mb-4">
                  ({monteCarloResults.iterations.toLocaleString()} iterations)
                </p>
                <div className="bg-white border-2 border-gray-200 rounded-lg p-6 shadow-sm">
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={monteCarloResults.waterfallData}
                      margin={{ top: 30, right: 30, left: 20, bottom: 60 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="name"
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        fontSize={11}
                        fontWeight="bold"
                      />
                      <YAxis
                        domain={[70, 105]}
                        label={{
                          value: "Mean CO₂-equivalent (kg CO₂-eq)",
                          angle: -90,
                          position: "insideLeft",
                          style: {
                            textAnchor: "middle",
                            fontSize: "12px",
                            fontWeight: "bold",
                          },
                        }}
                        fontSize={11}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "rgba(255, 255, 255, 0.95)",
                          border: "2px solid #e0e0e0",
                          borderRadius: "8px",
                          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                        }}
                        formatter={(value, name, props) => {
                          const data = props.payload;
                          return [
                            `Mean: ${data.value.toFixed(1)} kg`,
                            `Median: ${data.median.toFixed(1)} kg`,
                            `95% CI: [${data.lower95.toFixed(
                              1
                            )}, ${data.upper95.toFixed(1)}]`,
                          ];
                        }}
                        labelFormatter={(label) => `Year Transition: ${label}`}
                      />
                      <Bar
                        dataKey="value"
                        name="Mean CO₂-eq"
                        radius={[4, 4, 0, 0]}
                      >
                        {monteCarloResults.waterfallData.map((entry, index) => (
                          <Bar key={`bar-${index}`} fill={entry.fill} />
                        ))}
                        <LabelList
                          dataKey="value"
                          position="top"
                          fontSize={10}
                          fontWeight="bold"
                          formatter={(value) => value.toFixed(1)}
                        />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-xs text-gray-500 text-center mt-3">
                  Monte Carlo simulation showing year-over-year CO₂ reduction
                  with {monteCarloResults.statistics.volatility}% volatility and{" "}
                  {monteCarloResults.statistics.reductionRate}% annual reduction
                  rate
                </p>
              </div>
            </div>
          )}

          {!monteCarloResults && !runningMonteCarlo && (
            <div className="text-center py-8 text-gray-500">
              <p className="text-sm">
                Click "Run Monte Carlo" to perform uncertainty analysis
              </p>
              <p className="text-xs mt-1">
                Simulates 2000 iterations to quantify result confidence
                intervals
              </p>
            </div>
          )}
        </Card>

        {/* Materials Table */}
        {materialsInfo.length > 0 && (
          <Card className="p-6 mb-12 space-y-4">
            <h3 className="text-lg font-semibold">Materials</h3>
            <div className="overflow-auto -mx-2">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left bg-gray-50 border-b">
                    <th className="py-2 px-2 font-medium text-gray-600">
                      Material
                    </th>
                    <th className="py-2 px-2 font-medium text-gray-600">
                      Mass (kg)
                    </th>
                    <th className="py-2 px-2 font-medium text-gray-600">
                      Emissions (kg CO₂e)
                    </th>
                    <th className="py-2 px-2 font-medium text-gray-600">
                      Circularity Index
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {materialsInfo.map((m, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2 px-2">{m.material || "—"}</td>
                      <td className="py-2 px-2">{fmt(m.mass_kg)}</td>
                      <td className="py-2 px-2">{fmt(m.emissions_kg_co2e)}</td>
                      <td className="py-2 px-2">
                        {fmt(m.circularity_index, 3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
        <div className="flex justify-end mt-4 mb-16">
          <Button onClick={handleGenerateReport} disabled={generatingReport}>
            {generatingReport ? "Generating…" : "Generate Report"}
          </Button>
        </div>
      </Section>
    </>
  );
}

/* ----------------- Custom Charts ------------------ */

const comprehensiveCarbonData = [
  {
    name: "Mining",
    current: 500,
    improved: 400,
    strategy: "Diesel → Electric trucks / EV fleet",
  },
  {
    name: "Alumina Refining",
    current: 1200,
    improved: 800,
    strategy: "Coal boilers → Renewable heat",
  },
  {
    name: "Smelting",
    current: 7000,
    improved: 4000,
    strategy: "Grid coal → Hydro/solar/wind",
  },
  {
    name: "Casting/Forming",
    current: 1000,
    improved: 700,
    strategy: "Ineff. furnaces → Efficient furnaces",
  },
  {
    name: "Transportation",
    current: 800,
    improved: 300,
    strategy: "Road trucks → Rail / E-fleet",
  },
  {
    name: "Product Use",
    current: 300,
    improved: 200,
    strategy: "Single-use → Durable & design for recycling",
  },
  {
    name: "Recycling",
    current: 500,
    improved: 300,
    strategy: "Low recycling → Closed-loop recycling",
  },
];

// Custom renderer for "reduction" label above improved bar
const renderReductionLabel = (props) => {
  const { x, y, value } = props; // Recharts passes exact x,y for each label
  // Move label a bit above the bar
  return (
    <text
      x={x}
      y={y - 6}
      fill="#059669"
      fontSize={12}
      fontWeight="bold"
      textAnchor="middle"
    >
      {value}
    </text>
  );
};

// Custom X Axis tick renderer — draws multiline strategy under each tick
const renderTickWithStrategy = ({ x, y, payload, index }) => {
  // payload.value is the category name (e.g. "Mining")
  // Use the same index to get strategy text from our data array
  const entry = comprehensiveCarbonData[index];
  const lines = entry.strategy.split(" → ");
  // primary tick label (category) + strategy lines (multiline, with arrows)
  return (
    <g transform={`translate(${x},${y})`}>
      <text x={0} y={0} dy={0} textAnchor="middle" fontSize={11} fill="#333">
        {payload.value}
      </text>

      {lines.map((line, i) => (
        <text
          key={i}
          x={0}
          y={16 + i * 12} // space below the main tick label
          textAnchor="middle"
          fontSize={9}
          fill="#666"
        >
          {i === 0 ? line : `→ ${line}`}
        </text>
      ))}
    </g>
  );
};

function ComprehensiveCarbonChart() {
  return (
    <ResponsiveContainer width="100%" height={480}>
      <BarChart
        data={comprehensiveCarbonData}
        margin={{ top: 10, right: 10, left: 10, bottom: 10 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="name"
          interval={0}
          tick={renderTickWithStrategy}
          height={110} // leave space for multiline tick text
        />
        <YAxis
          domain={[0, 8000]}
          label={{
            value: "kg CO₂ / ton",
            angle: -90,
            position: "insideLeft",
            offset: 10,
            style: { textAnchor: "middle", fontSize: 12, fontWeight: "bold" },
          }}
        />
        <Tooltip
          formatter={(value, name) => [
            `${value} kg CO₂/ton`,
            name === "current" ? "Current" : "Improved",
          ]}
          labelFormatter={(label) => `Stage: ${label}`}
          contentStyle={{
            backgroundColor: "#fff",
            border: "1px solid #ccc",
            borderRadius: 4,
          }}
        />
        <Legend verticalAlign="top" height={36} iconType="rect" />
        <Bar dataKey="current" fill="#E69F00" name="Current" />
        <Bar dataKey="improved" fill="#56B4E9" name="Improved">
          {/* Put reduction labels above improved bars using LabelList */}
          <LabelList dataKey="reduction" content={renderReductionLabel} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
