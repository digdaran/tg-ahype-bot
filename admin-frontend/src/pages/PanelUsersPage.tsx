import { FormEvent, useEffect, useState } from "react";
import { apiClient, apiErrorMessage } from "../api/client";
import type { PanelUser } from "../types/api";

export default function PanelUsersPage() {
  const [items, setItems] = useState<PanelUser[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("operator");

  const load = async () => {
    const { data } = await apiClient.get("/api/panel-users");
    setItems(data);
  };

  useEffect(() => {
    load();
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiClient.post("/api/panel-users", { login, password, full_name: fullName, role });
      setShowForm(false);
      setLogin("");
      setPassword("");
      setFullName("");
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const toggleBlock = async (u: PanelUser) => {
    await apiClient.post(`/api/panel-users/${u.id}/${u.is_blocked ? "unblock" : "block"}`);
    load();
  };

  const changePassword = async (u: PanelUser) => {
    const newPassword = window.prompt(`Новый пароль для ${u.login}:`);
    if (!newPassword) return;
    await apiClient.post(`/api/panel-users/${u.id}/change-password`, { new_password: newPassword });
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Пользователи панели</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Отмена" : "+ Новый пользователь"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={create} className="card mb-6 grid grid-cols-2 gap-4">
          {error && <div className="col-span-2 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</div>}
          <div>
            <label className="block text-sm font-medium mb-1">Логин</label>
            <input className="input" value={login} onChange={(e) => setLogin(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Пароль</label>
            <input type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Имя</label>
            <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Роль</label>
            <select className="input" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="operator">Operator</option>
              <option value="administrator">Administrator</option>
              <option value="super_admin">Super Admin</option>
            </select>
          </div>
          <div className="col-span-2">
            <button type="submit" className="btn-primary">
              Создать
            </button>
          </div>
        </form>
      )}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Логин</th>
              <th>Имя</th>
              <th>Роль</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id}>
                <td>{u.login}</td>
                <td>{u.full_name || "—"}</td>
                <td>{u.role}</td>
                <td>{u.is_blocked ? <span className="badge bg-red-100 text-red-700">заблокирован</span> : <span className="badge bg-emerald-100 text-emerald-700">активен</span>}</td>
                <td className="space-x-2">
                  <button className="text-brand-600 text-sm font-medium" onClick={() => changePassword(u)}>
                    Сменить пароль
                  </button>
                  <button className="text-red-600 text-sm font-medium" onClick={() => toggleBlock(u)}>
                    {u.is_blocked ? "Разблокировать" : "Заблокировать"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
