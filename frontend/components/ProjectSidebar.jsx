"use client";
import Link from "next/link";
import { usePathname, useParams } from "next/navigation";

const steps = [
  { key: "upload", label: "Upload Datasets" },
  { key: "analysis", label: "Analysis" },
  { key: "results", label: "Results & Report" },
];

export default function ProjectSidebar() {
  const pathname = usePathname();
  const { id } = useParams();

  const currentIndex = steps.findIndex((s) => pathname.includes(`/${s.key}`));

  return (
    <aside className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3 tracking-wide">
          PROJECT PROGRESS
        </h3>
        <ol className="space-y-2">
          {steps.map((s, idx) => {
            const state =
              idx < currentIndex
                ? "done"
                : idx === currentIndex
                ? "active"
                : "upcoming";
            return (
              <li key={s.key}>
                <Link
                  href={`/projects/${id}/${s.key}`}
                  className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium border transition-colors ${
                    state === "active"
                      ? "border-brand-emerald bg-brand-sky text-brand-forest"
                      : state === "done"
                      ? "border-green-200 bg-green-50 text-green-700"
                      : "border-transparent hover:border-gray-200 text-gray-500 hover:text-gray-700"
                  }`}
                >
                  <span
                    className={`w-6 h-6 inline-flex items-center justify-center rounded-md text-xs font-semibold ${
                      state === "active"
                        ? "bg-brand-emerald text-white"
                        : state === "done"
                        ? "bg-green-500 text-white"
                        : "bg-gray-200 text-gray-600"
                    }`}
                  >
                    {state === "done" ? "✓" : idx + 1}
                  </span>
                  {s.label}
                </Link>
              </li>
            );
          })}
        </ol>
      </div>
      <div className="p-4 rounded-lg bg-brand-sky/60 border border-brand-sky text-xs text-brand-forest leading-relaxed">
        Track each stage of your LCA workflow. You can revisit earlier steps to
        adjust inputs before final reporting.
      </div>
    </aside>
  );
}
