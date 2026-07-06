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
          Go to <Link to="/users/new">Add user</Link> and create a username and password for each person.
          They will use these to sign in to the helper app on their own PC.
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
      title: "Send staff the employee help link",
      body: (
        <p>
          Each person downloads and installs the Windows helper <strong>on their own computer</strong> — you do
          not install it for them. Share this link (no admin password required):
        </p>
      ),
      action: (
        <div className="inline-actions">
          <code className="help-url">{helpUrl}</code>
          <CopyButton text={helpUrl} label="Copy link" />
          <a className="btn btn-ghost" href="/help" target="_blank" rel="noreferrer">
            Preview employee page
          </a>
        </div>
      ),
    },
    {
      title: "Optional: test the helper yourself",
      body: (
        <p>
          If you also need files on the appliance, create a file user for yourself and download the helper from the{" "}
          <a href="/help" target="_blank" rel="noreferrer">
            employee help page
          </a>{" "}
          like your staff will.
        </p>
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
        lede="Onboard employees: you add users and permissions; staff download the helper themselves."
      />
      <section className="card featured-card section-card">
        <StepGuide steps={steps} />
      </section>
    </div>
  );
}
