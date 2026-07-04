import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Loading } from "./components/Loading";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { FoldersPage } from "./pages/FoldersPage";
import { LoginPage } from "./pages/LoginPage";
import { SetupPage } from "./pages/SetupPage";
import { SnapshotsPage } from "./pages/SnapshotsPage";
import { StoragePage } from "./pages/StoragePage";
import { UsersPage } from "./pages/UsersPage";

function AppRoutes() {
  const { state } = useAuth();

  if (state === "loading") {
    return (
      <div className="auth-page">
        <Loading label="Starting FrogsWork…" />
      </div>
    );
  }

  if (state === "needs-setup") {
    return (
      <Routes>
        <Route path="/setup" element={<SetupPage />} />
        <Route path="*" element={<Navigate to="/setup" replace />} />
      </Routes>
    );
  }

  if (state === "needs-login") {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/users" element={<UsersPage />} />
        <Route path="/folders" element={<FoldersPage />} />
        <Route path="/storage" element={<StoragePage />} />
        <Route path="/snapshots" element={<SnapshotsPage />} />
        <Route path="/" element={<Navigate to="/users" replace />} />
        <Route path="*" element={<Navigate to="/users" replace />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
