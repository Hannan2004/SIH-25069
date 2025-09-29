import { cn } from "@/lib/utils";

const badgeVariants = {
  default: "bg-brand-copper/10 text-brand-copper border-brand-copper/30",
  secondary: "bg-[#F3E3D7] text-[#5E3A20] border-[#E4CCBA]",
  success: "bg-green-100 text-green-700 border-green-200",
  warning: "bg-amber-100 text-amber-700 border-amber-200",
  error: "bg-red-100 text-red-700 border-red-200",
  outline: "bg-transparent text-brand-copper border-brand-copper/40",
};

export default function Badge({
  variant = "default",
  children,
  className = "",
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border tracking-wide",
        badgeVariants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
