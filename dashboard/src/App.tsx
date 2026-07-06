import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ToastProvider } from "./components/Toast";
import { Loading } from "./components/Loading";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ArchetypeFormPage } from "./pages/ArchetypeFormPage";
import { ArchetypesPage } from "./pages/ArchetypesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FolderFormPage } from "./pages/FolderFormPage";
import { FoldersPage } from "./pages/FoldersPage";
import { HelpPage } from "./pages/HelpPage";
import { LoginPage } from "./pages/LoginPage";
import { PermissionsPage } from "./pages/PermissionsPage";
import { SetupGuidePage } from "./pages/SetupGuidePage";
import { SetupPage } from "./pages/SetupPage";
import { SnapshotsPage } from "./pages/SnapshotsPage";
import { StoragePage } from "./pages/StoragePage";
import { SystemPage } from "./pages/SystemPage";
import { TemporaryAccessPage } from "./pages/TemporaryAccessPage";
import { UserFormPage } from "./pages/UserFormPage";
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
        <Route path="/help" element={<HelpPage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="*" element={<Navigate to="/setup" replace />} />
      </Routes>
    );
  }

  if (state === "needs-login") {
    return (
      <Routes>
        <Route path="/help" element={<HelpPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/help" element={<HelpPage />} />
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/users/new" element={<UserFormPage />} />
        <Route path="/users/archetypes" element={<ArchetypesPage />} />
        <Route path="/users/archetypes/new" element={<ArchetypeFormPage />} />
        <Route path="/users/archetypes/:id/edit" element={<ArchetypeFormPage />} />
        <Route path="/users/:id/temporary-access" element={<TemporaryAccessPage />} />
        <Route path="/users/:id/edit" element={<UserFormPage />} />
        <Route path="/folders" element={<FoldersPage />} />
        <Route path="/folders/new" element={<FolderFormPage />} />
        <Route path="/folders/:id/edit" element={<FolderFormPage />} />
        <Route path="/permissions" element={<PermissionsPage />} />
        <Route path="/guide" element={<SetupGuidePage />} />
        <Route path="/storage" element={<StoragePage />} />
        <Route path="/snapshots" element={<SnapshotsPage />} />
        <Route path="/system" element={<SystemPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ToastProvider>
  );
}
