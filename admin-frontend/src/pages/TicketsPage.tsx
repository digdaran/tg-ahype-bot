import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { Ticket } from "../types/api";

export default function TicketsPage() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);

  const load = async () => {
    const { data } = await apiClient.get("/api/tickets", { params: { q: query || undefined, limit: 100 } });
    setItems(data.items);
    setTotal(data.total);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Номерки ({total})</h1>

      <div className="flex gap-2 mb-4">
        <input
          className="input max-w-sm"
          placeholder="Поиск по коду номерка…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
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
              <th>Код</th>
              <th>Участник</th>
              <th>Источник</th>
              <th>Выдан</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id}>
                <td className="font-mono">{t.full_code}</td>
                <td>{t.participant_id}</td>
                <td>{t.source === "online" ? "Онлайн" : "Офлайн"}</td>
                <td>{new Date(t.issued_at).toLocaleString("ru-RU")}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="text-center text-slate-400 py-6">
                  Нет данных
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
