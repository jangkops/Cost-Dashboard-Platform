import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Onboarding from "./pages/Onboarding";
import SSOTest from "./pages/SSOTest";
import CreateAccount from "./pages/CreateAccount";
import UpdateRole from "./pages/UpdateRole";
import DeleteAccount from "./pages/DeleteAccount";
import ProjectGroups from "./pages/ProjectGroups";
import Monitoring from "./pages/Monitoring";
import UserLogs from "./pages/UserLogs";
import GitHubPermissions from "./pages/GitHubPermissions";
import GitHubAuditLogs from "./pages/GitHubAuditLogs";
import CostMonitoring from "./pages/CostMonitoring";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("authToken");
  return token ? children : <Navigate to="/login" replace />;
}

function LoginWrapper() {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) {
      navigate("/");
    }
  }, [navigate]);

  const handleLogin = (data) => {
    setIsAuthenticated(true);
    navigate("/");
  };

  return <Login onLogin={handleLogin} />;
}

function LayoutWrapper() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("userRole");
    localStorage.removeItem("username");
    navigate("/login");
  };

  return <Layout onLogout={handleLogout} />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginWrapper />} />
        <Route path="/cost-monitoring" element={<CostMonitoring />} />
        <Route element={<ProtectedRoute><LayoutWrapper /></ProtectedRoute>}>
          <Route path="/" element={<Onboarding />} />
          <Route path="/provisioning/onboarding" element={<Onboarding />} />
          <Route path="/provisioning/offboarding" element={<div className="p-8"><h1 className="text-3xl font-bold">사용자 삭제 (준비 중)</h1></div>} />
          <Route path="/sso-test" element={<SSOTest />} />
          <Route path="/server/create" element={<CreateAccount />} />
          <Route path="/server/update" element={<UpdateRole />} />
          <Route path="/server/delete" element={<DeleteAccount />} />
          <Route path="/server/project-groups" element={<ProjectGroups />} />
          <Route path="/sso/permission" element={<div className="p-8"><h1 className="text-3xl font-bold">SSO 권한 변경 (준비 중)</h1></div>} />
          <Route path="/github/permissions" element={<GitHubPermissions />} />
          <Route path="/github-audit" element={<GitHubAuditLogs />} />
          <Route path="/logs" element={<Monitoring />} />
          <Route path="/user-logs" element={<UserLogs />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
