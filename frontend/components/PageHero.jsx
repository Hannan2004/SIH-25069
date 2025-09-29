import Spline from "@splinetool/react-spline/next";

export default function PageHero({
  title,
  description,
  children,
  className = "",
  splineScene,
  dense = false, // deprecated in favor of spacing variants
  splineScale = 0.5, // 0 < scale <=1
  spacing = "standard", // home | standard | compact | tight
}) {
  const has3D = Boolean(splineScene);

  // Backward compatibility: if dense provided explicitly, override spacing unless spacing explicitly set
  const resolvedSpacing = dense ? "compact" : spacing;

  const paddingMap = {
    home: "py-16 md:py-48", // large hero (landing)
    standard: "py-16 md:py-28", // default content hero
    compact: "py-10 md:py-16", // lighter for auth & secondary pages
    tight: "py-8 md:py-12", // very small header banners
  };
  const padding = paddingMap[resolvedSpacing] || paddingMap.standard;

  return (
    <div
      className={`relative ${padding} ${className}`}
      style={{ backgroundColor: "#FFF0E3" }}
    >
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div
          className={`flex flex-col ${
            has3D ? "lg:flex-row" : ""
          } gap-12 items-stretch`}
        >
          {/* Left Content */}
          <div className="flex-1 max-w-xl lg:pr-4 xl:pr-8 self-center">
            <h1 className="text-gradient mb-8 leading-tight">{title}</h1>
            {description && (
              <p className="text-lg md:text-xl text-brand-charcoal/80 leading-relaxed mb-10">
                {description}
              </p>
            )}
            {children && <div className="flex flex-wrap gap-4">{children}</div>}
          </div>
          {/* Right Spline Container */}
          {has3D && (
            <div className="flex-1 relative flex items-center justify-center mt-[-18%]">
              <div className="relative w-full max-w-xl">
                {/* Outer box provides layout space */}
                <div className="relative w-full">
                  {/* 4:3 ratio placeholder */}
                  {/* Scaled content layer */}
                  <div
                    className="absolute inset-0 flex items-center justify-center overflow-visible"
                    style={{
                      transform: `scale(${splineScale})`,
                      transformOrigin: "center center",
                    }}
                  >
                    {/* Large virtual canvas to ensure full model loads without cropping */}
                    <div className="w-[1600px] h-[1200px] pointer-events-auto relative">
                      <Spline scene={splineScene} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
