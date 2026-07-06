import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiRequestError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { AuthBrand } from "../components/AuthBrand";
import { ErrorBanner } from "../components/ErrorBanner";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(password, email.trim() || undefined);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <AuthBrand
          title="Sign in"
          subtitle="Use the owner account you created during setup."
        />
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit} className="stack-form">
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Leave blank if you did not use email"
            />
            <span className="hint">Required if you set up with an email address</span>
          </label>
          <label>
            Dashboard password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
