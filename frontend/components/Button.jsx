import { cn } from "@/lib/utils";

const buttonVariants = {
  default:
    "bg-brand-copper hover:bg-brand-aluminum text-white shadow-sm hover:shadow transition-colors", // Primary
  destructive: "bg-red-600 hover:bg-red-700 text-white",
  outline:
    "border border-brand-steel/50 bg-white hover:bg-brand-aluminum/30 text-brand-charcoal",
  secondary:
    "bg-brand-green hover:bg-brand-steel text-white focus-visible:ring-brand-green/40",
  ghost:
    "hover:bg-brand-aluminum/30 text-brand-blue focus-visible:ring-brand-blue/30",
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
        "inline-flex items-center justify-center rounded-xl font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-brand-blue disabled:opacity-50 disabled:cursor-not-allowed",
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
