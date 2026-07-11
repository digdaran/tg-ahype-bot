import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./store/AuthContext";
import Layout from "./components/Layout";
import PrivateRoute from "./components/PrivateRoute";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ParticipantsPage from "./pages/ParticipantsPage";
import SalesPage from "./pages/SalesPage";
import ManualRegistrationsPage from "./pages/ManualRegistrationsPage";
import TicketsPage from "./pages/TicketsPage";
import GiveawaysPage from "./pages/GiveawaysPage";
import SettingsPage from "./pages/SettingsPage";
import PanelUsersPage from "./pages/PanelUsersPage";
import BroadcastsPage from "./pages/BroadcastsPage";
import ReportsPage from "./pages/ReportsPage";
import AuditLogPage from "./pages/AuditLogPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<PrivateRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/participants" element={<ParticipantsPage />} />
              <Route path="/sales" element={<SalesPage />} />
              <Route path="/manual-registrations" element={<ManualRegistrationsPage />} />
              <Route path="/tickets" element={<TicketsPage />} />
              <Route path="/giveaways" element={<GiveawaysPage />} />
              <Route path="/broadcasts" element={<BroadcastsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/panel-users" element={<PanelUsersPage />} />
              <Route path="/audit-log" element={<AuditLogPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
