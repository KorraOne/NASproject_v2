import { Link } from "react-router-dom";

const DISMISS_KEY = "frogswork-getting-started-dismissed";

export function GettingStartedBanner() {
  if (localStorage.getItem(DISMISS_KEY) === "1") {
    return null;
  }

  function dismiss() {
    localStorage.setItem(DISMISS_KEY, "1");
    window.location.reload();
  }

  return (
    <div className="getting-started-banner">
      <div>
        <strong>Getting started</strong>
        <p>
          Add your first team member on <Link to="/users">Users</Link>, then share the{" "}
          <Link to="/guide">setup guide</Link> and <a href="/api/helper/download">Windows helper</a>.
        </p>
      </div>
      <button type="button" className="btn btn-ghost btn-small" onClick={dismiss}>
        Dismiss
      </button>
    </div>
  );
}

export function dismissGettingStarted() {
  localStorage.setItem(DISMISS_KEY, "1");
}
