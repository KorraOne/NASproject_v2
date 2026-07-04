import type { ReactNode } from "react";

interface PageIntroProps {
  title: string;
  lede?: string;
  badge?: string;
  action?: ReactNode;
}

export function PageIntro({ title, lede, badge, action }: PageIntroProps) {
  return (
    <header className="page-header">
      <div className="page-intro">
        {badge ? <span className="page-badge">{badge}</span> : null}
        <h1>{title}</h1>
        {lede ? <p className="lede">{lede}</p> : null}
      </div>
      {action}
    </header>
  );
}
