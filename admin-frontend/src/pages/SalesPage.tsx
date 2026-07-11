import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { Payment } from "../types/api";
import { StatusBadge } from "./DashboardPage";

export default function SalesPage() {
  const [items, setItems] = useState<Payment[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("");
  const [provider, setProvider] = useState("");

  const load = async () => {
    const { data } = await apiClient.get("/api/sales", {
      params: { status: status || undefined, provider: provider || undefined, limit: 100 },
    });
    setItems(data.items);
    setTotal(data.total);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, provider]);

  const exportCsv = () => {
    window.open(`${apiClient.defaults.baseURL}/api/sales/export`, "_blank");
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Продажи ({total})</h1>
        <button className="btn-secondary" onClick={exportCsv}>
          Экспорт CSV
        </button>
      </div>

      <div className="flex gap-3 mb-4">
        <select className="input max-w-xs" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Все статусы</option>
          <option value="pending">Ожидает</option>
          <option value="succeeded">Успешно</option>
          <option value="failed">Отклонён</option>
          <option value="canceled">Отменён</option>
        </select>
        <select className="input max-w-xs" value={provider} onChange={(e) => setProvider(e.target.value)}>
          <option value="">Все банки</option>
          <option value="tbank">Т-Банк</option>
          <option value="vtb">ВТБ</option>
        </select>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Заказ</th>
              <th>Payment ID</th>
              <th>Банк</th>
              <th>Кол-во</th>
              <th>Сумма</th>
              <th>Статус</th>
              <th>Дата</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id}>
                <td>{p.order_id}</td>
                <td>{p.provider_payment_id || "—"}</td>
                <td>{p.provider === "tbank" ? "Т-Банк" : "ВТБ"}</td>
                <td>{p.quantity}</td>
                <td>{p.amount} ₽</td>
                <td>
                  <StatusBadge status={p.status} />
                </td>
                <td>{new Date(p.created_at).toLocaleString("ru-RU")}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center text-slate-400 py-6">
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
