"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Globe, TrendingUp } from "lucide-react";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import FeatureIcon from "@/components/FeatureIcon";
import { createProject } from "@/lib/projects";
import { useUser } from "@/context/UserContext";

export default function NewProjectPage() {
  const { user, loading } = useUser();
  const [formData, setFormData] = useState({
    projectName: "",
    metal: "",
    geography: "India",
    method: "IPCC GWP100",
    dataSource: "India Defaults",
    studyType: "internal_decision_support",
    analysisType: "cradle_to_gate",
    reportType: "technical",
  });
  const router = useRouter();

  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      if (!user) throw new Error("You must be signed in to create a project");
      const projectId = await createProject(
        {
          name: formData.projectName,
          metal: formData.metal,
          geography: formData.geography,
          method: formData.method,
          dataSource: formData.dataSource,
          studyType: formData.studyType,
          analysisType: formData.analysisType,
          reportType: formData.reportType,
          status: "draft",
        },
        user
      );
      router.push(`/projects/${projectId}/upload`);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  // Redirect unauthenticated users once loading completes
  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/signin");
    }
  }, [loading, user, router]);

  if (loading || (!user && typeof window !== "undefined")) {
    return (
      <Section>
        <div className="max-w-2xl mx-auto py-20 text-center text-gray-500">
          Loading user...
        </div>
      </Section>
    );
  }

  if (!user) return null; // safety

  return (
    <>
      <PageHero
        title="Create New LCA Analysis"
        description="Set up your project parameters and begin comprehensive life cycle assessment"
        spacing="standard"
      />

      <Section>
        <div className="max-w-2xl mx-auto">
          <Card className="p-8">
            <div className="text-center mb-8">
              <FeatureIcon icon={Plus} size="lg" className="mx-auto mb-4" />
              <h2 className="text-2xl font-semibold mb-2">Project Setup</h2>
              <p className="text-gray-600">
                Configure your analysis parameters to ensure accurate and
                relevant results
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded-lg">
                  {error}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Name
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                  placeholder="e.g., Aluminium Ingot Production - Plant ABC"
                  value={formData.projectName}
                  onChange={(e) =>
                    setFormData({ ...formData, projectName: e.target.value })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  Choose a descriptive name for easy identification
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Metal Type
                </label>
                <select
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                  value={formData.metal}
                  onChange={(e) =>
                    setFormData({ ...formData, metal: e.target.value })
                  }
                >
                  <option value="">Select Metal</option>
                  <option value="Aluminium">Aluminium</option>
                  <option value="Copper">Copper</option>
                  <option value="Critical Mineral">Critical Mineral</option>
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Geography
                  </label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <select
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                      value={formData.geography}
                      onChange={(e) =>
                        setFormData({ ...formData, geography: e.target.value })
                      }
                    >
                      <option value="India">India</option>
                      <option value="Asia-Pacific">Asia-Pacific</option>
                      <option value="Global">Global</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    LCIA Method
                  </label>
                  <div className="relative">
                    <TrendingUp className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <select
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                      value={formData.method}
                      onChange={(e) =>
                        setFormData({ ...formData, method: e.target.value })
                      }
                    >
                      <option value="IPCC GWP100">IPCC GWP100</option>
                      <option value="ReCiPe 2016">ReCiPe 2016</option>
                      <option value="EF 3.0">EF 3.0</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Study Type
                  </label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                    value={formData.studyType}
                    onChange={(e) =>
                      setFormData({ ...formData, studyType: e.target.value })
                    }
                  >
                    <option value="internal_decision_support">
                      Internal Decision Support
                    </option>
                    <option value="comparative_assertion">
                      Comparative Assertion
                    </option>
                    <option value="public_communication">
                      Public Communication
                    </option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Analysis Type
                  </label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                    value={formData.analysisType}
                    onChange={(e) =>
                      setFormData({ ...formData, analysisType: e.target.value })
                    }
                  >
                    <option value="cradle_to_gate">Cradle to Gate</option>
                    <option value="cradle_to_grave">Cradle to Grave</option>
                    <option value="gate_to_gate">Gate to Gate</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Report Type
                  </label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                    value={formData.reportType}
                    onChange={(e) =>
                      setFormData({ ...formData, reportType: e.target.value })
                    }
                  >
                    <option value="technical">Technical</option>
                    <option value="executive">Executive</option>
                    <option value="regulatory">Regulatory</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Source Preset
                </label>
                <select
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                  value={formData.dataSource}
                  onChange={(e) =>
                    setFormData({ ...formData, dataSource: e.target.value })
                  }
                >
                  <option value="India Defaults">India Defaults</option>
                  <option value="Custom Dataset">Custom Dataset</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  India Defaults include local grid mix, transport patterns, and
                  recycling data
                </p>
              </div>

              <div className="bg-brand-sky rounded-xl p-4">
                <h4 className="font-semibold text-brand-forest mb-2">
                  India-Calibrated Defaults Include:
                </h4>
                <ul className="text-sm text-brand-forest space-y-1">
                  <li>
                    • State-wise electricity grid emission factors (2023-24)
                  </li>
                  <li>• Transport mix optimization (road vs rail logistics)</li>
                  <li>• Domestic scrap availability and recycling rates</li>
                  <li>• Industrial process efficiency benchmarks</li>
                </ul>
              </div>

              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={creating}
              >
                {creating ? "Creating..." : "Create Project & Continue"}
              </Button>
            </form>
          </Card>
        </div>
      </Section>
    </>
  );
}
