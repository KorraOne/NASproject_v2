import { useEffect, useState } from "react";
import { getPublicInfo, type PublicInfo } from "../api/public";
import { AuthBrand } from "../components/AuthBrand";
import { CopyButton } from "../components/CopyButton";
import { GuideCard } from "../components/GuideCard";
import { Loading } from "../components/Loading";
import { StepGuide } from "../components/StepGuide";

export function HelpPage() {
  const [info, setInfo] = useState<PublicInfo | null>(null);

  useEffect(() => {
    getPublicInfo()
      .then(setInfo)
      .catch(() => setInfo(null));
  }, []);

  const address = info?.primary_ip ?? "frogswork.local";
  const connectAddress = info?.primary_ip ?? "frogswork.local";

  const steps = [
    {
      title: "Download FrogsWork Helper",
      body: <p>Install the helper app on your Windows PC. Your manager created your username and password.</p>,
      action: (
        <a className="btn btn-primary btn-large" href="/api/helper/download">
          Download FrogsWork Helper
        </a>
      ),
    },
    {
      title: "Install and open",
      body: (
        <>
          <p>Run <strong>FrogsWork.Helper.exe</strong>. If Windows SmartScreen warns you, click More info, then Run anyway.</p>
          <GuideCard variant="tip" title="SmartScreen">
            The helper is not code-signed yet. Choose Run anyway when prompted.
          </GuideCard>
        </>
      ),
    },
    {
      title: "Sign in",
      body: (
        <p>
          Use address <strong>{connectAddress}</strong>, your username, and the password from your manager. Prefer
          the IP number if the name does not work.
        </p>
      ),
    },
    {
      title: "Find your files",
      body: (
        <p>
          Open drive <strong>W:</strong> in File Explorer. Your private files are in{" "}
          <strong>Personal → your username</strong>. Team folders appear if your manager granted access. Press F5
          to refresh if something new does not show.
        </p>
      ),
    },
    {
      title: "Network tip",
      body: (
        <GuideCard variant="info" title="One FrogsWork box">
          You may see more than one FrogsWork entry under Network. Use the address your manager gave you — do not
          map the same drive twice.
        </GuideCard>
      ),
    },
  ];

  return (
    <div className="auth-page help-page">
      <div className="help-page-inner">
        <AuthBrand title="Connect your PC" subtitle="Employee guide" />
        {info === null && !address ? (
          <Loading label="Loading…" />
        ) : (
          <>
            <div className="card help-info-card">
              <p>
                FrogsWork address: <strong>{address}</strong>
                {info?.primary_ip ? <CopyButton text={info.primary_ip} label="Copy IP" /> : null}
              </p>
            </div>
            <section className="card section-card">
              <StepGuide steps={steps} />
            </section>
          </>
        )}
      </div>
    </div>
  );
}
