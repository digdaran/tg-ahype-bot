import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../store/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", roles: ["super_admin", "administrator", "operator"] },
  { to: "/participants", label: "Участники", roles: ["super_admin", "administrator", "operator"] },
  { to: "/sales", label: "Продажи", roles: ["super_admin", "administrator", "operator"] },
  { to: "/manual-registrations", label: "Ручные регистрации", roles: ["super_admin", "administrator", "operator"] },
  { to: "/tickets", label: "Номерки", roles: ["super_admin", "administrator", "operator"] },
  { to: "/giveaways", label: "Розыгрыши", roles: ["super_admin", "administrator", "operator"] },
  { to: "/broadcasts", label: "Рассылки", roles: ["super_admin", "administrator"] },
  { to: "/reports", label: "Отчёты", roles: ["super_admin", "administrator"] },
  { to: "/settings", label: "Настройки", roles: ["super_admin", "administrator"] },
  { to: "/panel-users", label: "Пользователи панели", roles: ["super_admin"] },
  { to: "/audit-log", label: "Журнал аудита", roles: ["super_admin", "administrator"] },
];

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 shrink-0 bg-slate-900 text-slate-200 flex flex-col">
        <div className="px-5 py-5 text-lg font-bold text-white border-b border-slate-800">
          🎟 Raffle Admin
        </div>
        <nav className="flex-1 overflow-y-auto py-3">
          {NAV_ITEMS.filter((item) => !user || item.roles.includes(user.role)).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `block px-5 py-2.5 text-sm rounded-lg mx-2 mb-1 transition-colors ${
                  isActive ? "bg-brand-600 text-white" : "hover:bg-slate-800"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-slate-800 text-sm">
          <div className="font-medium text-white">{user?.full_name || user?.login}</div>
          <div className="text-slate-400 text-xs mb-3">{roleLabel(user?.role)}</div>
          <button className="btn-secondary w-full" onClick={logout}>
            Выйти
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}

function roleLabel(role?: string): string {
  switch (role) {
    case "super_admin":
      return "Super Admin";
    case "administrator":
      return "Administrator";
    case "operator":
      return "Operator";
    default:
      return "";
  }
}
