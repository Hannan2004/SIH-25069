import { cn } from '@/lib/utils'

const badgeVariants = {
  default: "bg-brand-emerald/10 text-brand-emerald border-brand-emerald/20",
  secondary: "bg-gray-100 text-gray-700 border-gray-200",
  success: "bg-green-100 text-green-700 border-green-200",
  warning: "bg-amber-100 text-amber-700 border-amber-200",
  error: "bg-red-100 text-red-700 border-red-200",
}

export default function Badge({ 
  variant = "default", 
  children, 
  className = "" 
}) {
  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
      badgeVariants[variant],
      className
    )}>
      {children}
    </span>
  )
}