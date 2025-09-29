import { cn } from "@/lib/utils";

const buttonVariants = {
  // Rich copper gradient primary, subtle elevation
  default:
    "bg-gradient-to-b from-brand-copper to-[#915828] text-white shadow-md hover:from-[#C57A42] hover:to-[#9A6030] active:scale-[0.98] disabled:from-brand-copper/60 disabled:to-[#915828]/60",
  destructive:
    "bg-red-600 hover:bg-red-700 text-white shadow focus-visible:ring-red-500/40",
  outline:
    "border border-brand-copper/40 bg-white/70 backdrop-blur-sm text-brand-charcoal hover:bg-[#F7E6D9] hover:border-brand-copper/60",
  secondary: "bg-[#5E3A20] text-white hover:bg-[#4d301b] shadow-inner",
  ghost: "text-brand-copper hover:bg-brand-copper/10",
  link: "text-brand-copper underline-offset-4 hover:underline",
};

const buttonSizes = {
  default: "h-10 px-4 py-2",
  sm: "h-9 px-3 text-sm",
  lg: "h-12 px-8 text-lg",
  icon: "h-10 w-10",
};

export default function Button({
  className,
  variant = "default",
  size = "default",
  children,
  disabled,
  ...props
}) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-xl font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-brand-copper/50 disabled:opacity-50 disabled:cursor-not-allowed",
        buttonVariants[variant],
        buttonSizes[size],
        className
      )}
      disabled={disabled}
      aria-disabled={disabled || undefined}
      aria-busy={disabled || undefined}
      {...props}
    >
      {children}
    </button>
  );
}
