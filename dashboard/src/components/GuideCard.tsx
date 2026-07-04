import type { ReactNode } from "react";

type GuideVariant = "info" | "tip" | "warning";

interface GuideCardProps {
  variant?: GuideVariant;
  title?: string;
  children: ReactNode;
}

export function GuideCard({ variant = "info", title, children }: GuideCardProps) {
  return (
    <div className={`guide-card guide-card--${variant}`}>
      {title ? <strong className="guide-card-title">{title}</strong> : null}
      <div className="guide-card-body">{children}</div>
    </div>
  );
}
