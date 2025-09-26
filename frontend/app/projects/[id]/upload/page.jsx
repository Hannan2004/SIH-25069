"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import UploadDropzone from "@/components/UploadDropzone";
import EditableSheet from "@/components/EditableSheet";

export default function UploadPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id;
  const [project, setProject] = useState(null);
  // in-memory datasets: { [id]: { label, sheets?, activeSheet, fileMeta } }
  // localStorage will only persist: projects[projectId].datasetIndex = { [id]: { label, fileMeta, activeSheet } }
  const [datasets, setDatasets] = useState({});
  const [activeDataset, setActiveDataset] = useState("");
  const [activeSheet, setActiveSheet] = useState("");
  const [datasetType, setDatasetType] = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  useEffect(() => {
    const projects = JSON.parse(localStorage.getItem("dc_projects") || "{}");
    if (projects[projectId]) {
      setProject(projects[projectId]);
      const pj = projects[projectId];
      // New model: datasetIndex (metadata only)
      if (pj.datasetIndex) {
        setDatasets(pj.datasetIndex); // note: sheets not stored; will load on demand
        const first = Object.keys(pj.datasetIndex)[0];
        if (first) {
          setActiveDataset(first);
          setActiveSheet(pj.datasetIndex[first].activeSheet || "");
        }
      } else if (pj.sheetJSON) {
        // Migration path from older formats
        if (pj.sheetJSON.datasets) {
          const migrated = {};
          Object.entries(pj.sheetJSON.datasets).forEach(([k, v]) => {
            migrated[k] = {
              label: v.label,
              activeSheet: v.activeSheet,
              fileMeta: v.fileMeta || null,
              // omit sheets for storage
            };
          });
          pj.datasetIndex = migrated;
          delete pj.sheetJSON; // remove large payload
          const projectsAll = JSON.parse(
            localStorage.getItem("dc_projects") || "{}"
          );
          projectsAll[projectId] = pj;
          localStorage.setItem("dc_projects", JSON.stringify(projectsAll));
          setDatasets(migrated);
          const first = Object.keys(migrated)[0];
          if (first) {
            setActiveDataset(first);
            setActiveSheet(migrated[first].activeSheet || "");
          }
        } else if (pj.sheetJSON.sheets) {
          // legacy single dataset
          const migrated = {
            default: {
              label: "Primary Inventory",
              activeSheet: pj.sheetJSON.active,
              fileMeta: null,
            },
          };
          pj.datasetIndex = migrated;
          delete pj.sheetJSON;
          const projectsAll = JSON.parse(
            localStorage.getItem("dc_projects") || "{}"
          );
          projectsAll[projectId] = pj;
          localStorage.setItem("dc_projects", JSON.stringify(projectsAll));
          setDatasets(migrated);
          setActiveDataset("default");
          setActiveSheet(migrated.default.activeSheet || "");
        }
      }
    }
  }, [projectId]);

  const handleUpload = useCallback(
    (data) => {
      if (!datasetType) return;
      const base = datasetType.toLowerCase().replace(/[^a-z0-9]+/g, "-");
      const key = Object.keys(datasets).includes(base)
        ? `${base}-${Date.now().toString().slice(-4)}`
        : base;
      const next = {
        ...datasets,
        [key]: {
          label: datasetType,
          activeSheet: data.active,
          fileMeta: data.fileMeta || null,
          sheets: data.sheets, // keep in memory only
        },
      };
      setDatasets(next);
      setActiveDataset(key);
      setActiveSheet(data.active);
      setDatasetType("");
      setStatusMsg(`Added dataset: ${datasetType}`);
      setTimeout(() => setStatusMsg(""), 2500);
    },
    [datasetType, datasets]
  );

  const handleSave = () => {
    if (!Object.keys(datasets).length) return;
    const metaOnly = {};
    Object.entries(datasets).forEach(([k, v]) => {
      metaOnly[k] = {
        label: v.label,
        activeSheet: v.activeSheet,
        fileMeta: v.fileMeta || null,
      };
    });
    const projects = JSON.parse(localStorage.getItem("dc_projects") || "{}");
    if (!projects[projectId]) return;
    projects[projectId].datasetIndex = metaOnly;
    delete projects[projectId].sheetJSON; // ensure old large structure removed
    localStorage.setItem("dc_projects", JSON.stringify(projects));
    setStatusMsg("Dataset metadata saved.");
    setTimeout(() => setStatusMsg(""), 3000);
  };

  const fillEmpty = () => {
    if (!activeDataset) return;
    const ds = datasets[activeDataset];
    if (!ds.sheets) return; // nothing loaded in memory
    const newSheets = {};
    Object.entries(ds.sheets).forEach(([name, rows]) => {
      newSheets[name] = rows.map((r) =>
        r.map((c) => (c === "" || c == null ? "0" : c))
      );
    });
    const updated = {
      ...datasets,
      [activeDataset]: { ...ds, sheets: newSheets },
    };
    setDatasets(updated);
  };

  const proceed = () => {
    handleSave();
    router.push(`/projects/${projectId}/missing-values`);
  };

  return (
    <>
      <PageHero
        title="Upload Inventory Data"
        description="Add one or more structured datasets (e.g., Primary Process, Energy Mix, Scrap Flows). Each dataset may include multiple sheets."
      />
      <Section>
        <div className="space-y-8">
          <Card className="p-6 space-y-6">
            <div className="grid md:grid-cols-3 gap-4 items-end">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dataset Type
                </label>
                <select
                  value={datasetType}
                  onChange={(e) => setDatasetType(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-brand-emerald"
                >
                  <option value="">Select type…</option>
                  <option>Primary Inventory</option>
                  <option>Energy Mix</option>
                  <option>Scrap & Recycling</option>
                  <option>Transport & Logistics</option>
                  <option>Supplemental Parameters</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Choose a dataset category before uploading a file.
                </p>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload File
                </label>
                <UploadDropzone onDataParsed={handleUpload} />
              </div>
            </div>
            {Object.keys(datasets).length === 0 && (
              <p className="text-sm text-gray-500">No datasets added yet.</p>
            )}
            {Object.keys(datasets).length > 0 && (
              <div className="space-y-6">
                <div className="flex flex-wrap gap-3 items-center">
                  {Object.entries(datasets).map(([key, ds]) => {
                    const hasUrl = ds.fileMeta?.url;
                    return (
                      <button
                        key={key}
                        title={
                          hasUrl ? `Source: ${ds.fileMeta.url}` : undefined
                        }
                        onClick={() => {
                          setActiveDataset(key);
                          setActiveSheet(ds.activeSheet);
                        }}
                        className={`px-4 py-2 rounded-full text-xs font-medium border relative transition group ${
                          activeDataset === key
                            ? "bg-brand-emerald text-white border-brand-emerald"
                            : "bg-white hover:bg-gray-50"
                        }`}
                      >
                        {ds.label}
                        {hasUrl && (
                          <span className="ml-1 text-[10px] underline decoration-dotted group-hover:text-brand-sky">
                            link
                          </span>
                        )}
                      </button>
                    );
                  })}
                  <div className="ml-auto flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={fillEmpty}
                      disabled={!activeDataset}
                    >
                      Fill empty with 0
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleSave}>
                      Save All
                    </Button>
                    <Button
                      size="sm"
                      onClick={proceed}
                      disabled={!Object.keys(datasets).length}
                    >
                      Proceed →
                    </Button>
                  </div>
                </div>
                {activeDataset && (
                  <div className="border rounded-lg p-4">
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      {datasets[activeDataset].sheets &&
                        Object.keys(datasets[activeDataset].sheets).map(
                          (sheet) => (
                            <button
                              key={sheet}
                              onClick={() => setActiveSheet(sheet)}
                              className={`px-3 py-1.5 rounded-md text-xs font-medium border ${
                                activeSheet === sheet
                                  ? "bg-brand-emerald text-white border-brand-emerald"
                                  : "bg-white hover:bg-gray-50"
                              }`}
                            >
                              {sheet}
                            </button>
                          )
                        )}
                    </div>
                    {datasets[activeDataset].sheets ? (
                      <EditableSheet
                        sheetName={activeSheet}
                        data={datasets[activeDataset].sheets[activeSheet]}
                        onChange={(rows) => {
                          const updated = {
                            ...datasets,
                            [activeDataset]: {
                              ...datasets[activeDataset],
                              sheets: {
                                ...datasets[activeDataset].sheets,
                                [activeSheet]: rows,
                              },
                              activeSheet: activeSheet,
                            },
                          };
                          setDatasets(updated);
                        }}
                      />
                    ) : (
                      <p className="text-xs text-gray-500">
                        Sheets not loaded. Re-upload file to edit locally.
                      </p>
                    )}
                    {datasets[activeDataset].fileMeta?.url && (
                      <p className="mt-3 text-[11px] text-gray-500 break-all">
                        Source URL:{" "}
                        <a
                          className="text-brand-emerald hover:underline"
                          href={datasets[activeDataset].fileMeta.url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {datasets[activeDataset].fileMeta.url}
                        </a>
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
            {statusMsg && (
              <p className="text-xs text-brand-emerald">{statusMsg}</p>
            )}
          </Card>
          <Card className="p-4 bg-brand-sky/40 border-brand-sky text-xs text-brand-forest">
            Tip: Add multiple datasets to represent different parts of your
            system (e.g., energy vs process vs logistics). They will be merged
            logically in later analysis steps.
          </Card>
        </div>
      </Section>
    </>
  );
}
