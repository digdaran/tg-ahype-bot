import { FormEvent, useEffect, useState } from "react";
import { apiClient, apiErrorMessage } from "../api/client";
import type { Giveaway, ManualRegistration } from "../types/api";
import { StatusBadge } from "./DashboardPage";

export default function ManualRegistrationsPage() {
  const [items, setItems] = useState<ManualRegistration[]>([]);
  const [giveaways, setGiveaways] = useState<Giveaway[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [phone, setPhone] = useState("");
  const [giveawayId, setGiveawayId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [comment, setComment] = useState("");

  const load = async () => {
    const [regsRes, giveawaysRes] = await Promise.all([
      apiClient.get("/api/manual-registrations", { params: { limit: 100 } }),
      apiClient.get("/api/giveaways"),
    ]);
    setItems(regsRes.data.items);
    setGiveaways(giveawaysRes.data);
    if (!giveawayId && giveawaysRes.data.length > 0) setGiveawayId(giveawaysRes.data[0].id);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const createRegistration = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiClient.post("/api/manual-registrations", { phone, giveaway_id: giveawayId, quantity, comment });
      setPhone("");
      setComment("");
      setQuantity(1);
      setShowForm(false);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const confirmRegistration = async (id: string) => {
    await apiClient.post(`/api/manual-registrations/${id}/confirm`);
    load();
  };

  const cancelRegistration = async (id: string) => {
    await apiClient.post(`/api/manual-registrations/${id}/cancel`);
    load();
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Ручные регистрации</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Отмена" : "+ Новая регистрация"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={createRegistration} className="card mb-6 grid grid-cols-2 gap-4">
          {error && <div className="col-span-2 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</div>}
          <div>
            <label className="block text-sm font-medium mb-1">Телефон</label>
            <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+79991234567" required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Розыгрыш</label>
            <select className="input" value={giveawayId} onChange={(e) => setGiveawayId(e.target.value)} required>
              {giveaways.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name} ({g.prefix})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Количество номерков</label>
            <input
              type="number"
              min={1}
              className="input"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Комментарий</label>
            <input className="input" value={comment} onChange={(e) => setComment(e.target.value)} />
          </div>
          <div className="col-span-2">
            <button type="submit" className="btn-primary">
              Создать регистрацию
            </button>
          </div>
        </form>
      )}

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Телефон/участник</th>
              <th>Кол-во</th>
              <th>Статус</th>
              <th>Комментарий</th>
              <th>Создано</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.participant_id}</td>
                <td>{r.quantity}</td>
                <td>
                  <StatusBadge status={r.status} />
                </td>
                <td>{r.comment || "—"}</td>
                <td>{new Date(r.created_at).toLocaleString("ru-RU")}</td>
                <td className="space-x-2">
                  {r.status === "pending" && (
                    <>
                      <button className="text-emerald-600 text-sm font-medium" onClick={() => confirmRegistration(r.id)}>
                        Выдать номерки
                      </button>
                      <button className="text-red-600 text-sm font-medium" onClick={() => cancelRegistration(r.id)}>
                        Отменить
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center text-slate-400 py-6">
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
