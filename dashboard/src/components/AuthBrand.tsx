interface AuthBrandProps {
  title: string;
  subtitle: string;
}

export function AuthBrand({ title, subtitle }: AuthBrandProps) {
  return (
    <div className="auth-brand">
      <span className="auth-brand-mark" aria-hidden>
        🐸
      </span>
      <div>
        <strong className="auth-brand-name">FrogsWork</strong>
        <span className="auth-brand-tag">{title}</span>
        <p className="auth-brand-sub">{subtitle}</p>
      </div>
    </div>
  );
}
