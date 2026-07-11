import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost" | "danger";
};

export function Button({ className, variant = "default", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex h-9 items-center justify-center gap-2 rounded-md px-3 text-sm font-medium transition-colors disabled:opacity-50",
        variant === "default" && "bg-accent text-slate-950 hover:bg-teal-300",
        variant === "ghost" && "border border-border bg-transparent text-slate-200 hover:bg-white/5",
        variant === "danger" && "bg-danger text-white hover:bg-red-400",
        className,
      )}
      {...props}
    />
  );
}
