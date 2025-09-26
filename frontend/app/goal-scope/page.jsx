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
        "Assess cradle-to-gate global warming potential (GWP) for producing 1 kg aluminium ingot in Indian conditions",
      color: "brand-emerald",
    },
    {
      icon: Ruler,
      title: "Functional Unit",
      content:
        "1 kilogram of primary aluminium ingot, meeting IS 737:2020 standards for commercial purity",
      color: "brand-copper",
    },
    {
      icon: Globe,
      title: "System Boundary",
      content:
        "Cradle-to-gate: Bauxite mining → Alumina refining → Primary smelting → Casting → Transport to customer",
      color: "brand-steel",
    },
    {
      icon: TrendingUp,
      title: "Impact Category",
      content:
        "Climate change potential (kg CO₂-eq, 100-year GWP, IPCC AR6 characterization factors)",
      color: "accent-sun",
    },
  ];

  const additional = [
    {
      icon: Box,
      title: "Goal",
      value: "Assess cradle-to-gate GWP for producing 1 kg aluminium ingot",
      note: "Benchmark & improve",
    },
    {
      icon: Layers,
      title: "System Boundary",
      value: "Mining → Refining → Smelting → Casting → Transport",
      note: "Cradle-to-gate",
    },
    {
      icon: Activity,
      title: "Impact Category",
      value: "Climate change (kg CO₂e, 100-year GWP, IPCC AR6)",
      note: "More coming soon",
    },
    {
      icon: Globe2,
      title: "Geography Defaults",
      value: "India grid mix, transport split, scrap flows",
      note: "Editable later",
    },
  ];

  return (
    <>
      <PageHero
        title="Goal & Scope Definition"
        description="Following ISO 14040/44 methodology, we establish clear objectives and boundaries for your LCA study"
      />

      <Section>
        <div className="max-w-6xl mx-auto space-y-12">
          {/* Scope Definition Cards */}
          <div>
            <h3 className="text-xl font-semibold mb-6">
              Study Scope Definition
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {scopeElements.map((element, index) => (
                <Card key={index} className="h-full">
                  <FeatureIcon
                    icon={element.icon}
                    color={element.color}
                    className="mb-4"
                  />
                  <h4 className="text-lg font-semibold mb-3">
                    {element.title}
                  </h4>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {element.content}
                  </p>
                </Card>
              ))}
            </div>

            <h3 className="text-xl font-semibold mt-12 mb-6">
              Additional Parameters
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
              {additional.map((a, i) => (
                <Card key={i} className="p-6 flex flex-col">
                  <div className="flex items-start space-x-4 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-brand-sky flex items-center justify-center">
                      <a.icon className="h-5 w-5 text-brand-emerald" />
                    </div>
                    <div>
                      <h4 className="font-semibold mb-1">{a.title}</h4>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {a.value}
                      </p>
                    </div>
                  </div>
                  {a.note && (
                    <p className="text-xs text-gray-500 mt-auto">{a.note}</p>
                  )}
                </Card>
              ))}
            </div>
            <div className="bg-brand-sky/60 rounded-xl p-6 border border-brand-sky">
              <h4 className="font-semibold mb-2 text-brand-forest">
                Standards & Methodology
              </h4>
              <p className="text-sm text-brand-forest leading-relaxed">
                Methodological framing references ISO 14040/44. Impact category
                presently limited to climate change (GWP100) with Indian
                localized assumptions (grid mix, transport logistics, recycling
                flows). Future expansion will add energy, water, toxicity, and
                circularity indicators (recycled content, EoL collection
                efficiency, closed-loop fractions).
              </p>
            </div>
          </div>
        </div>
      </Section>

      <Section background="gray">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-center mb-12">System Boundary Visualization</h2>

          {/* Process Flow Diagram */}
          <div className="bg-white rounded-xl p-8 shadow-sm border">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6 items-center">
              {[
                {
                  name: "Bauxite Mining",
                  color: "bg-amber-100 text-amber-800",
                },
                {
                  name: "Alumina Refining",
                  color: "bg-blue-100 text-blue-800",
                },
                { name: "Primary Smelting", color: "bg-red-100 text-red-800" },
                {
                  name: "Casting",
                  color: "bg-brand-aluminum/30 text-brand-steel",
                },
                { name: "Transport", color: "bg-green-100 text-green-800" },
              ].map((stage, index) => (
                <div key={index} className="text-center">
                  <div className={`${stage.color} rounded-lg p-4 mb-3`}>
                    <div className="text-sm font-medium">{stage.name}</div>
                  </div>
                  {index < 4 && (
                    <div className="hidden md:block absolute transform translate-x-full -translate-y-6">
                      <ArrowRight className="h-5 w-5 text-gray-400" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="mt-8 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold mb-2">
                Key Assumptions & Data Sources
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Indian electricity grid mix (2023-24 CEA data)</li>
                <li>
                  • Transport via road (60%) and rail (40%) - typical Indian
                  logistics
                </li>
                <li>
                  • Primary aluminium production (excludes recycled content in
                  this baseline)
                </li>
                <li>• Plant-gate allocation for multi-product facilities</li>
              </ul>
            </div>
          </div>
        </div>
      </Section>

      <Section>
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="mb-6">Ready to Begin Your Analysis?</h2>
          <p className="text-xl text-gray-600 mb-8 leading-relaxed">
            With your goal and scope clearly defined, you can now proceed to
            create a new project and start collecting your inventory data.
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
