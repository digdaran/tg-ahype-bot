import { FormEvent, useEffect, useState } from "react";
import { apiClient } from "../api/client";

interface SettingsData {
  payment_provider_override: string | null;
  active_payment_provider: string;
  support_contact: string | null;
  poster_settings_note: string | null;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [providers, setProviders] = useState<string[]>([]);
  const [override, setOverride] = useState("");
  const [supportContact, setSupportContact] = useState("");
  const [posterNote, setPosterNote] = useState("");
  const [saved, setSaved] = useState(false);

  const load = async () => {
    const [settingsRes, providersRes] = await Promise.all([
      apiClient.get<SettingsData>("/api/settings"),
      apiClient.get("/api/settings/payment-providers"),
    ]);
    setSettings(settingsRes.data);
    setProviders(providersRes.data.providers);
    setOverride(settingsRes.data.payment_provider_override || "");
    setSupportContact(settingsRes.data.support_contact || "");
    setPosterNote(settingsRes.data.poster_settings_note || "");
  };

  useEffect(() => {
    load();
  }, []);

  const save = async (e: FormEvent) => {
    e.preventDefault();
    await apiClient.patch("/api/settings", {
      payment_provider_override: override || null,
      clear_payment_provider_override: !override,
      support_contact: supportContact,
      poster_settings_note: posterNote,
    });
    setSaved(true);
    load();
    setTimeout(() => setSaved(false), 2000);
  };

  if (!settings) return <div className="text-slate-500">Загрузка…</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Настройки</h1>

      <form onSubmit={save} className="card max-w-xl space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Активный платёжный провайдер</label>
          <div className="text-sm text-slate-500 mb-2">
            Сейчас используется: <b>{settings.active_payment_provider === "tbank" ? "Т-Банк" : "ВТБ"}</b> (по умолчанию из .env,
            переопределить можно ниже)
          </div>
          <select className="input" value={override} onChange={(e) => setOverride(e.target.value)}>
            <option value="">Не переопределять (использовать .env)</option>
            {providers.map((p) => (
              <option key={p} value={p}>
                {p === "tbank" ? "Т-Банк" : "ВТБ"}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Контакт поддержки</label>
          <input className="input" value={supportContact} onChange={(e) => setSupportContact(e.target.value)} />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Заметка по настройке постеров</label>
          <textarea className="input" rows={3} value={posterNote} onChange={(e) => setPosterNote(e.target.value)} />
        </div>

        <button type="submit" className="btn-primary">
          Сохранить
        </button>
        {saved && <span className="ml-3 text-emerald-600 text-sm">Сохранено ✓</span>}
      </form>
    </div>
  );
}
