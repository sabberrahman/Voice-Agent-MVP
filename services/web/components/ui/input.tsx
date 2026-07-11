import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-border bg-slate-950 px-3 text-sm text-slate-100 outline-none placeholder:text-muted focus:border-accent",
        className,
      )}
      {...props}
    />
  );
}
