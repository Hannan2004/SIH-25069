"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { LogIn, Mail, Lock, Building, Briefcase } from "lucide-react";
import PageHero from "@/components/PageHero";
import Section from "@/components/Section";
import Card from "@/components/Card";
import Button from "@/components/Button";
import {
  signInEmailPassword,
  signInWithGoogleRaw,
  saveUserProfile,
} from "@/lib/auth";
import Image from "next/image";
import { useUser } from "@/context/UserContext";

export default function SignInPage() {
  const { setUser } = useUser();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [googleState, setGoogleState] = useState({
    stage: "idle", // idle | authed-new | saving
    tempUser: null,
    org: "",
    role: "",
    industry: "",
  });
  const router = useRouter();

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
    setIsLoading(true);
    try {
      const profile = await signInEmailPassword({
        email: formData.email,
        password: formData.password,
      });
      setUser(profile);
      router.push("/projects/new");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to sign in");
    } finally {
      setIsLoading(false);
    }
  };

  const startGoogle = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const { isNewUser, authUser, existingProfile } =
        await signInWithGoogleRaw();
      if (isNewUser) {
        setGoogleState({
          stage: "authed-new",
          tempUser: authUser,
          org: "",
          role: "",
          industry: "",
        });
      } else {
        const profile = { uid: authUser.uid, ...existingProfile, ...authUser };
        setUser(profile);
        router.push("/projects/new");
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Google sign-in failed");
    } finally {
      setIsLoading(false);
    }
  };

  const completeGoogleProfile = async (e) => {
    e.preventDefault();
    if (googleState.stage !== "authed-new" || !googleState.tempUser) return;
    setError(null);
    setIsLoading(true);
    try {
      if (!googleState.org || !googleState.role || !googleState.industry) {
        setError("All fields are required");
        setIsLoading(false);
        return;
      }
      const saved = await saveUserProfile(googleState.tempUser.uid, {
        name: googleState.tempUser.name,
        email: googleState.tempUser.email,
        photoURL: googleState.tempUser.photoURL,
        org: googleState.org,
        role: googleState.role,
        industry: googleState.industry,
        provider: "google",
      });
      const profile = { uid: googleState.tempUser.uid, ...saved };
      setUser(profile);
      router.push("/projects/new");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to save profile");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <PageHero
        title="Welcome Back"
        description="Sign in to your DhatuChakr account to continue your LCA analysis"
        spacing="compact"
      />

      <Section>
        <div className="max-w-md mx-auto">
          <Card className="p-8 bg-white/70 backdrop-blur-md border border-brand-copper/30 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.08)]">
            <div className="text-center mb-8">
              <div className={sectionBadge}>
                <LogIn className="h-6 w-6 text-brand-copper" />
              </div>
              <h2 className="text-2xl font-semibold tracking-tight text-brand-charcoal">
                Sign In
              </h2>
            </div>

            {googleState.stage === "authed-new" ? (
              <form onSubmit={completeGoogleProfile} className="space-y-6">
                {error && (
                  <div className="text-sm text-red-700/90 bg-red-50/80 border border-red-200/70 px-3 py-2 rounded-lg">
                    {error}
                  </div>
                )}
                <div className="space-y-4 border border-brand-aluminum/60 rounded-xl p-4 bg-white/60">
                  <p className="text-sm font-medium text-brand-charcoal/80">
                    Welcome{" "}
                    {googleState.tempUser?.name || googleState.tempUser?.email}!
                    Complete your profile to continue.
                  </p>
                  <div>
                    <label className={labelCls}>Organization</label>
                    <div className="relative">
                      <Building className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                      <input
                        type="text"
                        required
                        className={iconInputBase}
                        placeholder="Company Name"
                        value={googleState.org}
                        onChange={(e) =>
                          setGoogleState((s) => ({ ...s, org: e.target.value }))
                        }
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className={labelCls}>Role</label>
                      <div className="relative">
                        <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                        <input
                          type="text"
                          required
                          className={iconInputBase}
                          placeholder="Sustainability Manager"
                          value={googleState.role}
                          onChange={(e) =>
                            setGoogleState((s) => ({
                              ...s,
                              role: e.target.value,
                            }))
                          }
                        />
                      </div>
                    </div>
                    <div>
                      <label className={labelCls}>Industry</label>
                      <input
                        type="text"
                        required
                        className={inputBase}
                        placeholder="Primary Aluminium"
                        value={googleState.industry}
                        onChange={(e) =>
                          setGoogleState((s) => ({
                            ...s,
                            industry: e.target.value,
                          }))
                        }
                      />
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="ghost"
                    className="flex-1"
                    disabled={isLoading}
                    onClick={() =>
                      setGoogleState({
                        stage: "idle",
                        tempUser: null,
                        org: "",
                        role: "",
                        industry: "",
                      })
                    }
                  >
                    Cancel
                  </Button>
                  <Button type="submit" className="flex-1" disabled={isLoading}>
                    {isLoading ? "Saving..." : "Finish Sign Up"}
                  </Button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                  <div className="text-sm text-red-700/90 bg-red-50/80 border border-red-200/70 px-3 py-2 rounded-lg">
                    {error}
                  </div>
                )}
                <div>
                  <label className={labelCls}>Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                    <input
                      type="email"
                      required
                      className={iconInputBase}
                      placeholder="your@email.com"
                      value={formData.email}
                      onChange={(e) =>
                        setFormData({ ...formData, email: e.target.value })
                      }
                    />
                  </div>
                </div>
                <div>
                  <label className={labelCls}>Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-brand-steel/50" />
                    <input
                      type="password"
                      required
                      className={iconInputBase}
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({ ...formData, password: e.target.value })
                      }
                    />
                  </div>
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={isLoading}
                >
                  {isLoading ? "Signing In..." : "Sign In"}
                </Button>
                <div className="relative">
                  <div className="flex items-center my-2">
                    <div className="flex-grow h-px bg-brand-aluminum/60" />
                    <span className="px-3 text-xs uppercase tracking-wide text-brand-steel/60">
                      Or
                    </span>
                    <div className="flex-grow h-px bg-brand-aluminum/60" />
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full group !border-brand-copper/40 bg-white/70 hover:bg-brand-copper/10 hover:border-brand-copper/60"
                    onClick={startGoogle}
                    disabled={isLoading}
                  >
                    <span className="flex items-center justify-center font-medium text-brand-charcoal">
                      <span className="relative flex items-center justify-center w-6 h-6 mr-2 rounded-md bg-white shadow-inner ring-1 ring-brand-aluminum/70 group-hover:ring-brand-copper/60 transition">
                        <Image
                          src="/google-icon.svg"
                          alt="Google"
                          width={14}
                          height={14}
                          className="opacity-90 group-hover:opacity-100 transition"
                        />
                        <span className="absolute inset-0 rounded-md bg-brand-copper/0 group-hover:bg-brand-copper/5 transition" />
                      </span>
                      Continue with Google
                    </span>
                  </Button>
                </div>
              </form>
            )}

            <div className="mt-6 text-center">
              <p className="text-brand-steel">
                Don't have an account?{" "}
                <Link
                  href="/auth/signup"
                  className="text-brand-copper hover:underline font-medium"
                >
                  Sign up
                </Link>
              </p>
            </div>
          </Card>
        </div>
      </Section>
    </>
  );
}
