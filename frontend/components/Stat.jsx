export default function Stat({
  label,
  value,
  note,
  unit = "",
  trend,
  variant = "card", // 'card' | 'plain'
  className = "",
}) {
  if (variant === "plain") {
    return (
      <div className={`text-center ${className}`}>
        <div className="flex items-baseline justify-center space-x-1">
          <span className="text-3xl md:text-4xl font-bold text-brand-charcoal">
            {value}
          </span>
          {unit && (
            <span className="text-lg text-brand-charcoal/60">{unit}</span>
          )}
        </div>
        <p className="text-sm text-brand-charcoal/70 mt-1">{label}</p>
        {trend != null && (
          <p
            className={`text-xs mt-1 ${
              trend > 0 ? "text-red-500" : "text-green-500"
            }`}
          >
            {trend > 0 ? "↑" : "↓"} {Math.abs(trend)}% vs conventional
          </p>
        )}
        {note && (
          <p className="text-[11px] mt-2 text-brand-charcoal/60">{note}</p>
        )}
      </div>
    );
  }

  // default card variant
  return (
    <div
      className={`p-4 rounded-xl bg-white/80 backdrop-blur-sm border border-brand-copper/30 shadow-sm flex flex-col ${className}`}
    >
      <p className="text-[11px] uppercase tracking-wide text-brand-charcoal/60 mb-1 font-medium">
        {label}
      </p>
      <p className="text-2xl font-semibold text-brand-copper">
        {value}
        {unit && (
          <span className="text-sm font-normal text-brand-charcoal/60 ml-1">
            {unit}
          </span>
        )}
      </p>
      {trend != null && (
        <p
          className={`text-[11px] mt-1 ${
            trend > 0 ? "text-red-500" : "text-green-500"
          }`}
        >
          {trend > 0 ? "↑" : "↓"} {Math.abs(trend)}% vs conventional
        </p>
      )}
      {note && (
        <p className="text-[11px] mt-1 text-brand-charcoal/60">{note}</p>
      )}
    </div>
  );
}
