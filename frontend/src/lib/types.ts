export type Role = "buyer" | "seller" | "admin";
export interface User { id: number; email: string; full_name: string; phone: string | null; district: string | null; role: Role; is_active: boolean }
export interface Page<T> { items: T[]; page: number; page_size: number; total: number; pages: number; counts?: Record<string, number> }
export interface Category { id: number; name: string; slug: string; is_active: boolean }
export interface Product {
  id: number; seller_id: number; category_id: number | null; name: string; description: string | null; price_afn: string; unit: string; stock_qty: number;
  status: "active" | "hidden"; hidden_by_admin: boolean; created_at: string; updated_at: string; seller_name?: string | null; district?: string | null;
}
export interface Seller {
  id: number; business_name: string; category_id: number | null; description: string | null; district: string | null; address_note: string | null;
  phone: string | null; opening_hours: string | null; status: "pending" | "approved" | "rejected" | "suspended"; review_note: string | null; created_at: string;
}
export type OrderStatus = "pending" | "confirmed" | "ready" | "completed" | "cancelled";
export interface OrderItem { product_id: number; product_name: string; unit_price_afn: string; quantity: number; line_total_afn: string }
export interface Order {
  id: number; buyer_id: number; seller_id: number; status: OrderStatus; payment_preference: "cash" | "mobile_money"; mobile_money_provider: string | null;
  payment_status: string; total_afn: string; buyer_note: string | null; cancel_reason: string | null; estimated_pickup_at: string | null; created_at: string; updated_at: string; items: OrderItem[];
}
export interface Question { id: number; construct: string; code: string; text_en: string; text_fa: string | null; position: number }
export const DISTRICTS = [...Array.from({ length: 22 }, (_, i) => `PD${i + 1}`), "Other"];
export const PROVIDERS = ["M-Paisa", "HesabPay", "Afghan Wireless Mobile Money", "MoneyPay", "Other"];
export interface AppNotification { id: number; order_id: number | null; product_id: number | null; kind: string; title: string; message: string; read_at: string | null; created_at: string }
export interface LiveState { unread: number; latest: { id: number; kind: string; title: string; message: string; order_id: number | null } | null; pending_orders?: number }
export type RecommendedProduct = Product & { reason: string | null; match: number };
