import { FormEvent, useEffect, useState } from "react";
import { apiClient, apiErrorMessage } from "../api/client";
import type { Giveaway } from "../types/api";

export default function GiveawaysPage() {
  const [items, setItems] = useState<Giveaway[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [prefix, setPrefix] = useState("");
  const [ticketPrice, setTicketPrice] = useState(500);
  const [maxTickets, setMaxTickets] = useState(1000);

  const load = async () => {
    const { data } = await apiClient.get("/api/giveaways");
    setItems(data);
  };

  useEffect(() => {
    load();
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiClient.post("/api/giveaways", { name, prefix, ticket_price: ticketPrice, max_tickets: maxTickets });
      setShowForm(false);
      setName("");
      setPrefix("");
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const action = async (id: string, path: string) => {
    await apiClient.post(`/api/giveaways/${id}/${path}`);
    load();
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Розыгрыши</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Отмена" : "+ Новый розыгрыш"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={create} className="card mb-6 grid grid-cols-2 gap-4">
          {error && <div className="col-span-2 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</div>}
          <div>
            <label className="block text-sm font-medium mb-1">Название</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Префикс номерков</label>
            <input className="input" value={prefix} onChange={(e) => setPrefix(e.target.value.toUpperCase())} required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Стоимость номерка, ₽</label>
            <input
              type="number"
              className="input"
              value={ticketPrice}
              onChange={(e) => setTicketPrice(Number(e.target.value))}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Максимум номерков</label>
            <input
              type="number"
              className="input"
              value={maxTickets}
              onChange={(e) => setMaxTickets(Number(e.target.value))}
              required
            />
          </div>
          <div className="col-span-2">
            <button type="submit" className="btn-primary">
              Создать
            </button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {items.map((g) => (
          <div key={g.id} className="card">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="font-bold text-lg">{g.name}</div>
                <div className="text-xs text-slate-500 font-mono">{g.prefix}</div>
              </div>
              <div className="flex gap-1">
                {g.is_registration_open && <span className="badge bg-emerald-100 text-emerald-700">открыт</span>}
                {g.is_locked && <span className="badge bg-red-100 text-red-700">заблокирован</span>}
                {g.is_immutable && <span className="badge bg-slate-200 text-slate-600">неизменяем</span>}
              </div>
            </div>
            <div className="text-sm text-slate-600 mb-3">
              Цена: {g.ticket_price} ₽ · Выдано {g.tickets_issued} / {g.max_tickets} · Осталось {g.tickets_remaining}
            </div>
            <div className="flex flex-wrap gap-2">
              {!g.is_registration_open ? (
                <button className="btn-secondary" onClick={() => action(g.id, "open")}>
                  Открыть регистрацию
                </button>
              ) : (
                <button className="btn-secondary" onClick={() => action(g.id, "close")}>
                  Закрыть регистрацию
                </button>
              )}
              {!g.is_locked ? (
                <button className="btn-danger" onClick={() => action(g.id, "lock")}>
                  Заблокировать выдачу
                </button>
              ) : (
                <button className="btn-secondary" onClick={() => action(g.id, "unlock")}>
                  Разблокировать
                </button>
              )}
            </div>
          </div>
        ))}
        {items.length === 0 && <div className="text-slate-400">Розыгрышей пока нет</div>}
      </div>
    </div>
  );
}
