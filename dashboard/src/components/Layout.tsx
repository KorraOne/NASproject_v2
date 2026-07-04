import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout() {
  const { logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden>
            🐸
          </span>
          <div>
            <strong>FrogsWork</strong>
            <span className="brand-sub">File Storage</span>
          </div>
        </div>
        <nav className="app-nav" aria-label="Main">
          <NavLink to="/users" className={({ isActive }) => (isActive ? "active" : undefined)}>
            Users
          </NavLink>
          <NavLink to="/folders" className={({ isActive }) => (isActive ? "active" : undefined)}>
            Folders
          </NavLink>
          <NavLink to="/storage" className={({ isActive }) => (isActive ? "active" : undefined)}>
            Storage
          </NavLink>
          <NavLink to="/snapshots" className={({ isActive }) => (isActive ? "active" : undefined)}>
            Snapshots
          </NavLink>
          <NavLink to="/system" className={({ isActive }) => (isActive ? "active" : undefined)}>
            System
          </NavLink>
        </nav>
        <button type="button" className="btn btn-ghost" onClick={() => logout()}>
          Sign out
        </button>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
