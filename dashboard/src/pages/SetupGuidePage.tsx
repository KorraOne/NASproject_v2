import { Link } from "react-router-dom";
import { CopyButton } from "../components/CopyButton";
import { GuideCard } from "../components/GuideCard";
import { PageIntro } from "../components/PageIntro";
import { StepGuide } from "../components/StepGuide";

export function SetupGuidePage() {
  const helpUrl = `${window.location.origin}/help`;

  const steps = [
    {
      title: "Add a file user",
      body: (
        <p>
          Go to <Link to="/users/new">Add user</Link> and create a username and password. Each person gets a
          private folder at <strong>W:\Personal\their-username</strong>.
        </p>
      ),
    },
    {
      title: "Grant shared folder access",
      body: (
        <p>
          Open <Link to="/users/archetypes">Archetypes</Link> or{" "}
          <Link to="/permissions">Permissions</Link> and set <strong>Read only</strong> or{" "}
          <strong>Read & write</strong> for each team folder.
        </p>
      ),
    },
    {
      title: "Download the Windows helper",
      body: (
        <p>
          Install the helper on each employee PC. It maps the <strong>W:</strong> drive automatically after
          sign-in.
        </p>
      ),
      action: (
        <a className="btn btn-primary" href="/api/helper/download">
          Download FrogsWork Helper
        </a>
      ),
    },
    {
      title: "Share the employee guide",
      body: (
        <p>
          Send your team this link — no admin login required. They can download the helper and follow the
          steps on their Windows PC.
        </p>
      ),
      action: (
        <div className="inline-actions">
          <code className="help-url">{helpUrl}</code>
          <CopyButton text={helpUrl} label="Copy link" />
          <a className="btn btn-ghost" href="/help" target="_blank" rel="noreferrer">
            Preview guide
          </a>
        </div>
      ),
    },
    {
      title: "Optional: set default personal folder size",
      body: (
        <p>
          On <Link to="/system">System</Link>, set a default maximum size for new personal folders.
        </p>
      ),
    },
    {
      title: "After upgrades",
      body: (
        <GuideCard variant="tip" title="One network address">
          Tell employees to use either the IP address or <strong>frogswork.local</strong> — not both. If they
          see two FrogsWork entries in Network, pick one and disconnect old drive mappings (U:, S:, etc.).
        </GuideCard>
      ),
    },
  ];

  return (
    <div className="page">
      <PageIntro
        title="User guide"
        lede="Step-by-step checklist for onboarding employees to FrogsWork File Storage."
      />
      <section className="card featured-card section-card">
        <StepGuide steps={steps} />
      </section>
    </div>
  );
}
