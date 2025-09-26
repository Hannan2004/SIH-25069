import { cn } from '@/lib/utils'

export default function Card({ 
  className, 
  children, 
  hover = true,
  padding = "default",
  ...props 
}) {
  const paddingVariants = {
    none: "",
    sm: "p-4",
    default: "p-6",
    lg: "p-8",
  }

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-gray-200 card-shadow",
        hover && "hover:card-shadow-hover transition-all duration-200",
        paddingVariants[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}