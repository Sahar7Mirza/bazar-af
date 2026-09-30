import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, fieldErrors } from "@/lib/api";
import { afn, pref } from "@/lib/format";

describe("format", () => {
  it("formats AFN amounts", () => { expect(afn("1234.5")).toBe("1,234.5 AFN"); expect(afn(0)).toBe("0 AFN"); });
  it("describes payment preference", () => { expect(pref("cash")).toBe("Cash"); expect(pref("mobile_money", "HesabPay")).toBe("Mobile Money · HesabPay"); });
});

describe("api client", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));
  afterEach(() => vi.unstubAllGlobals());
  const mock = (status: number, body: unknown) => (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(new Response(body === undefined ? null : JSON.stringify(body), { status }));

  it("goes through the BFF proxy and builds the query string, skipping empty values", async () => {
    mock(200, { ok: true });
    await api("products", { query: { q: "naan", page: 2, district: "", x: undefined } });
    expect((fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0][0]).toBe("/api/proxy/products?q=naan&page=2");
  });
  it("sends JSON bodies", async () => {
    mock(201, {});
    await api("orders", { method: "POST", body: { a: 1 } });
    const init = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0][1];
    expect(init.method).toBe("POST"); expect(init.body).toBe('{"a":1}'); expect(init.headers["Content-Type"]).toBe("application/json");
  });
  it("parses the unified error format", async () => {
    mock(422, { error: { code: "validation_error", message: "Request validation failed", request_id: "r1", details: [{ field: "email", message: "bad" }] } });
    const err = await api("x").catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 422, code: "validation_error", requestId: "r1" });
    expect(fieldErrors(err)).toEqual({ email: "bad" });
  });
  it("returns undefined for 204 and a friendly error when offline", async () => {
    mock(204, undefined);
    expect(await api("x", { method: "DELETE" })).toBeUndefined();
    (fetch as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(new TypeError("network"));
    await expect(api("x")).rejects.toMatchObject({ status: 0, code: "network" });
  });
});

describe("cart", () => {
  const store = new Map<string, string>();
  beforeEach(() => { store.clear(); vi.stubGlobal("localStorage", { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => store.set(k, v) }); vi.resetModules(); });
  afterEach(() => vi.unstubAllGlobals());
  const line = (id: number, sellerId = 1, max = 5) => ({ productId: id, name: `P${id}`, price: "10", unit: "kg", sellerId, sellerName: "S", max });

  it("rejects products from a second seller", async () => {
    const { cart } = await import("@/lib/cart");
    expect(cart.add(line(1, 1)).ok).toBe(true);
    expect(cart.add(line(2, 2))).toEqual({ ok: false, reason: "one_seller" });
  });
  it("merges quantities and never exceeds stock", async () => {
    const { cart, cartTotal } = await import("@/lib/cart");
    cart.add(line(1, 1, 5), 3); cart.add(line(1, 1, 5), 4);
    const saved = JSON.parse(store.get("bazar.cart.v1")!);
    expect(saved).toHaveLength(1); expect(saved[0].qty).toBe(5);
    expect(cartTotal(saved)).toBe(50);
    cart.setQty(1, 99); expect(JSON.parse(store.get("bazar.cart.v1")!)[0].qty).toBe(5);
    cart.setQty(1, 0); expect(JSON.parse(store.get("bazar.cart.v1")!)[0].qty).toBe(1);
  });
});
