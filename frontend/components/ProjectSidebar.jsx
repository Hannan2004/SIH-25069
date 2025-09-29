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
        <h3 className="text-sm font-semibold text-brand-steel mb-3 tracking-wide">
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
                  className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium border transition-all shadow-sm ${
                    state === "active"
                      ? "border-brand-copper bg-white/80 text-brand-charcoal"
                      : state === "done"
                      ? "border-brand-gold/40 bg-brand-gold/15 text-brand-gold"
                      : "border-brand-aluminum/40 bg-white/50 text-brand-steel/70 hover:border-brand-copper/40 hover:text-brand-charcoal"
                  }`}
                >
                  <span
                    className={`w-6 h-6 inline-flex items-center justify-center rounded-md text-xs font-semibold transition-all ${
                      state === "active"
                        ? "bg-brand-copper text-white shadow"
                        : state === "done"
                        ? "bg-brand-gold text-white"
                        : "bg-brand-aluminum/70 text-brand-steel/70"
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
      <div className="p-4 rounded-lg bg-white/60 backdrop-blur-sm border border-brand-copper/25 text-xs text-brand-steel/80 leading-relaxed">
        Track each stage of your LCA workflow. You can revisit earlier steps to
        adjust inputs before final reporting.
      </div>
    </aside>
  );
}
