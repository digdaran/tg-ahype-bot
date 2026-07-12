import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { ManualRegistration, Participant, Payment, Ticket } from "../types/api";

export default function ParticipantsPage() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Participant[]>([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<Participant | null>(null);

  const load = async () => {
    const { data } = await apiClient.get("/api/participants", { params: { q: query || undefined, limit: 50 } });
    setItems(data.items);
    setTotal(data.total);
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Участники ({total})</h1>

      <div className="flex gap-2 mb-4">
        <input
          className="input max-w-sm"
          placeholder="Поиск по телефону, имени, telegram…"
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
              <th>Телефон</th>
              <th>Имя</th>
              <th>Telegram</th>
              <th>Регистрация</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id}>
                <td>{p.phone}</td>
                <td>{p.full_name || "—"}</td>
                <td>{p.telegram_username ? `@${p.telegram_username}` : p.telegram_user_id ? "привязан" : "—"}</td>
                <td>{new Date(p.created_at).toLocaleDateString("ru-RU")}</td>
                <td>
                  <button className="text-brand-600 text-sm font-medium" onClick={() => setSelected(p)}>
                    Подробнее
                  </button>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center text-slate-400 py-6">
                  Ничего не найдено
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selected && <ParticipantDetail participant={selected} onClose={() => setSelected(null)} onSaved={load} />}
    </div>
  );
}

function ParticipantDetail({
  participant,
  onClose,
  onSaved,
}: {
  participant: Participant;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [manualRegs, setManualRegs] = useState<ManualRegistration[]>([]);
  const [fullName, setFullName] = useState(participant.full_name || "");
  const [comment, setComment] = useState(participant.comment || "");
  const [isBlocked, setIsBlocked] = useState(participant.is_blocked);

  useEffect(() => {
    apiClient.get(`/api/participants/${participant.id}/tickets`).then((r) => setTickets(r.data));
    apiClient.get(`/api/participants/${participant.id}/payments`).then((r) => setPayments(r.data));
    apiClient.get(`/api/participants/${participant.id}/manual-registrations`).then((r) => setManualRegs(r.data));
  }, [participant.id]);

  const save = async () => {
    await apiClient.patch(`/api/participants/${participant.id}`, {
      full_name: fullName,
      comment,
      is_blocked: isBlocked,
    });
    onSaved();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-lg font-bold">{participant.phone}</h2>
          <button className="text-slate-400 hover:text-slate-700" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium mb-1">Имя</label>
            <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="flex items-end gap-2">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={isBlocked} onChange={(e) => setIsBlocked(e.target.checked)} />
              Заблокирован
            </label>
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium mb-1">Комментарий</label>
            <textarea className="input" rows={2} value={comment} onChange={(e) => setComment(e.target.value)} />
          </div>
        </div>
        <button className="btn-primary mb-6" onClick={save}>
          Сохранить
        </button>

        <h3 className="font-semibold mb-2">Номерки ({tickets.length})</h3>
        <div className="flex flex-wrap gap-1 mb-6">
          {tickets.map((t) => (
            <span key={t.id} className="badge bg-brand-50 text-brand-700">
              {t.full_code}
            </span>
          ))}
          {tickets.length === 0 && <span className="text-slate-400 text-sm">Нет номерков</span>}
        </div>

        <h3 className="font-semibold mb-2">Платежи ({payments.length})</h3>
        <ul className="text-sm mb-6 space-y-1">
          {payments.map((p) => (
            <li key={p.id}>
              {p.order_id} — {p.amount} ₽ — {p.status}
            </li>
          ))}
          {payments.length === 0 && <li className="text-slate-400">Нет платежей</li>}
        </ul>

        <h3 className="font-semibold mb-2">Ручные регистрации ({manualRegs.length})</h3>
        <ul className="text-sm space-y-1">
          {manualRegs.map((r) => (
            <li key={r.id}>
              {r.quantity} шт. — {r.status} ({new Date(r.created_at).toLocaleDateString("ru-RU")})
            </li>
          ))}
          {manualRegs.length === 0 && <li className="text-slate-400">Нет ручных регистраций</li>}
        </ul>
      </div>
    </div>
  );
}
