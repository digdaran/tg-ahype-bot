export type PanelRole = "super_admin" | "administrator" | "operator";
export type PaymentProvider = "tbank" | "vtb";
export type PaymentStatus = "pending" | "succeeded" | "failed" | "canceled";
export type TicketSource = "online" | "manual";
export type ManualRegistrationStatus = "pending" | "confirmed" | "cancelled";
export type BroadcastChannel = "telegram";
export type BroadcastStatus = "draft" | "sending" | "sent" | "failed";

export interface PanelUser {
  id: string;
  login: string;
  full_name?: string | null;
  role: PanelRole;
  is_blocked: boolean;
  last_login_at?: string | null;
  created_at: string;
}

export interface Participant {
  id: string;
  phone: string;
  full_name?: string | null;
  telegram_user_id?: number | null;
  telegram_username?: string | null;
  is_blocked: boolean;
  comment?: string | null;
  created_at: string;
}

export interface Giveaway {
  id: string;
  name: string;
  prefix: string;
  ticket_price: number;
  max_tickets: number;
  tickets_issued: number;
  tickets_remaining: number;
  is_registration_open: boolean;
  is_locked: boolean;
  is_immutable: boolean;
  opened_at?: string | null;
  locked_at?: string | null;
  created_at: string;
}

export interface Ticket {
  id: string;
  giveaway_id: string;
  number: number;
  full_code: string;
  participant_id: string;
  source: TicketSource;
  payment_id?: string | null;
  manual_registration_id?: string | null;
  issued_at: string;
}

export interface Payment {
  id: string;
  order_id: string;
  participant_id: string;
  giveaway_id: string;
  provider: PaymentProvider;
  provider_payment_id?: string | null;
  quantity: number;
  amount: number;
  currency: string;
  status: PaymentStatus;
  payment_url?: string | null;
  confirmed_at?: string | null;
  failure_reason?: string | null;
  created_at: string;
}

export interface ManualRegistration {
  id: string;
  participant_id: string;
  giveaway_id: string;
  quantity: number;
  comment?: string | null;
  status: ManualRegistrationStatus;
  operator_id: string;
  cancelled_by_id?: string | null;
  cancelled_at?: string | null;
  confirmed_at?: string | null;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  actor_type: string;
  actor_id?: string | null;
  actor_label?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  details?: string | null;
  ip_address?: string | null;
  created_at: string;
}

export interface Broadcast {
  id: string;
  title: string;
  message_text: string;
  channel: BroadcastChannel;
  status: BroadcastStatus;
  created_by_id: string;
  sent_at?: string | null;
  stats?: string | null;
  created_at: string;
}

export interface DashboardData {
  total_participants: number;
  tickets_issued: number;
  tickets_remaining: number;
  total_revenue: number;
  average_check: number;
  recent_payments: { order_id: string; amount: number; status: string; created_at: string }[];
  recent_registrations: { phone: string; full_name: string | null; created_at: string }[];
}

export interface Paginated<T> {
  items: T[];
  total: number;
}
