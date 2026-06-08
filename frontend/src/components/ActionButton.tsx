import type { ReactNode } from "react";
import { cn } from "../lib/utils";

type ActionButtonProps = {
  children: ReactNode;
  icon: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "quiet";
  title?: string;
};

export function ActionButton({ children, icon, onClick, disabled, variant = "secondary", title }: ActionButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2",
        disabled && "cursor-not-allowed opacity-50",
        variant === "primary" && "border-emerald-600 bg-emerald-600 text-white hover:bg-emerald-700",
        variant === "secondary" && "border-slate-300 bg-white text-slate-900 shadow-sm hover:border-emerald-200 hover:bg-emerald-50",
        variant === "quiet" && "border-transparent bg-slate-100 text-slate-700 hover:bg-emerald-50 hover:text-emerald-800"
      )}
      disabled={disabled}
      onClick={onClick}
      title={title}
      type="button"
    >
      <span className="size-4 shrink-0">{icon}</span>
      <span className="truncate">{children}</span>
    </button>
  );
}
