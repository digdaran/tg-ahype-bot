import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiClient } from "../api/client";

export default function ReportsPage() {
  const [salesByDay, setSalesByDay] = useState<any[]>([]);
  const [salesByMonth, setSalesByMonth] = useState<any[]>([]);
  const [onlineOffline, setOnlineOffline] = useState<{ online_tickets: number; offline_tickets: number } | null>(null);
  const [byOperator, setByOperator] = useState<any[]>([]);
  const [byProvider, setByProvider] = useState<any[]>([]);
  const [financial, setFinancial] = useState<any | null>(null);

  useEffect(() => {
    apiClient.get("/api/reports/sales-by-day").then((r) => setSalesByDay(r.data));
    apiClient.get("/api/reports/sales-by-month").then((r) => setSalesByMonth(r.data));
    apiClient.get("/api/reports/online-vs-offline").then((r) => setOnlineOffline(r.data));
    apiClient.get("/api/reports/by-operator").then((r) => setByOperator(r.data));
    apiClient.get("/api/reports/by-payment-provider").then((r) => setByProvider(r.data));
    apiClient.get("/api/reports/financial-summary").then((r) => setFinancial(r.data));
  }, []);

  const exportParticipants = () => {
    window.open(`${apiClient.defaults.baseURL}/api/reports/participants/export`, "_blank");
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Отчёты</h1>
        <button className="btn-secondary" onClick={exportParticipants}>
          Экспорт участников (CSV)
        </button>
      </div>

      {financial && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="card">
            <div className="text-xs uppercase text-slate-500 mb-1">Выручка</div>
            <div className="text-2xl font-bold">{financial.total_revenue.toLocaleString("ru-RU")} ₽</div>
          </div>
          <div className="card">
            <div className="text-xs uppercase text-slate-500 mb-1">Успешных оплат</div>
            <div className="text-2xl font-bold">{financial.successful_payments}</div>
          </div>
          <div className="card">
            <div className="text-xs uppercase text-slate-500 mb-1">Средний чек</div>
            <div className="text-2xl font-bold">{financial.average_check.toFixed(0)} ₽</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <h2 className="font-semibold mb-3">Продажи по дням</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={salesByDay}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" fontSize={11} />
              <YAxis fontSize={11} />
              <Tooltip />
              <Line type="monotone" dataKey="amount" stroke="#2f57d6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="font-semibold mb-3">Продажи по месяцам</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={salesByMonth}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" fontSize={11} />
              <YAxis fontSize={11} />
              <Tooltip />
              <Bar dataKey="amount" fill="#3b6df0" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-3">Онлайн vs Офлайн</h2>
          {onlineOffline && (
            <ul className="text-sm space-y-1">
              <li>Онлайн номерков: {onlineOffline.online_tickets}</li>
              <li>Офлайн номерков: {onlineOffline.offline_tickets}</li>
            </ul>
          )}
        </div>

        <div className="card">
          <h2 className="font-semibold mb-3">По операторам</h2>
          <ul className="text-sm space-y-1">
            {byOperator.map((o, i) => (
              <li key={i}>
                {o.operator}: {o.registrations} регистраций, {o.tickets} номерков
              </li>
            ))}
            {byOperator.length === 0 && <li className="text-slate-400">Нет данных</li>}
          </ul>
        </div>

        <div className="card">
          <h2 className="font-semibold mb-3">По платёжным системам</h2>
          <ul className="text-sm space-y-1">
            {byProvider.map((p, i) => (
              <li key={i}>
                {p.provider === "tbank" ? "Т-Банк" : "ВТБ"}: {p.count} платежей, {p.amount.toLocaleString("ru-RU")} ₽
              </li>
            ))}
            {byProvider.length === 0 && <li className="text-slate-400">Нет данных</li>}
          </ul>
        </div>
      </div>
    </div>
  );
}
