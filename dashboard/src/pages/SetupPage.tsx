import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { completeSetup } from "../api/setup";
import { ApiRequestError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { AuthBrand } from "../components/AuthBrand";
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

const STEPS = ["Welcome", "Password", "Finish"] as const;

export function SetupPage() {
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [timezone, setTimezone] = useState("Australia/Perth");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onFinish(e: FormEvent) {
    e.preventDefault();
    setError(null);
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

  function onPasswordNext(e: FormEvent) {
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
    setStep(2);
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <AuthBrand
          title="First-time setup"
          subtitle="A few quick steps to get your file storage ready."
        />

        <div className="wizard-progress" aria-label={`Step ${step + 1} of ${STEPS.length}`}>
          {STEPS.map((_, index) => (
            <div
              key={STEPS[index]}
              className={`wizard-progress-step${index <= step ? " is-active" : ""}${index < step ? " is-done" : ""}`}
            />
          ))}
        </div>

        <ErrorBanner message={error} />

        {step === 0 && (
          <div>
            <h2>Welcome to FrogsWork</h2>
            <p className="lede">This little box will store your team&apos;s files safely on your network.</p>
            <ul className="welcome-list">
              <li>Store private files for each person</li>
              <li>Share folders like Projects or Invoices</li>
              <li>Automatic nightly backups you can restore</li>
            </ul>
            <div className="wizard-actions">
              <span />
              <button type="button" className="btn btn-primary" onClick={() => setStep(1)}>
                Continue
              </button>
            </div>
          </div>
        )}

        {step === 1 && (
          <form onSubmit={onPasswordNext} className="stack-form">
            <h2>Choose your password</h2>
            <p className="lede">You&apos;ll use this to sign in to the management dashboard. Keep it somewhere safe.</p>
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
              <span className="hint">At least 8 characters</span>
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
            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setStep(0)}>
                Back
              </button>
              <button type="submit" className="btn btn-primary">
                Continue
              </button>
            </div>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={onFinish} className="stack-form">
            <h2>Almost done</h2>
            <p className="lede">Pick your timezone so backups and schedules run at the right local time.</p>
            <label>
              Timezone
              <select value={timezone} onChange={(e) => setTimezone(e.target.value)}>
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz.replace("_", " ")}
                  </option>
                ))}
              </select>
            </label>
            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setStep(1)}>
                Back
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                {busy ? "Setting up…" : "Complete setup"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
