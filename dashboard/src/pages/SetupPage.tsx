import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { completeSetup, getSetupStatus } from "../api/setup";
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

export function SetupPage() {
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [requiresClaim, setRequiresClaim] = useState(false);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(0);
  const [claimCode, setClaimCode] = useState("");
  const [email, setEmail] = useState("");
  const [backupEmail, setBackupEmail] = useState("");
  const [backupPhone, setBackupPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [timezone, setTimezone] = useState("Australia/Perth");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const steps = useMemo(
    () => (requiresClaim
      ? ["Welcome", "Setup code", "Account", "Finish"]
      : ["Welcome", "Password", "Finish"]),
    [requiresClaim],
  );

  useEffect(() => {
    getSetupStatus()
      .then((status) => setRequiresClaim(Boolean(status.requires_claim_code)))
      .catch(() => setRequiresClaim(false))
      .finally(() => setLoading(false));
  }, []);

  async function onFinish(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await completeSetup({
        password,
        timezone,
        claim_code: requiresClaim ? claimCode.trim() : undefined,
        email: requiresClaim ? email.trim() : email.trim() || undefined,
        backup_email: backupEmail.trim() || undefined,
        backup_phone: backupPhone.trim() || undefined,
      });
      await refresh();
      navigate("/", { replace: true });
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
    setStep((s) => s + 1);
  }

  function onClaimNext(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!claimCode.trim()) {
      setError("Enter the setup code from the card in your box.");
      return;
    }
    setStep((s) => s + 1);
  }

  function onAccountNext(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email.trim() || !email.includes("@")) {
      setError("Enter a valid email for your owner account.");
      return;
    }
    setStep((s) => s + 1);
  }

  if (loading) {
    return <div className="auth-page"><p className="muted">Loading…</p></div>;
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <AuthBrand
          title={requiresClaim ? "Claim your FrogsWork box" : "First-time setup"}
          subtitle="A few quick steps to get your file storage ready."
        />

        <div className="wizard-progress" aria-label={`Step ${step + 1} of ${steps.length}`}>
          {steps.map((label, index) => (
            <div
              key={label}
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

        {requiresClaim && step === 1 && (
          <form onSubmit={onClaimNext} className="stack-form">
            <h2>Enter your setup code</h2>
            <p className="lede">Find this on the card inside your box — not on the label on the unit.</p>
            <label>
              Setup code
              <input
                value={claimCode}
                onChange={(e) => setClaimCode(e.target.value.toUpperCase())}
                placeholder="FW-XXXX-XXXX"
                required
                autoComplete="off"
              />
            </label>
            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setStep(0)}>Back</button>
              <button type="submit" className="btn btn-primary">Continue</button>
            </div>
          </form>
        )}

        {requiresClaim && step === 2 && (
          <form onSubmit={onAccountNext} className="stack-form">
            <h2>Your owner account</h2>
            <p className="lede">Use this email to sign in to the dashboard later.</p>
            <label>
              Email
              <input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label>
              Dashboard password
              <input type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
            </label>
            <label>
              Confirm password
              <input type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} />
            </label>
            <label>
              Backup email <span className="hint">(optional)</span>
              <input type="email" value={backupEmail} onChange={(e) => setBackupEmail(e.target.value)} />
            </label>
            <label>
              Backup phone <span className="hint">(optional)</span>
              <input type="tel" value={backupPhone} onChange={(e) => setBackupPhone(e.target.value)} />
            </label>
            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setStep(1)}>Back</button>
              <button type="submit" className="btn btn-primary">Continue</button>
            </div>
          </form>
        )}

        {!requiresClaim && step === 1 && (
          <form onSubmit={onPasswordNext} className="stack-form">
            <h2>Choose your password</h2>
            <p className="lede">You&apos;ll use this to sign in to the management dashboard.</p>
            <label>
              Dashboard password
              <input type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
            </label>
            <label>
              Confirm password
              <input type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} />
            </label>
            <label>
              Email <span className="hint">(optional)</span>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setStep(0)}>Back</button>
              <button type="submit" className="btn btn-primary">Continue</button>
            </div>
          </form>
        )}

        {step === steps.length - 1 && (
          <form onSubmit={onFinish} className="stack-form">
            <h2>Almost done</h2>
            <p className="lede">Pick your timezone so backups run at the right local time.</p>
            <label>
              Timezone
              <select value={timezone} onChange={(e) => setTimezone(e.target.value)}>
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>{tz.replace("_", " ")}</option>
                ))}
              </select>
            </label>
            <div className="wizard-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setStep(step - 1)}>Back</button>
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
