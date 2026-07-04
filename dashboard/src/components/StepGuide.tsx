import type { ReactNode } from "react";

export interface StepItem {
  title: string;
  body: ReactNode;
  action?: ReactNode;
}

interface StepGuideProps {
  steps: StepItem[];
}

export function StepGuide({ steps }: StepGuideProps) {
  return (
    <ol className="step-guide">
      {steps.map((step, index) => (
        <li key={step.title} className="step-guide-item">
          <div className="step-guide-marker" aria-hidden>
            {index + 1}
          </div>
          <div className="step-guide-content">
            <h3 className="step-guide-title">{step.title}</h3>
            <div className="step-guide-body">{step.body}</div>
            {step.action ? <div className="step-guide-action">{step.action}</div> : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
