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
          <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
            <li>Switch to renewable energy sources during smelting</li>
            <li>Optimize transport routes to reduce fuel consumption</li>
            <li>Increase recycling of input materials</li>
            <li>Adopt energy-efficient refining technologies</li>
            <li>Implement waste heat recovery systems</li>
          </ul>

          {/* Before vs After Combined Chart */}
          <div className="mt-6">
            <h4 className="text-lg font-semibold mb-4">Before vs After Emissions</h4>
            <div className="bg-white border rounded p-4 flex justify-center items-center" style={{ minHeight: '300px' }}>
              <div className="w-full">
                <BeforeAfterCombinedChart />
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2 text-center">
              Emission reductions across key stages after applying recommendations.
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

const combinedData = [
  { name: "Production", before: 400, after: 250 },
  { name: "Transport", before: 300, after: 180 },
  { name: "Energy", before: 500, after: 300 },
  { name: "End-of-Life", before: 200, after: 120 },
];

function BeforeAfterCombinedChart() {
  return (
    <ResponsiveContainer width="100%" height={280}>
      {/* 1. Adjusted top margin from 60 to 40 for better spacing */}
      <BarChart data={combinedData} margin={{ top: 40, right: 10, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="name" 
          fontSize={12} 
          interval={0}
          angle={0}
          textAnchor="middle"
          height={40}
          axisLine={false}
          tickLine={false}
        />
        <YAxis 
          domain={[0, 600]} 
          fontSize={10}
          /* 2. Changed YAxis label position from 'insideLeft' to 'outside' 
                to bring it down and fully display it. */
          label={{ 
            value: 'Emissions (kg CO₂e)', 
            angle: -90, 
            position: 'outside', 
            dx: -10, // Optional: minor adjustment to pull it closer to the Y-axis
            dy: 5 
          }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip 
          formatter={(value, name) => [
            `${value} kg CO₂e`, 
            name === 'before' ? 'Before' : 'After'
          ]}
        />
        <Bar dataKey="before" fill="#EF4444" name="before" />
        <Bar dataKey="after" fill="#10B981" name="after" />
        
        {/* Add percentage labels */}
        {combinedData.map((entry, index) => {
          const reduction = ((entry.before - entry.after) / entry.before * 100).toFixed(0);
          

          // Approximate X-position for centering over the XAxis label:
          // Using justify-between logic: spread percentages evenly across chart width
          const CHART_LEFT_MARGIN = 150; // Shifted right from 60 to 100
          const CHART_RIGHT_MARGIN = 40; // End margin
          const CHART_USABLE_WIDTH = 550; // Reduced width to accommodate left shift
          const totalItems = combinedData.length;
          
          // Calculate position using justify-between logic
          // For 4 items: positions at 0%, 33.33%, 66.66%, 100% of usable width
          const xPosition = CHART_LEFT_MARGIN + (index / (totalItems - 1)) * CHART_USABLE_WIDTH;

          return (
            <text
              key={index}
              x={xPosition}
              y={25}
              textAnchor="middle"
              fontSize="12"
              fill="#059669"
              fontWeight="bold"
            >
              ↓{reduction}%
            </text>
          );
        })}
      </BarChart>
    </ResponsiveContainer>
  );
}