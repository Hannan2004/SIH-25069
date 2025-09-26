import Link from "next/link";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import Stat from "@/components/Stat";

export const metadata = { title: "Analysis - DhatuChakr" };

export default function AnalysisPage() {
  const stats = [
    {
      label: "Total GWP (kg CO₂e/kg)",
      value: "8.42",
      note: "Sample placeholder",
    },
    { label: "Mining Share %", value: "22%", note: "Distribution placeholder" },
    {
      label: "Smelting Share %",
      value: "46%",
      note: "Distribution placeholder",
    },
    { label: "Recycled Content %", value: "34%", note: "Scenario placeholder" },
  ];
  return (
    <>
      <PageHero
        title="LCA Analysis (Preview)"
        description="Computation engine integration coming soon (Brightway/OpenLCA compatible). Displaying layout placeholders."
      />
      <Section>
        <div className="grid md:grid-cols-4 gap-6 mb-12">
          {stats.map((s, i) => (
            <Stat key={i} label={s.label} value={s.value} note={s.note} />
          ))}
        </div>
        <Card className="p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-4">
            Impact Breakdown (Placeholder)
          </h2>
          <p className="text-gray-600 mb-4 text-sm">
            A stagewise contribution chart will appear here once the engine is
            integrated.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            {["Mining", "Refining", "Smelting", "Casting", "Transport"].map(
              (stage) => (
                <div key={stage} className="p-4 rounded-lg bg-gray-50 border">
                  <p className="font-medium mb-1">{stage}</p>
                  <p className="text-gray-500">Placeholder metrics</p>
                </div>
              )
            )}
          </div>
        </Card>
        <div className="flex gap-4">
          <Link href="../results">
            <Button>View Results →</Button>
          </Link>
          <Link href="../upload">
            <Button variant="outline">Edit Inputs</Button>
          </Link>
        </div>
      </Section>
    </>
  );
}
