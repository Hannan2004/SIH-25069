import { cn } from "@/lib/utils";

const buttonVariants = {
  default: "bg-brand-emerald hover:bg-brand-forest text-white",
  destructive: "bg-red-500 hover:bg-red-600 text-white",
  outline: "border border-gray-300 bg-white hover:bg-gray-50 text-gray-700",
  secondary: "bg-gray-100 hover:bg-gray-200 text-gray-900",
  ghost: "hover:bg-gray-100 text-gray-700",
  link: "text-brand-emerald underline-offset-4 hover:underline",
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
        "inline-flex items-center justify-center rounded-xl font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-emerald focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
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
