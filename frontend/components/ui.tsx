import { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

// Flexible Button: variants + sizes, fullWidth, loading
type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";
const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-moss text-white hover:bg-moss-dark border border-moss",
  secondary: "bg-white text-ink border border-[#d8ded8] hover:bg-[#f5f7f4]",
  ghost: "bg-transparent text-[#65716a] hover:bg-[#f5f7f4] hover:text-ink border border-transparent",
  danger: "bg-red-600 text-white hover:bg-red-700 border border-red-600",
};
const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2.5 text-sm",
  lg: "px-6 py-3 text-base",
};
export function Button({
  variant = "primary",
  size = "md",
  fullWidth = false,
  loading = false,
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize; fullWidth?: boolean; loading?: boolean }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-moss/20 ${variantClasses[variant]} ${sizeClasses[size]} ${fullWidth ? "w-full" : ""} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" aria-hidden />}
      {children}
    </button>
  );
}

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`w-full rounded-lg border border-[#d8ded8] bg-white px-3 py-2.5 text-sm text-ink outline-none placeholder:text-[#7b8780] focus:border-moss focus:ring-2 focus:ring-moss/15 disabled:bg-[#fafbf9] ${className}`} {...props} />;
}

export function Select({ className = "", children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={`w-full rounded-lg border border-[#d8ded8] bg-white px-3 py-2.5 text-sm text-ink outline-none focus:border-moss focus:ring-2 focus:ring-moss/15 ${className}`} {...props}>{children}</select>;
}

export function Textarea({ className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`w-full rounded-lg border border-[#d8ded8] bg-white px-3 py-2.5 text-sm text-ink outline-none placeholder:text-[#7b8780] focus:border-moss focus:ring-2 focus:ring-moss/15 ${className}`} {...props} />;
}

export function Label({ children, className = "", ...props }: { children: ReactNode; className?: string } & React.HTMLAttributes<HTMLLabelElement>) {
  return <label className={`block text-sm font-medium text-ink ${className}`} {...props}>{children}</label>;
}

export function Card({ children, className = "", hover = false }: { children: ReactNode; className?: string; hover?: boolean }) {
  return <section className={`rounded-2xl border border-[#e5e8e3] bg-white shadow-panel ${hover ? "transition hover:shadow-large hover:-translate-y-0.5" : ""} ${className}`}>{children}</section>;
}
export function CardHeader({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`flex items-center justify-between border-b border-[#edf0eb] p-5 ${className}`}>{children}</div>;
}
export function CardBody({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`p-5 ${className}`}>{children}</div>;
}

export function Badge({ value, variant = "default" }: { value: string; variant?: "default" | "success" | "warning" | "info" | "neutral" }) {
  const map: Record<string, string> = {
    default: "bg-stone-100 text-stone-700",
    success: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    warning: "bg-amber-50 text-amber-800 border border-amber-200",
    info: "bg-blue-50 text-blue-700 border border-blue-200",
    neutral: "bg-[#f5f7f4] text-[#65716a] border border-[#e5e8e3]",
  };
  // Auto variant by well-known statuses
  let auto: string = map[variant];
  if (variant === "default") {
    if (value === "ACTIVE") auto = map.success;
    else if (value === "COMPLETED" || value === "APPROVED") auto = map.info;
    else if (value === "ON_HOLD" || value === "PENDING_APPROVAL") auto = map.warning;
  }
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${auto}`}>{value.replace(/_/g, " ")}</span>;
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-lg ${className}`} aria-hidden />;
}

export function Alert({ children, variant = "info", className = "" }: { children: ReactNode; variant?: "info" | "error" | "success" | "warning"; className?: string }) {
  const styles: Record<string, string> = {
    info: "bg-blue-50 text-blue-800 border-blue-200",
    error: "bg-red-50 text-red-700 border-red-200",
    success: "bg-emerald-50 text-emerald-800 border-emerald-200",
    warning: "bg-amber-50 text-amber-800 border-amber-200",
  };
  return <div className={`rounded-lg border p-3 text-sm ${styles[variant]} ${className}`}>{children}</div>;
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="mb-3 grid h-12 w-12 place-items-center rounded-full bg-[#f5f7f4] text-[#8a948e]">—</div>
      <h3 className="font-semibold text-ink">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-[#65716a]">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <p className="text-sm font-semibold text-moss">{eyebrow}</p>}
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-ink">{title}</h1>
        {description && <p className="mt-2 text-sm text-[#65716a] sm:text-base">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
