import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

const MORE_ROUTES = [
  "/permissions",
  "/storage",
  "/snapshots",
  "/guide",
  "/system",
] as const;

const GROUPS = [
  {
    label: "Access",
    items: [
      { to: "/permissions", label: "Permissions" },
      { to: "/users/archetypes", label: "Archetypes" },
    ],
  },
  {
    label: "Data",
    items: [
      { to: "/storage", label: "Storage" },
      { to: "/snapshots", label: "Backups" },
    ],
  },
  {
    label: "Help",
    items: [
      { to: "/guide", label: "User Guide" },
      { to: "/help", label: "Employee help", external: true },
    ],
  },
  {
    label: "Appliance",
    items: [{ to: "/system", label: "System" }],
  },
] as const;

function isMoreRoute(pathname: string): boolean {
  return MORE_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

export function NavMoreMenu() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const moreActive = isMoreRoute(location.pathname);

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="nav-more" ref={rootRef}>
      <button
        type="button"
        className={`nav-more-trigger${moreActive ? " active" : ""}`}
        aria-expanded={open}
        aria-haspopup="true"
        onClick={() => setOpen((value) => !value)}
      >
        More
      </button>
      {open ? (
        <div className="nav-more-panel" role="menu">
          {GROUPS.map((group) => (
            <div key={group.label} className="nav-more-group">
              <div className="nav-more-group-label">{group.label}</div>
              {group.items.map((item) =>
                "external" in item && item.external ? (
                  <a
                    key={item.to}
                    className="nav-more-link"
                    href={item.to}
                    target="_blank"
                    rel="noreferrer"
                    role="menuitem"
                  >
                    {item.label}
                  </a>
                ) : (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`nav-more-link${location.pathname === item.to ? " active" : ""}`}
                    role="menuitem"
                    onClick={() => setOpen(false)}
                  >
                    {item.label}
                  </Link>
                ),
              )}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
