"use client";

import { useMemo } from "react";
import Spline from "@splinetool/react-spline/next";

export default function PageHero({
  title,
  description,
  children,
  className = "",
  splineScene,
  dense = false,
}) {
  const has3D = Boolean(splineScene);
  const padding = dense ? "py-10" : "py-16 md:py-24";

  return (
    <div
      className={`relative overflow-hidden ${padding} gradient-bg ${className}`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div
          className={`grid gap-12 items-center ${
            has3D ? "lg:grid-cols-2" : ""
          }`}
        >
          {/* Left Content */}
          <div className="max-w-xl">
            <h1 className="text-gradient mb-6 leading-tight">{title}</h1>
            {description && (
              <p className="text-lg md:text-xl text-brand-charcoal/80 leading-relaxed mb-8">
                {description}
              </p>
            )}
            {children && <div className="flex flex-wrap gap-4">{children}</div>}
          </div>
          {/* Right 3D Scene */}
          {has3D && (
            <div className="relative h-[340px] sm:h-[420px] md:h-[480px] lg:h-[520px] rounded-2xl bg-brand-charcoal/5 ring-1 ring-brand-aluminum/40 shadow-inner overflow-hidden">
              <div className="absolute inset-0 [mask-image:radial-gradient(circle_at_center,black,transparent_85%)] pointer-events-none" />
              <div className="absolute inset-0">
                <Spline scene={splineScene} className="!w-full !h-full" />
              </div>
            </div>
          )}
        </div>
      </div>
      {/* Subtle copper glow */}
      {has3D && (
        <div className="pointer-events-none absolute -top-32 -right-32 w-96 h-96 rounded-full bg-brand-copper/10 blur-3xl" />
      )}
    </div>
  );
}
