"use client";

import { useEffect, useState } from "react";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import Link from "next/link";

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
  const [projects, setProjects] = useState({});
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userData = localStorage.getItem("dc_user");
    if (userData) setUser(JSON.parse(userData));
    const stored = JSON.parse(localStorage.getItem("dc_projects") || "{}");
    setProjects(stored);
  }, []);

  const projectEntries = Object.entries(projects);

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
      />
      <Section>
        <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
          <h2 className="text-lg font-semibold text-gray-800">Your Projects</h2>
          <Link href="/projects/new">
            <Button size="sm">+ Add Project</Button>
          </Link>
        </div>
        {projectEntries.length === 0 && (
          <Card className="p-8 text-center space-y-4">
            <p className="text-gray-600 text-sm">You have no projects yet.</p>
            <Link href="/projects/new">
              <Button>Create your first project</Button>
            </Link>
          </Card>
        )}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projectEntries.map(([id, project]) => {
            const { steps, status, completedCount } = computeProgress(project);
            const pct = Math.round((completedCount / steps.length) * 100);
            const datasetCount = project.sheetJSON?.datasets
              ? Object.keys(project.sheetJSON.datasets).length
              : project.sheetJSON?.sheets
              ? Object.keys(project.sheetJSON.sheets).length
              : 0;
            return (
              <Card key={id} className="p-5 flex flex-col">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {project.name || "Untitled Project"}
                    </h3>
                    <p className="text-xs text-gray-500 mt-0.5">ID: {id}</p>
                  </div>
                  <Link
                    href={`/projects/${id}/upload`}
                    className="text-xs text-brand-emerald font-medium hover:underline"
                  >
                    Open →
                  </Link>
                </div>
                <div className="mb-4">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-brand-emerald to-brand-forest transition-all"
                      style={{ width: pct + "%" }}
                    />
                  </div>
                  <p className="mt-1 text-[11px] text-gray-500 tracking-wide">
                    Progress: {pct}%
                  </p>
                </div>
                <ul className="space-y-1 mb-4 text-xs">
                  {steps.map((s) => (
                    <li key={s.key} className="flex items-center gap-2">
                      <span
                        className={`inline-block w-2 h-2 rounded-full ${
                          status[s.key] ? "bg-brand-emerald" : "bg-gray-300"
                        }`}
                      />
                      <span
                        className={
                          status[s.key] ? "text-gray-700" : "text-gray-400"
                        }
                      >
                        {s.label}
                      </span>
                    </li>
                  ))}
                </ul>
                <div className="mt-auto flex flex-wrap gap-2 items-center text-[11px] text-gray-500">
                  <span className="px-2 py-0.5 rounded-full bg-gray-100">
                    {datasetCount} dataset{datasetCount === 1 ? "" : "s"}
                  </span>
                  {project.mappedJSON && (
                    <span className="px-2 py-0.5 rounded-full bg-brand-sky/40 text-brand-forest">
                      Mapped
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
