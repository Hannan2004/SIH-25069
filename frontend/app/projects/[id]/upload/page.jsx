"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import UploadDropzone from "@/components/UploadDropzone";
import EditableSheet from "@/components/EditableSheet";
import {
  getProject,
  addDataset,
  listDatasets,
  updateProject,
  addAnalysis,
} from "@/lib/projects";
import {
  extractAnalysisPayload,
  validatePayload,
} from "@/lib/extractAnalysisPayload";
import { useUser } from "@/context/UserContext";

export default function UploadPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id;
  const { user } = useUser();
  const [project, setProject] = useState(null);
  // in-memory only: { tempId: { label, sheets, activeSheet, fileMeta } } OR persisted (id from Firestore with gcsUrl)
  const [localDatasets, setLocalDatasets] = useState({});
  const [remoteDatasets, setRemoteDatasets] = useState([]); // list from Firestore
  const [activeDataset, setActiveDataset] = useState(null); // key: tempId or remote id
  const [activeSheet, setActiveSheet] = useState("");
  const [datasetType, setDatasetType] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [processingAnalysis, setProcessingAnalysis] = useState(false);
  const [currentAgent, setCurrentAgent] = useState("");
  const [agentStep, setAgentStep] = useState(0);
  // analysis states removed in new flow (persist + redirect)
  const [analysisPayload, setAnalysisPayload] = useState(null);
  // analysisPayload omitted (not needed for UI currently)

  useEffect(() => {
    (async () => {
      const pj = await getProject(projectId);
      if (pj) setProject(pj);
      const rds = await listDatasets(projectId);
      setRemoteDatasets(rds);
    })();
  }, [projectId]);

  const handleUpload = useCallback(
    (data) => {
      if (!datasetType) return;
      const tempId = `temp-${Date.now()}`;
      setLocalDatasets((prev) => ({
        ...prev,
        [tempId]: {
          label: datasetType,
          activeSheet: data.active,
          fileMeta: data.fileMeta,
          sheets: data.sheets,
        },
      }));
      setActiveDataset(tempId);
      setActiveSheet(data.active);
      setDatasetType("");
      setStatusMsg(`Added dataset (not yet saved): ${datasetType}`);
      setTimeout(() => setStatusMsg(""), 2500);
    },
    [datasetType]
  );

  const saveActiveDataset = async () => {
    if (!activeDataset || !localDatasets[activeDataset]) return;
    setSaving(true);
    try {
      const ds = localDatasets[activeDataset];
      // Choose the active sheet (or fallback first sheet) for key/value extraction
      const sheetName = ds.activeSheet || Object.keys(ds.sheets)[0];
      const rows = ds.sheets[sheetName];
      const payload = extractAnalysisPayload(rows);
      // Log payload for developer visibility
      console.log("[Dataset Payload]", payload);

      // Validate payload
      const validation = validatePayload(payload);

      // Sanitize sheets snapshot to remove nested arrays (Firestore disallows arrays of arrays)
      // We convert each sheet's 2D array into an array of row objects keyed by header names when present.
      const sanitizeRows = (rMatrix) => {
        if (!Array.isArray(rMatrix)) return [];
        if (!rMatrix.length) return [];
        // If already array of objects just return (assume safe)
        if (typeof rMatrix[0] === "object" && !Array.isArray(rMatrix[0]))
          return rMatrix;
        // Expect array-of-arrays
        const headerCandidate = rMatrix[0];
        const nonEmptyHeaderCount = Array.isArray(headerCandidate)
          ? headerCandidate.filter(
              (c) => c !== null && c !== undefined && c !== ""
            ).length
          : 0;
        const looksLikeHeader = nonEmptyHeaderCount >= 2; // simple heuristic
        let headers = [];
        let dataRows = rMatrix;
        if (looksLikeHeader) {
          headers = headerCandidate.map((h, i) =>
            h === null || h === undefined || h === "" ? `col_${i}` : String(h)
          );
          dataRows = rMatrix.slice(1);
        } else {
          // fabricate headers col_0..col_n
          const maxLen = Math.max(
            ...rMatrix.map((r) => (Array.isArray(r) ? r.length : 0))
          );
          headers = Array.from({ length: maxLen }, (_, i) => `col_${i}`);
        }
        return dataRows
          .filter(
            (row) =>
              Array.isArray(row) &&
              row.some((c) => c !== null && c !== undefined && c !== "")
          )
          .map((row) => {
            const obj = {};
            headers.forEach((h, idx) => {
              obj[h] = row[idx] === undefined ? "" : row[idx];
            });
            return obj;
          });
      };

      const sanitizedSheets = Object.fromEntries(
        Object.entries(ds.sheets).map(([name, rMatrix]) => [
          name,
          sanitizeRows(rMatrix),
        ])
      );

      const datasetId = await addDataset(projectId, {
        name: ds.label,
        type: ds.label,
        activeSheet: sheetName,
        payload, // store the structured analysis payload directly
        // Store sanitized snapshot (array of objects) to remain Firestore-compliant
        sheetsSnapshot: sanitizedSheets,
        validation,
      });

      // Remove temp + refresh list
      setLocalDatasets((prev) => {
        const cp = { ...prev };
        delete cp[activeDataset];
        return cp;
      });
      const rds = await listDatasets(projectId);
      setRemoteDatasets(rds);
      setActiveDataset(datasetId);
      setStatusMsg(
        validation.valid
          ? "Dataset payload saved."
          : `Dataset saved with warnings: ${validation.issues.join("; ")}`
      );
      setTimeout(() => setStatusMsg(""), 2500);
      await updateProject(projectId, { hasDatasets: true });
    } catch (e) {
      console.error(e);
      setStatusMsg(e.message || "Save failed");
      setTimeout(() => setStatusMsg(""), 3000);
    } finally {
      setSaving(false);
    }
  };

  const fillEmpty = () => {
    if (!activeDataset) return;
    // Only applies to unsaved local dataset currently in memory
    if (!localDatasets[activeDataset]) return;
    const ds = localDatasets[activeDataset];
    const newSheets = {};
    Object.entries(ds.sheets).forEach(([name, rows]) => {
      newSheets[name] = rows.map((r) =>
        r.map((c) => (c === "" || c == null ? "0" : c))
      );
    });
    setLocalDatasets((prev) => ({
      ...prev,
      [activeDataset]: { ...ds, sheets: newSheets },
    }));
  };

  const runAnalysis = async () => {
    if (!activeDataset) return;
    let payload = null;
    if (localDatasets[activeDataset]) {
      const ds = localDatasets[activeDataset];
      const sheet = ds.activeSheet || Object.keys(ds.sheets)[0];
      payload = extractAnalysisPayload(ds.sheets[sheet]);
    } else {
      const ds = remoteDatasets.find((d) => d.id === activeDataset);
      if (!ds) return;
      if (ds.payload) {
        payload = ds.payload; // already stored
      } else if (ds.sheetsSnapshot) {
        const sheet = ds.activeSheet || Object.keys(ds.sheetsSnapshot)[0];
        const sheetData = ds.sheetsSnapshot[sheet];
        // If sheetData is array of objects we can send directly to extractor.
        if (
          Array.isArray(sheetData) &&
          sheetData.length > 0 &&
          typeof sheetData[0] === "object" &&
          !Array.isArray(sheetData[0])
        ) {
          payload = extractAnalysisPayload(sheetData);
        } else {
          // Fallback (should not happen after sanitization)
          payload = extractAnalysisPayload(sheetData);
        }
      } else {
        setStatusMsg("No payload available for this dataset");
        setTimeout(() => setStatusMsg(""), 2500);
        return;
      }
    }
    if (!payload) return;

    // Start three-phase processing
    setProcessingAnalysis(true);
    setAgentStep(0);

    try {
      // Phase 1: Data Ingestion Agent (5 seconds)
      setCurrentAgent("Data Ingestion Agent");
      setAgentStep(1);
      await new Promise((resolve) => setTimeout(resolve, 5000));

      // Phase 2: LCA Analysis Agent (5 seconds)
      setCurrentAgent("LCA Analysis Agent");
      setAgentStep(2);
      await new Promise((resolve) => setTimeout(resolve, 5000));

      // Phase 3: Compliance Agent (5 seconds)
      setCurrentAgent("Compliance Agent");
      setAgentStep(3);
      await new Promise((resolve) => setTimeout(resolve, 5000));

      // Now perform actual analysis
      setAnalyzing(true);
      setAnalysisPayload(payload);
      const backendBase =
        process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const started = performance.now();
      // Attach project-level configuration overrides if present
      const enrichedPayload = {
        ...payload,
        study_type:
          project?.studyType ||
          payload.study_type ||
          "internal_decision_support",
        analysis_type:
          project?.analysisType || payload.analysis_type || "cradle_to_gate",
        report_type: project?.reportType || payload.report_type || "technical",
      };
      const res = await fetch(`${backendBase}/analyze/comprehensive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(enrichedPayload),
      });
      if (!res.ok) {
        setStatusMsg("Analysis failed");
        setTimeout(() => setStatusMsg(""), 2500);
        return;
      }
      const result = await res.json();
      const durationMs = Math.round(performance.now() - started);
      // Persist analysis document then redirect
      const analysisId = await addAnalysis(projectId, {
        datasetId: activeDataset,
        payload: enrichedPayload,
        result,
        status: "complete",
        durationMs,
        studyType: enrichedPayload.study_type,
        analysisType: enrichedPayload.analysis_type,
        reportType: enrichedPayload.report_type,
      });
      setStatusMsg("Analysis complete – redirecting…");
      setTimeout(() => setStatusMsg(""), 2000);
      router.push(`/projects/${projectId}/analysis?analysis=${analysisId}`);
    } catch (e) {
      console.error(e);
      setStatusMsg("Analysis error");
      setTimeout(() => setStatusMsg(""), 2500);
    } finally {
      setAnalyzing(false);
      setProcessingAnalysis(false);
      setCurrentAgent("");
      setAgentStep(0);
    }
  };

  return (
    <>
      <PageHero
        title="Upload Inventory Data"
        description="Add one or more structured datasets (e.g., Primary Process, Energy Mix, Scrap Flows). Each dataset may include multiple sheets."
        spacing="standard"
      />
      <Section>
        <div className="space-y-8">
          <Card className="p-6 space-y-6 bg-white/70 backdrop-blur-sm border border-brand-copper/25">
            <div className="grid md:grid-cols-3 gap-4 items-end">
              <div>
                <label className="block text-sm font-medium text-brand-steel mb-2">
                  Dataset Type
                </label>
                <select
                  value={datasetType}
                  onChange={(e) => setDatasetType(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm border border-brand-aluminum/60 bg-white/60 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-brand-copper/60 focus:border-brand-copper/60 placeholder:text-brand-steel/50"
                >
                  <option value="">Select type…</option>
                  <option>Primary Inventory</option>
                  <option>Energy Mix</option>
                  <option>Scrap & Recycling</option>
                  <option>Transport & Logistics</option>
                  <option>Supplemental Parameters</option>
                </select>
                <p className="text-xs text-brand-steel/60 mt-1">
                  Choose a dataset category before uploading a file.
                </p>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-brand-steel mb-2">
                  Upload File
                </label>
                <UploadDropzone onDataParsed={handleUpload} />
              </div>
            </div>
            {Object.keys(localDatasets).length === 0 &&
            remoteDatasets.length === 0 ? (
              <p className="text-sm text-brand-steel/70">
                No datasets added yet.
              </p>
            ) : (
              <div className="space-y-6">
                <div className="flex flex-wrap gap-3 items-center">
                  {remoteDatasets.map((ds) => (
                    <button
                      key={ds.id}
                      title={
                        ds.payload
                          ? "Stored as payload"
                          : ds.gcsUrl
                          ? `Source: ${ds.gcsUrl}`
                          : undefined
                      }
                      onClick={() => {
                        setActiveDataset(ds.id);
                        setActiveSheet(ds.activeSheet || "");
                      }}
                      className={`px-4 py-2 rounded-full text-xs font-medium border relative transition group shadow-sm ${
                        activeDataset === ds.id
                          ? "bg-brand-copper text-white border-brand-copper"
                          : "bg-white/70 hover:bg-white border-brand-aluminum/60 text-brand-charcoal"
                      }`}
                    >
                      {ds.name || ds.type}
                      {ds.payload && (
                        <span className="ml-1 text-[10px] text-brand-gold">
                          ●
                        </span>
                      )}
                    </button>
                  ))}
                  {Object.entries(localDatasets).map(([key, ds]) => (
                    <button
                      key={key}
                      title="Unsaved dataset"
                      onClick={() => {
                        setActiveDataset(key);
                        setActiveSheet(ds.activeSheet);
                      }}
                      className={`px-4 py-2 rounded-full text-xs font-medium border relative transition group shadow-sm ${
                        activeDataset === key
                          ? "bg-brand-copper text-white border-brand-copper"
                          : "bg-white/70 hover:bg-white border-brand-aluminum/60 text-brand-charcoal"
                      }`}
                    >
                      {ds.label}*
                    </button>
                  ))}
                  <div className="ml-auto flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={fillEmpty}
                      disabled={!activeDataset || !localDatasets[activeDataset]}
                    >
                      Fill empty with 0
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={saveActiveDataset}
                      disabled={!localDatasets[activeDataset] || saving}
                    >
                      {saving ? "Saving…" : "Save Dataset"}
                    </Button>
                    <Button
                      size="sm"
                      onClick={runAnalysis}
                      disabled={
                        !activeDataset || analyzing || processingAnalysis
                      }
                    >
                      {processingAnalysis
                        ? "Processing..."
                        : analyzing
                        ? "Analyzing…"
                        : "Analyze"}
                    </Button>
                  </div>
                </div>
                {activeDataset && localDatasets[activeDataset] && (
                  <div className="border border-brand-aluminum/60 rounded-lg p-4 bg-white/60 backdrop-blur-sm">
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      {Object.keys(localDatasets[activeDataset].sheets).map(
                        (sheet) => (
                          <button
                            key={sheet}
                            onClick={() => setActiveSheet(sheet)}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium border shadow-sm transition ${
                              activeSheet === sheet
                                ? "bg-brand-copper text-white border-brand-copper"
                                : "bg-white/80 hover:bg-white border-brand-aluminum/60 text-brand-charcoal"
                            }`}
                          >
                            {sheet}
                          </button>
                        )
                      )}
                    </div>
                    <EditableSheet
                      sheetName={activeSheet}
                      data={localDatasets[activeDataset].sheets[activeSheet]}
                      onChange={(rows) => {
                        setLocalDatasets((prev) => ({
                          ...prev,
                          [activeDataset]: {
                            ...prev[activeDataset],
                            sheets: {
                              ...prev[activeDataset].sheets,
                              [activeSheet]: rows,
                            },
                            activeSheet,
                          },
                        }));
                      }}
                    />
                  </div>
                )}
                {activeDataset &&
                  remoteDatasets.find((d) => d.id === activeDataset) && (
                    <div className="border border-brand-aluminum/60 rounded-lg p-4 text-xs text-brand-steel/70 space-y-2 bg-white/60 backdrop-blur-sm">
                      <p className="font-medium text-brand-charcoal/80">
                        Stored Dataset
                      </p>
                      <pre className="bg-brand-soft/80 p-2 rounded max-h-48 overflow-auto text-[11px]">
                        {JSON.stringify(
                          remoteDatasets.find((d) => d.id === activeDataset)
                            ?.payload || {},
                          null,
                          2
                        )}
                      </pre>
                      <p className="text-[10px] text-brand-steel/50">
                        (Original sheets snapshot preserved in Firestore)
                      </p>
                    </div>
                  )}
                {statusMsg && (
                  <p className="text-xs text-brand-copper font-medium animate-pulse">
                    {statusMsg}
                  </p>
                )}
              </div>
            )}
          </Card>
          {(processingAnalysis || analyzing) && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/70 backdrop-blur-sm">
              <div className="bg-white/80 border border-brand-copper/30 rounded-lg p-8 shadow-xl flex flex-col items-center gap-6 w-[380px]">
                <div className="animate-spin h-10 w-10 rounded-full border-4 border-brand-copper border-t-transparent" />

                {processingAnalysis && (
                  <>
                    <div className="text-center space-y-3">
                      <h3 className="text-lg font-semibold text-brand-charcoal">
                        {currentAgent}
                      </h3>
                      <p className="text-sm text-brand-steel/70">
                        Processing your data through our AI agents...
                      </p>
                    </div>

                    {/* Progress indicators */}
                    <div className="flex items-center gap-4 w-full">
                      <div
                        className={`flex flex-col items-center gap-2 flex-1 transition-all duration-500 ${
                          agentStep >= 1
                            ? "text-brand-copper"
                            : "text-brand-steel/50"
                        }`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-500 ${
                            agentStep >= 1
                              ? "border-brand-copper bg-brand-copper text-white shadow"
                              : "border-brand-aluminum/70 text-brand-steel/60 bg-white"
                          }`}
                        >
                          1
                        </div>
                        <span className="text-xs text-center leading-tight">
                          Data
                          <br />
                          Ingestion
                        </span>
                      </div>

                      <div
                        className={`h-0.5 flex-1 transition-all duration-500 ${
                          agentStep >= 2
                            ? "bg-gradient-to-r from-brand-copper via-brand-gold to-brand-steel"
                            : "bg-brand-aluminum/60"
                        }`}
                      />

                      <div
                        className={`flex flex-col items-center gap-2 flex-1 transition-all duration-500 ${
                          agentStep >= 2
                            ? "text-brand-copper"
                            : "text-brand-steel/50"
                        }`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-500 ${
                            agentStep >= 2
                              ? "border-brand-copper bg-brand-copper text-white shadow"
                              : "border-brand-aluminum/70 text-brand-steel/60 bg-white"
                          }`}
                        >
                          2
                        </div>
                        <span className="text-xs text-center leading-tight">
                          LCA
                          <br />
                          Analysis
                        </span>
                      </div>

                      <div
                        className={`h-0.5 flex-1 transition-all duration-500 ${
                          agentStep >= 3
                            ? "bg-gradient-to-r from-brand-copper via-brand-gold to-brand-steel"
                            : "bg-brand-aluminum/60"
                        }`}
                      />

                      <div
                        className={`flex flex-col items-center gap-2 flex-1 transition-all duration-500 ${
                          agentStep >= 3
                            ? "text-brand-copper"
                            : "text-brand-steel/50"
                        }`}
                      >
                        <div
                          className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-500 ${
                            agentStep >= 3
                              ? "border-brand-copper bg-brand-copper text-white shadow"
                              : "border-brand-aluminum/70 text-brand-steel/60 bg-white"
                          }`}
                        >
                          3
                        </div>
                        <span className="text-xs text-center leading-tight">
                          Compliance
                          <br />
                          Check
                        </span>
                      </div>
                    </div>
                  </>
                )}

                {analyzing && !processingAnalysis && (
                  <p className="text-sm text-brand-steel/70 text-center">
                    Running analysis…
                  </p>
                )}
              </div>
            </div>
          )}
          <Card className="p-4 bg-white/60 backdrop-blur-sm border border-brand-copper/25 text-xs text-brand-steel/80">
            Tip: Add multiple datasets to represent different parts of your
            system (e.g., energy vs process vs logistics). They will be merged
            logically in later analysis steps.
          </Card>
          {remoteDatasets.length > 0 && (
            <div className="flex justify-end">
              <Button
                onClick={() => {
                  // choose first saved dataset for now
                  const first = remoteDatasets[0];
                  router.push(
                    `/projects/${projectId}/analysis?dataset=${first.id}`
                  );
                }}
              >
                Start Analysis →
              </Button>
            </div>
          )}
        </div>
      </Section>
    </>
  );
}
