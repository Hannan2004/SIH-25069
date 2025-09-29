import Link from "next/link";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import FeatureIcon from "@/components/FeatureIcon";
import Button from "@/components/Button";
import {
  ArrowRight,
  Target,
  Ruler,
  Globe,
  TrendingUp,
  Layers,
  Activity,
  Globe2,
  Box,
} from "lucide-react";

export const metadata = {
  title: "Goal & Scope - DhatuChakr",
  description:
    "Define objective, functional unit, boundaries, and impact category for your LCA study (ISO 14040/44 aligned).",
};

export default function GoalScopePage() {
  // (Methodology steps removed from this page — progress now appears within project pages sidebar.)

  const scopeElements = [
    {
      icon: Target,
      title: "Goal",
      content:
        "Quantify cradle‑to‑gate GWP for producing 1 kg aluminium ingot under Indian operating & supply chain conditions.",
      color: "copper",
    },
    {
      icon: Ruler,
      title: "Functional Unit",
      content:
        "1 kg primary aluminium ingot (IS 737:2020 compliant) at plant gate ready for downstream fabrication.",
      color: "steel",
    },
    {
      icon: Globe,
      title: "System Boundary",
      content:
        "Cradle‑to‑gate: Bauxite mining → Alumina refining → Primary smelting → Casting/finishing → Outbound transport.",
      color: "charcoal",
    },
    {
      icon: TrendingUp,
      title: "Impact Category",
      content:
        "Climate change (GWP100, kg CO₂e) using IPCC AR6 characterization factors — additional categories pending.",
      color: "gold",
    },
  ];

  const additional = [
    {
      icon: Box,
      title: "Geography",
      value:
        "India (regional grid mix, logistics modal split, scrap availability)",
      note: "User-overridable",
    },
    {
      icon: Layers,
      title: "Allocation",
      value: "Physical allocation; mass basis for multi‑output refinery nodes",
      note: "Economic sensitivity later",
    },
    {
      icon: Activity,
      title: "Data Quality",
      value: "Tiered: Primary plant data + curated secondary emission factors",
      note: "DQI scoring planned",
    },
    {
      icon: Globe2,
      title: "Temporal Scope",
      value: "2024–2025 operating year baseline (rolling updates supported)",
      note: "Historic compare next",
    },
  ];

  return (
    <>
      <PageHero
        title="Goal & Scope Definition"
        description="Following ISO 14040/44 methodology, we establish clear objectives and boundaries for your LCA study"
        spacing="standard"
      />

      <Section className="bg-[#ffffff]">
        <div className="max-w-6xl mx-auto space-y-12">
          {/* Scope Definition Cards */}
          <div>
            <h3 className="text-xl font-semibold mb-6 text-brand-charcoal tracking-tight">
              Study Scope Definition
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {scopeElements.map((element, index) => (
                <Card
                  key={index}
                  className="h-full bg-white/80 backdrop-blur-sm border border-brand-copper/25"
                >
                  <FeatureIcon
                    icon={element.icon}
                    color={element.color}
                    variant="soft"
                    className="mb-4"
                  />
                  <h4 className="text-lg font-semibold mb-3 text-brand-charcoal">
                    {element.title}
                  </h4>
                  <p className="text-sm leading-relaxed text-brand-charcoal/80">
                    {element.content}
                  </p>
                </Card>
              ))}
            </div>
            <h3 className="text-xl font-semibold mt-12 mb-6 text-brand-charcoal tracking-tight">
              Additional Parameters
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
              {additional.map((a, i) => (
                <Card
                  key={i}
                  className="p-6 flex flex-col bg-white/80 border border-brand-copper/25"
                >
                  <div className="flex items-start space-x-4 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-brand-copper/10 flex items-center justify-center">
                      <a.icon className="h-5 w-5 text-brand-copper" />
                    </div>
                    <div>
                      <h4 className="font-semibold mb-1 text-brand-charcoal">
                        {a.title}
                      </h4>
                      <p className="text-sm text-brand-charcoal/80 leading-relaxed">
                        {a.value}
                      </p>
                    </div>
                  </div>
                  {a.note && (
                    <p className="text-xs text-brand-charcoal/60 mt-auto">
                      {a.note}
                    </p>
                  )}
                </Card>
              ))}
            </div>
            <div className="rounded-xl p-6 border border-brand-copper/30 bg-white/70 backdrop-blur-sm">
              <h4 className="font-semibold mb-2 text-brand-charcoal">
                Standards & Methodology
              </h4>
              <p className="text-sm text-brand-charcoal/80 leading-relaxed">
                Based on ISO 14040/44 framework. Current scope covers climate
                change (GWP100, IPCC AR6). Indian localization includes regional
                grid mix, logistics modal share and upstream raw material
                emission factors. Roadmap: add energy demand, water use,
                toxicity categories and circularity KPIs (recycled content %,
                EoL recovery, closed‑loop share).
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
              <Card className="p-6 bg-white/80 border border-brand-copper/30">
                <h4 className="font-semibold mb-3 text-brand-charcoal">
                  Included Processes
                </h4>
                <ul className="text-sm text-brand-charcoal/80 space-y-1 list-disc pl-4">
                  <li>Ore extraction & beneficiation</li>
                  <li>Alumina refining (Bayer)</li>
                  <li>Primary electrolysis (Hall–Héroult)</li>
                  <li>Anode production & consumption</li>
                  <li>Molten metal casting & finishing</li>
                  <li>Inbound & outbound logistics within boundary</li>
                </ul>
              </Card>
              <Card className="p-6 bg-white/80 border border-brand-copper/30">
                <h4 className="font-semibold mb-3 text-brand-charcoal">
                  Excluded / Not Yet Modeled
                </h4>
                <ul className="text-sm text-brand-charcoal/80 space-y-1 list-disc pl-4">
                  <li>Capital goods (equipment manufacture)</li>
                  <li>Downstream fabrication (rolling/extrusion)</li>
                  <li>Use phase & end‑of‑life pathways</li>
                  <li>Packaging materials</li>
                  <li>Worker commuting & tertiary services</li>
                </ul>
              </Card>
            </div>
          </div>
        </div>
      </Section>
      <Section className="bg-[#FDF3EA]">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-center mb-12 text-brand-charcoal tracking-tight">
            System Boundary Visualization
          </h2>
          <div className="rounded-xl p-8 bg-white/80 backdrop-blur-sm border border-brand-copper/30 relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-stretch md:justify-between gap-6 relative">
              {[
                { name: "Bauxite Mining", tone: "copper" },
                { name: "Alumina Refining", tone: "steel" },
                { name: "Primary Smelting", tone: "charcoal" },
                { name: "Casting / Finishing", tone: "aluminum" },
                { name: "Outbound Transport", tone: "gold" },
              ].map((stage, idx, arr) => (
                <div key={idx} className="relative flex-1 min-w-[160px]">
                  <div className="rounded-lg px-4 py-5 text-center shadow-sm border border-brand-copper/30 bg-white/70">
                    <p className="text-xs font-medium tracking-wide text-brand-charcoal/70 mb-1">
                      Stage {idx + 1}
                    </p>
                    <p className="text-sm font-semibold text-brand-charcoal leading-snug">
                      {stage.name}
                    </p>
                  </div>
                  {idx < arr.length - 1 && (
                    <div className="hidden md:block absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 w-20 h-[2px] bg-gradient-to-r from-brand-copper/60 to-brand-copper">
                      <span className="absolute -right-1 -top-1 h-3 w-3 rotate-45 bg-brand-copper"></span>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="p-4 bg-white/70 border border-brand-copper/30">
                <h5 className="font-semibold mb-2 text-brand-charcoal text-sm">
                  Flow Coverage
                </h5>
                <p className="text-xs text-brand-charcoal/70 leading-relaxed">
                  Includes upstream raw material extraction, process energy,
                  consumables (anodes, fluxes) and direct process emissions
                  (CO₂, PFCs) up to cast ingot delivery.
                </p>
              </Card>
              <Card className="p-4 bg-white/70 border border-brand-copper/30">
                <h5 className="font-semibold mb-2 text-brand-charcoal text-sm">
                  Transport Logic
                </h5>
                <p className="text-xs text-brand-charcoal/70 leading-relaxed">
                  Default outbound: blended rail / road share; inbound bauxite +
                  alumina legs modeled with regional distance factors.
                </p>
              </Card>
              <Card className="p-4 bg-white/70 border border-brand-copper/30">
                <h5 className="font-semibold mb-2 text-brand-charcoal text-sm">
                  Planned Extensions
                </h5>
                <p className="text-xs text-brand-charcoal/70 leading-relaxed">
                  Add recycling loops, allocation sensitivity, electricity
                  decarbonization scenarios and downstream fabrication.
                </p>
              </Card>
            </div>
          </div>
        </div>
      </Section>

      <Section className="bg-[#ffffff]">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="mb-6 text-brand-charcoal">
            Ready to Begin Your Analysis?
          </h2>
          <p className="text-lg text-brand-charcoal/80 mb-8 leading-relaxed">
            With goal & scope defined you can initiate a project and begin
            curated data ingestion & modelling.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/projects/new">
              <Button size="lg" className="group">
                Start New Analysis
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link href="/">
              <Button variant="outline" size="lg">
                Back to Home
              </Button>
            </Link>
          </div>
        </div>
      </Section>
    </>
  );
}
