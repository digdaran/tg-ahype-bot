import { FormEvent, useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { Broadcast } from "../types/api";

export default function BroadcastsPage() {
  const [items, setItems] = useState<Broadcast[]>([]);
  const [showForm, setShowForm] = useState(false);

  const [title, setTitle] = useState("");
  const [messageText, setMessageText] = useState("");
  // Канал сейчас только Telegram - VK-интеграция полностью удалена из
  // проекта (вернёмся к ней отдельно позже), поэтому выбор канала в форме
  // больше не нужен.
  const channel = "telegram";
  const [audience, setAudience] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [minTickets, setMinTickets] = useState("");
  const [maxTickets, setMaxTickets] = useState("");

  const load = async () => {
    const { data } = await apiClient.get("/api/broadcasts");
    setItems(data);
  };

  useEffect(() => {
    load();
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    await apiClient.post("/api/broadcasts", {
      title,
      message_text: messageText,
      channel,
      audience,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      min_tickets: minTickets ? Number(minTickets) : undefined,
      max_tickets: maxTickets ? Number(maxTickets) : undefined,
    });
    setShowForm(false);
    setTitle("");
    setMessageText("");
    load();
  };

  const send = async (id: string) => {
    if (!window.confirm("Отправить рассылку сейчас?")) return;
    await apiClient.post(`/api/broadcasts/${id}/send`);
    load();
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Рассылки</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Отмена" : "+ Новая рассылка"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={create} className="card mb-6 grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-sm font-medium mb-1">Заголовок</label>
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium mb-1">Текст сообщения</label>
            <textarea className="input" rows={3} value={messageText} onChange={(e) => setMessageText(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Аудитория</label>
            <select className="input" value={audience} onChange={(e) => setAudience(e.target.value)}>
              <option value="all">Все</option>
              <option value="paid">Только оплатившие</option>
              <option value="unpaid">Только неоплатившие</option>
              <option value="offline">Только офлайн</option>
              <option value="online">Только онлайн</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Дата от</label>
            <input type="date" className="input" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Дата до</label>
            <input type="date" className="input" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Кол-во номерков от</label>
            <input type="number" className="input" value={minTickets} onChange={(e) => setMinTickets(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Кол-во номерков до</label>
            <input type="number" className="input" value={maxTickets} onChange={(e) => setMaxTickets(e.target.value)} />
          </div>
          <div className="col-span-2">
            <button type="submit" className="btn-primary">
              Создать черновик
            </button>
          </div>
        </form>
      )}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Заголовок</th>
              <th>Канал</th>
              <th>Статус</th>
              <th>Статистика</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((b) => (
              <tr key={b.id}>
                <td>{b.title}</td>
                <td>{b.channel}</td>
                <td>{b.status}</td>
                <td>{b.stats || "—"}</td>
                <td>
                  {b.status === "draft" && (
                    <button className="text-brand-600 text-sm font-medium" onClick={() => send(b.id)}>
                      Отправить
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center text-slate-400 py-6">
                  Рассылок пока нет
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
