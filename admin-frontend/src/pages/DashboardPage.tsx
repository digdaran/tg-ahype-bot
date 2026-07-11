import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { DashboardData } from "../types/api";
import StatCard from "../components/StatCard";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    apiClient.get<DashboardData>("/api/dashboard").then((res) => setData(res.data));
  }, []);

  if (!data) return <div className="text-slate-500">Загрузка…</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <StatCard label="Участники" value={data.total_participants} />
        <StatCard label="Продано номерков" value={data.tickets_issued} accent="text-brand-600" />
        <StatCard label="Остаток номерков" value={data.tickets_remaining} />
        <StatCard label="Выручка" value={`${data.total_revenue.toLocaleString("ru-RU")} ₽`} accent="text-emerald-600" />
        <StatCard label="Средний чек" value={`${data.average_check.toFixed(0)} ₽`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-3">Последние оплаты</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Заказ</th>
                <th>Сумма</th>
                <th>Статус</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_payments.map((p) => (
                <tr key={p.order_id}>
                  <td>{p.order_id}</td>
                  <td>{p.amount} ₽</td>
                  <td>
                    <StatusBadge status={p.status} />
                  </td>
                  <td>{new Date(p.created_at).toLocaleString("ru-RU")}</td>
                </tr>
              ))}
              {data.recent_payments.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-slate-400 text-center py-4">
                    Пока нет оплат
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2 className="font-semibold mb-3">Последние регистрации</h2>
          <table className="data-table">
            <thead>
              <tr>
                <th>Телефон</th>
                <th>Имя</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_registrations.map((r, i) => (
                <tr key={i}>
                  <td>{r.phone}</td>
                  <td>{r.full_name || "—"}</td>
                  <td>{new Date(r.created_at).toLocaleString("ru-RU")}</td>
                </tr>
              ))}
              {data.recent_registrations.length === 0 && (
                <tr>
                  <td colSpan={3} className="text-slate-400 text-center py-4">
                    Пока нет регистраций
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    succeeded: "bg-emerald-100 text-emerald-700",
    pending: "bg-amber-100 text-amber-700",
    failed: "bg-red-100 text-red-700",
    canceled: "bg-slate-200 text-slate-600",
    confirmed: "bg-emerald-100 text-emerald-700",
    cancelled: "bg-red-100 text-red-700",
  };
  return <span className={`badge ${colors[status] || "bg-slate-100 text-slate-600"}`}>{status}</span>;
}
