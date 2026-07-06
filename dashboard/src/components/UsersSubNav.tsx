import { NavLink } from "react-router-dom";

export function UsersSubNav() {
  return (
    <nav className="sub-nav" aria-label="Users sections">
      <NavLink
        to="/users"
        end
        className={({ isActive }) => (isActive ? "active" : undefined)}
      >
        People
      </NavLink>
      <NavLink
        to="/users/archetypes"
        className={({ isActive }) => (isActive ? "active" : undefined)}
      >
        Archetypes
      </NavLink>
    </nav>
  );
}
