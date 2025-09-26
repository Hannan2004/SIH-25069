export default function FeatureIcon({ 
  icon: Icon, 
  color = "brand-emerald",
  size = "default",
  className = ""
}) {
  const sizeVariants = {
    sm: "w-8 h-8 p-1.5",
    default: "w-12 h-12 p-3",
    lg: "w-16 h-16 p-4"
  }

  const colorVariants = {
    "brand-emerald": "bg-brand-emerald/10 text-brand-emerald",
    "brand-copper": "bg-brand-copper/10 text-brand-copper",
    "brand-steel": "bg-brand-steel/10 text-brand-steel",
    "brand-aluminum": "bg-brand-aluminum/20 text-brand-steel",
    "accent-sun": "bg-accent-sun/10 text-amber-700"
  }

  return (
    <div className={`
      ${sizeVariants[size]} 
      ${colorVariants[color]}
      rounded-xl flex items-center justify-center
      ${className}
    `}>
      <Icon />
    </div>
  )
}