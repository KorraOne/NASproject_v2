import { BRAND_NAME, BRAND_SHORT } from "../brand";

interface AuthBrandProps {
  title: string;
  subtitle: string;
}

export function AuthBrand({ title, subtitle }: AuthBrandProps) {
  return (
    <div className="auth-brand">
      <img className="auth-brand-logo" src="/logo.png" alt="" aria-hidden />
      <div>
        <strong className="auth-brand-name">{BRAND_NAME}</strong>
        <span className="auth-brand-tag">{title}</span>
        <p className="auth-brand-sub">{subtitle}</p>
      </div>
    </div>
  );
}

export { BRAND_NAME, BRAND_SHORT };
