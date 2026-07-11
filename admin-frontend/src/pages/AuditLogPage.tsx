import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { AuditLogEntry } from "../types/api";

export default function AuditLogPage() {
  const [items, setItems] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [actionFilter, setActionFilter] = useState("");

  const load = async () => {
    const { data } = await apiClient.get("/api/audit-log", {
      params: { action: actionFilter || undefined, limit: 200 },
    });
    setItems(data.items);
    setTotal(data.total);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Журнал аудита ({total})</h1>

      <div className="flex gap-2 mb-4">
        <input
          className="input max-w-sm"
          placeholder="Фильтр по действию (например payment.succeeded)…"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
        />
        <button className="btn-primary" onClick={load}>
          Найти
        </button>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Действие</th>
              <th>Кто</th>
              <th>Сущность</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.created_at).toLocaleString("ru-RU")}</td>
                <td className="font-mono text-xs">{a.action}</td>
                <td>{a.actor_label || a.actor_type}</td>
                <td>
                  {a.entity_type ? `${a.entity_type}:${a.entity_id?.slice(0, 8)}` : "—"}
                </td>
                <td>{a.ip_address || "—"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center text-slate-400 py-6">
                  Нет записей
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
