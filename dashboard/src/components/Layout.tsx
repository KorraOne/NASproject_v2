import { NavLink, Outlet, useLocation } from "react-router-dom";
import { BRAND_NAME } from "../brand";
import { useAuth } from "../context/AuthContext";
import { NavMoreMenu } from "./NavMoreMenu";

function usersNavActive(pathname: string): boolean {
  return pathname === "/users" || pathname.startsWith("/users/");
}

export function Layout() {
  const { logout } = useAuth();
  const location = useLocation();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <img className="brand-logo" src="/logo.png" alt="" aria-hidden />
          <div>
            <strong>{BRAND_NAME}</strong>
          </div>
        </div>
        <nav className="app-nav" aria-label="Main">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : undefined)}>
            Dashboard
          </NavLink>
          <NavLink
            to="/users"
            className={() => (usersNavActive(location.pathname) ? "active" : undefined)}
          >
            Users
          </NavLink>
          <NavLink to="/folders" className={({ isActive }) => (isActive ? "active" : undefined)}>
            Folders
          </NavLink>
          <NavMoreMenu />
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
