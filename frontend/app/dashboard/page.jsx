"use client";

import { useEffect, useState } from "react";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import Link from "next/link";
import {
  listProjects,
  listDatasets,
  listAnalyses,
  updateProject,
} from "@/lib/projects";
import { useUser } from "@/context/UserContext";

// Derive a simple progress state for each project based on stored keys
function computeProgress(project) {
  const steps = [
    { key: "created", label: "Created" },
    { key: "upload", label: "Upload" },
    { key: "mapping", label: "Gap Mapping" },
    { key: "analysis", label: "Analysis" },
    { key: "results", label: "Results" },
  ];

  const status = {};
  status.created = true;
  status.upload = !!project.sheetJSON;
  status.mapping = !!project.mappedJSON;
  // (Future) could set analysis key when analysis is computed; for now assume after mapping
  status.analysis = !!project.mappedJSON;
  status.results = !!project.mappedJSON; // results page derives from mapped data currently

  const completedCount = steps.filter((s) => status[s.key]).length;
  return { steps, status, completedCount };
}

export default function DashboardPage() {
  const { user } = useUser();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        if (!user?.uid) {
          setLoading(false);
          return;
        }
        const pj = await listProjects(user.uid);
        if (cancelled) return;
        // For each project gather dataset & analysis counts (lightweight sequential for now)
        const enriched = [];
        for (const p of pj) {
          try {
            const datasets = await listDatasets(p.id);
            const analyses = await listAnalyses(p.id);
            const hasReport = analyses.some(
              (a) => a.result?.results?.report_summary?.report_files?.length
            );
            enriched.push({
              ...p,
              datasetCount: datasets.length,
              analysisCount: analyses.length,
              latestAnalysisId: analyses.length
                ? analyses[analyses.length - 1].id
                : null,
              hasReport,
            });
            // Opportunistically persist hasDatasets/hasReport flags if not set
            const needUpdate =
              (!p.hasDatasets && datasets.length) ||
              (!p.hasReport && hasReport);
            if (needUpdate) {
              updateProject(p.id, {
                hasDatasets: !!datasets.length,
                hasReport,
                latestAnalysisId: analyses.length
                  ? analyses[analyses.length - 1].id
                  : null,
              }).catch(() => {});
            }
          } catch (inner) {
            console.warn("Project enrichment failed", p.id, inner);
            enriched.push({
              ...p,
              datasetCount: 0,
              analysisCount: 0,
              hasReport: false,
            });
          }
        }
        setProjects(enriched);
      } catch (e) {
        setError(e.message || "Failed to load projects");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user?.uid]);

  const projectEntries = projects;

  return (
    <>
      <PageHero
        title="Dashboard"
        description={
          user
            ? `Welcome back, ${
                user.name.split(" ")[0]
              }. Manage your LCA projects.`
            : "Manage your LCA projects."
        }
        spacing="standard"
      />
      <Section>
        <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
          <h2 className="text-lg font-semibold text-brand-charcoal">
            Your Projects
          </h2>
          <Link href="/projects/new">
            <Button size="sm">+ Add Project</Button>
          </Link>
        </div>
        {loading && (
          <Card className="p-8 text-center text-sm text-brand-steel/70 bg-white/70 backdrop-blur-sm border border-brand-copper/20">
            Loading projects…
          </Card>
        )}
        {!loading && projectEntries.length === 0 && (
          <Card className="p-8 text-center space-y-4 bg-white/70 backdrop-blur-sm border border-brand-copper/25">
            <p className="text-brand-steel/80 text-sm">
              You have no projects yet.
            </p>
            <Link href="/projects/new">
              <Button>Create your first project</Button>
            </Link>
          </Card>
        )}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projectEntries.map((project) => {
            const id = project.id;
            // Determine destination: results if report, analysis if analyses exist, upload otherwise
            const destination =
              project.hasReport && project.latestAnalysisId
                ? `/projects/${id}/results?analysis=${project.latestAnalysisId}`
                : project.analysisCount > 0 && project.latestAnalysisId
                ? `/projects/${id}/analysis?analysis=${project.latestAnalysisId}`
                : project.datasetCount > 0
                ? `/projects/${id}/analysis?dataset=${
                    project.firstDatasetId || ""
                  }`
                : `/projects/${id}/upload`;

            const { steps, status, completedCount } = computeProgress({
              sheetJSON: project.datasetCount
                ? { sheets: Array(project.datasetCount).fill(0) }
                : null,
              mappedJSON: project.analysisCount ? {} : null,
            });
            const pct = Math.round((completedCount / steps.length) * 100);
            const datasetCount = project.datasetCount || 0;
            return (
              <Card
                key={id}
                className="p-5 flex flex-col cursor-pointer hover:shadow-lg hover:border-brand-copper/40 transition border border-brand-copper/20 bg-white/70 backdrop-blur-sm"
                onClick={() => (window.location.href = destination)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-brand-charcoal">
                      {project.name || project.title || "Untitled Project"}
                    </h3>
                    <p className="text-xs text-brand-steel/60 mt-0.5">
                      ID: {id}
                    </p>
                  </div>
                  <span className="text-xs font-medium text-brand-copper">
                    Open →
                  </span>
                </div>
                <div className="mb-4">
                  <div className="h-2 bg-brand-aluminum/40 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-brand-copper via-brand-gold to-brand-steel transition-all"
                      style={{ width: pct + "%" }}
                    />
                  </div>
                  <p className="mt-1 text-[11px] text-brand-steel/70 tracking-wide">
                    Progress: {pct}%
                  </p>
                </div>
                <ul className="space-y-1 mb-4 text-xs">
                  {steps.map((s) => (
                    <li key={s.key} className="flex items-center gap-2">
                      <span
                        className={`inline-block w-2 h-2 rounded-full ${
                          status[s.key]
                            ? "bg-brand-copper"
                            : "bg-brand-aluminum/60"
                        }`}
                      />
                      <span
                        className={
                          status[s.key]
                            ? "text-brand-charcoal/90"
                            : "text-brand-steel/50"
                        }
                      >
                        {s.label}
                      </span>
                    </li>
                  ))}
                </ul>
                <div className="mt-auto flex flex-wrap gap-2 items-center text-[11px] text-brand-steel/70">
                  <span className="px-2 py-0.5 rounded-full bg-brand-aluminum/40 text-brand-charcoal/80">
                    {datasetCount} dataset{datasetCount === 1 ? "" : "s"}
                  </span>
                  {project.analysisCount > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-brand-copper/15 text-brand-copper border border-brand-copper/30">
                      Analyzed
                    </span>
                  )}
                  {project.hasReport && (
                    <span className="px-2 py-0.5 rounded-full bg-brand-gold/15 text-brand-gold border border-brand-gold/30">
                      Report
                    </span>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      </Section>
    </>
  );
}
