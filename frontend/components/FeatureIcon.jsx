export default function FeatureIcon({
  icon: Icon,
  color = "copper", // updated default to copper palette
  size = "default",
  variant = "soft", // soft | solid | outline
  className = "",
}) {
  const sizeVariants = {
    sm: "w-8 h-8 p-1.5",
    default: "w-12 h-12 p-3",
    lg: "w-16 h-16 p-4",
  };
  // Base tonal colors referencing updated tailwind palette
  const base = {
    copper: {
      fg: "text-brand-copper",
      soft: "bg-brand-copper/15",
      solid: "bg-brand-copper text-white",
      outline: "ring-1 ring-brand-copper/50 bg-transparent",
    },
    gold: {
      fg: "text-brand-gold",
      soft: "bg-brand-gold/15",
      solid: "bg-brand-gold text-white",
      outline: "ring-1 ring-brand-gold/50 bg-transparent",
    },
    steel: {
      fg: "text-brand-steel",
      soft: "bg-brand-steel/15",
      solid: "bg-brand-steel text-white",
      outline: "ring-1 ring-brand-steel/40 bg-transparent",
    },
    aluminum: {
      fg: "text-brand-steel",
      soft: "bg-brand-aluminum/40",
      solid: "bg-brand-aluminum text-brand-charcoal",
      outline: "ring-1 ring-brand-aluminum/50 bg-transparent",
    },
    charcoal: {
      fg: "text-brand-charcoal",
      soft: "bg-brand-charcoal/10",
      solid: "bg-brand-charcoal text-white",
      outline: "ring-1 ring-brand-charcoal/40 bg-transparent",
    },
  };

  const palette = base[color] || base.copper;
  const toneClass =
    variant === "solid"
      ? palette.solid
      : variant === "outline"
      ? palette.outline + " " + palette.fg
      : palette.soft + " " + palette.fg; // soft default

  return (
    <div
      className={`
      ${sizeVariants[size]} 
      ${toneClass}
      rounded-xl flex items-center justify-center shadow-sm
      ${className}
    `}
    >
      <Icon />
    </div>
  );
}
