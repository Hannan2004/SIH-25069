"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import Loader from "@/components/Loader";

export default function MissingValuesPage() {
  const { id } = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stepIndex, setStepIndex] = useState(0);
  const [diff, setDiff] = useState([]); // [{sheet, row, col, from:'', to:'123'}]

  const steps = [
    "Checking Indian defaults for electricity, transport, recycling",
    "Estimating missing process parameters (AI/ML)",
    "Running Monte Carlo (preview)",
  ];

  useEffect(() => {
    const projects = JSON.parse(localStorage.getItem("dc_projects") || "{}");
    const project = projects[id];
    if (!project || !project.sheetJSON) return;
    const blanks = [];
    Object.entries(project.sheetJSON.sheets).forEach(([sheetName, rows]) => {
      rows.forEach((row, rIdx) =>
        row.forEach((cell, cIdx) => {
          if (cell === "" || cell == null) {
            const newVal = (Math.random() * 10).toFixed(2);
            blanks.push({
              sheet: sheetName,
              row: rIdx,
              col: cIdx,
              from: "",
              to: newVal,
            });
          }
        })
      );
    });
    // Simulate staged progress
    let current = 0;
    const interval = setInterval(() => {
      current += 1;
      if (current < steps.length) setStepIndex(current);
      else {
        clearInterval(interval);
        setTimeout(() => {
          setLoading(false);
          setDiff(blanks);
        }, 1000);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [id]);

  const accept = () => {
    const projects = JSON.parse(localStorage.getItem("dc_projects") || "{}");
    const project = projects[id];
    if (!project || !project.sheetJSON) return;
    const updated = { ...project.sheetJSON.sheets };
    diff.forEach((d) => {
      updated[d.sheet][d.row][d.col] = d.to;
    });
    project.mappedJSON = { ...project.sheetJSON, sheets: updated };
    projects[id] = project;
    localStorage.setItem("dc_projects", JSON.stringify(projects));
    router.push(`/projects/${id}/analysis`);
  };

  return (
    <>
      <PageHero
        title="AI-Assisted Gap Mapping"
        description="Completing missing inventory parameters using localized defaults & ML estimation"
      />
      <Section>
        {loading ? (
          <Card className="p-10 text-center space-y-6">
            <Loader />
            <div>
              <p className="font-medium text-gray-700 mb-2 animate-pulse">
                {steps[stepIndex]}
              </p>
              <p className="text-sm text-gray-500">
                Step {stepIndex + 1} of {steps.length}
              </p>
            </div>
          </Card>
        ) : (
          <Card className="p-8">
            <h2 className="text-2xl font-semibold mb-4">Suggested Fills</h2>
            <p className="text-sm text-gray-600 mb-6">
              {diff.length} cells filled. Review the proposed values below.
            </p>
            <div className="max-h-96 overflow-auto border rounded-lg">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">Sheet</th>
                    <th className="px-4 py-2 text-left">Row</th>
                    <th className="px-4 py-2 text-left">Column</th>
                    <th className="px-4 py-2 text-left">Old</th>
                    <th className="px-4 py-2 text-left">New</th>
                  </tr>
                </thead>
                <tbody>
                  {diff.slice(0, 300).map((d, i) => (
                    <tr key={i} className="border-t">
                      <td className="px-4 py-1">{d.sheet}</td>
                      <td className="px-4 py-1">{d.row + 1}</td>
                      <td className="px-4 py-1">{d.col + 1}</td>
                      <td className="px-4 py-1 text-gray-400">
                        {d.from || "—"}
                      </td>
                      <td className="px-4 py-1 font-medium text-brand-emerald">
                        {d.to}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-6 flex justify-end">
              <Button onClick={accept}>Accept & Continue →</Button>
            </div>
          </Card>
        )}
      </Section>
    </>
  );
}
