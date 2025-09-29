"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { UserPlus, User, Building, Briefcase, Mail, Lock } from "lucide-react";
import { signUpEmailPassword } from "@/lib/auth";
import { useUser } from "@/context/UserContext";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";

export default function SignUpPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    org: "",
    role: "",
    industry: "",
    password: "",
    confirmPassword: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const router = useRouter();
  const { setUser } = useUser();

  const industries = [
    "Primary Aluminium",
    "Secondary Aluminium",
    "Copper Smelting/Refining",
    "Rolling/Extrusion",
    "Recycling/EPR",
    "Other",
  ];

  const focusRing =
    "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-copper/60";
  const inputBase =
    "w-full rounded-xl border border-brand-aluminum/60 bg-white/60 backdrop-blur-sm px-4 py-3 text-sm placeholder:text-brand-steel/50 transition shadow-sm focus:border-brand-copper/60 " +
    focusRing;
  const iconInputBase =
    "w-full pl-10 pr-4 py-3 rounded-xl border border-brand-aluminum/60 bg-white/60 backdrop-blur-sm text-sm placeholder:text-brand-steel/50 transition shadow-sm focus:border-brand-copper/60 " +
    focusRing;
  const labelCls = "block text-sm font-medium text-brand-steel mb-2";
  const sectionBadge =
    "w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4 bg-gradient-to-br from-brand-copper/15 via-brand-gold/10 to-brand-steel/10 border border-brand-copper/30";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setIsLoading(true);
    try {
      const profile = await signUpEmailPassword({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        org: formData.org,
        role: formData.role,
        industry: formData.industry,
      });
      setUser(profile);
      router.push("/projects/new");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to create account");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <PageHero
        title="Get Started with DhatuChakr"
        description="Create your account to begin AI-assisted LCA analysis for metals and critical minerals"
        spacing="compact"
      />

      <Section>
        <div className="max-w-lg mx-auto">
          <Card className="p-8 bg-white/70 backdrop-blur-md border border-brand-copper/30 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.08)]">
            <div className="text-center mb-8">
              <div className={sectionBadge}>
                <UserPlus className="h-6 w-6 text-brand-copper" />
              </div>
              <h2 className="text-2xl font-semibold tracking-tight text-brand-charcoal">
                Create Account
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="text-sm text-red-700/90 bg-red-50/80 border border-red-200/70 px-3 py-2 rounded-lg">
                  {error}
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>Full Name</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                    <input
                      type="text"
                      required
                      className={iconInputBase}
                      placeholder="John Doe"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div>
                  <label className={labelCls}>Work Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                    <input
                      type="email"
                      required
                      className={iconInputBase}
                      placeholder="john@company.com"
                      value={formData.email}
                      onChange={(e) =>
                        setFormData({ ...formData, email: e.target.value })
                      }
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>Organization</label>
                  <div className="relative">
                    <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                    <input
                      type="text"
                      required
                      className={iconInputBase}
                      placeholder="Company Name"
                      value={formData.org}
                      onChange={(e) =>
                        setFormData({ ...formData, org: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div>
                  <label className={labelCls}>Role</label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                    <input
                      type="text"
                      required
                      className={iconInputBase}
                      placeholder="Sustainability Manager"
                      value={formData.role}
                      onChange={(e) =>
                        setFormData({ ...formData, role: e.target.value })
                      }
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className={labelCls}>Industry</label>
                <select
                  required
                  className={inputBase}
                  value={formData.industry}
                  onChange={(e) =>
                    setFormData({ ...formData, industry: e.target.value })
                  }
                >
                  <option value="">Select Industry</option>
                  {industries.map((industry) => (
                    <option key={industry} value={industry}>
                      {industry}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={labelCls}>Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                    <input
                      type="password"
                      required
                      minLength={8}
                      className={iconInputBase}
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({ ...formData, password: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div>
                  <label className={labelCls}>Confirm Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                    <input
                      type="password"
                      required
                      className={iconInputBase}
                      placeholder="••••••••"
                      value={formData.confirmPassword}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          confirmPassword: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={isLoading}
              >
                {isLoading ? "Creating Account..." : "Create Account"}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-brand-steel">
                Already have an account?{" "}
                <Link
                  href="/auth/signin"
                  className="text-brand-copper hover:underline font-medium"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </Card>
        </div>
      </Section>
    </>
  );
}
