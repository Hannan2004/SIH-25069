export default function Section({ 
  children, 
  className = "",
  background = "white",
  padding = "default"
}) {
  const backgroundVariants = {
    white: "bg-white",
    gray: "bg-gray-50",
    gradient: "gradient-bg"
  }

  const paddingVariants = {
    none: "",
    sm: "py-12",
    default: "py-16",
    lg: "py-24"
  }

  return (
    <section className={`${backgroundVariants[background]} ${paddingVariants[padding]} ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {children}
      </div>
    </section>
  )
}