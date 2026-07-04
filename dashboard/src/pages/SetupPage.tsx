import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { completeSetup } from "../api/setup";
import { ApiRequestError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { ErrorBanner } from "../components/ErrorBanner";

const TIMEZONES = [
  "Australia/Perth",
  "Australia/Sydney",
  "Australia/Melbourne",
  "Australia/Brisbane",
  "Australia/Adelaide",
  "Pacific/Auckland",
  "UTC",
];

export function SetupPage() {
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [timezone, setTimezone] = useState("Australia/Perth");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await completeSetup(password, timezone);
      await refresh();
      navigate("/login", { replace: true });
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Setup failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Welcome to FrogsWork</h1>
        <p className="lede">
          Set a dashboard password for managing users, folders, and storage on this appliance.
        </p>
        <ErrorBanner message={error} />
        <form onSubmit={onSubmit} className="stack-form">
          <label>
            Dashboard password
            <input
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </label>
          <label>
            Confirm password
            <input
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              minLength={8}
            />
          </label>
          <label>
            Timezone
            <select value={timezone} onChange={(e) => setTimezone(e.target.value)}>
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Setting up…" : "Complete setup"}
          </button>
        </form>
      </div>
    </div>
  );
}
