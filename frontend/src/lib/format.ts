export const afn = (v: string | number) => `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(Number(v))} AFN`;
export const date = (iso: string) => new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
export const dateTime = (iso: string) => new Date(iso).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
export const pref = (p: string, provider?: string | null) => (p === "cash" ? "Cash" : `Mobile Money${provider ? ` · ${provider}` : ""}`);
