import { cn } from "@/lib/utils";

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
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-brand-copper/25 bg-white/80 backdrop-blur-sm shadow-sm",
        hover &&
          "hover:shadow-md hover:border-brand-copper/40 transition-all duration-200",
        paddingVariants[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
