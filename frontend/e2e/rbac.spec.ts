import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test("anonymous visitors are sent to sign in for protected areas", async ({ page }) => {
  for (const p of ["/seller", "/admin", "/orders", "/checkout"]) {
    await page.goto(p);
    await expect(page).toHaveURL(/\/login\?next=/);
  }
});

test("wrong credentials show a generic error", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("buyer01@demo.bazar.af");
  await page.getByLabel("Password").fill("definitely-wrong-1");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.locator(".alert.bad")).toHaveText("Invalid email or password");
});

test("a buyer cannot reach seller or admin areas", async ({ page }) => {
  await login(page, "buyer01@demo.bazar.af");
  await page.goto("/admin");
  await expect(page).toHaveURL("/");
  await page.goto("/seller");
  await expect(page).toHaveURL("/");
});

test("a seller cannot reach admin or checkout", async ({ page }) => {
  await login(page, "seller01@demo.bazar.af");
  await page.goto("/admin");
  await expect(page).toHaveURL("/");
  await page.goto("/checkout");
  await expect(page).toHaveURL("/");
});

test("tokens are httpOnly cookies, not readable by page scripts", async ({ page, context }) => {
  await login(page, "buyer01@demo.bazar.af");
  const js = await page.evaluate(() => document.cookie + JSON.stringify({ ...localStorage }));
  expect(js).not.toMatch(/baz_at|baz_rt|eyJ/);
  const cookies = await context.cookies();
  expect(cookies.find((c) => c.name === "baz_at")?.httpOnly).toBe(true);
  expect(cookies.find((c) => c.name === "baz_rt")?.httpOnly).toBe(true);
});

test("proxy refuses token endpoints and the session ends on sign out", async ({ page }) => {
  await login(page, "buyer01@demo.bazar.af");
  const r = await page.request.post("/api/proxy/auth/refresh", { data: { refresh_token: "x".repeat(40) } });
  expect(r.status()).toBe(404);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("link", { name: "Sign in" })).toBeVisible();
  await page.goto("/orders");
  await expect(page).toHaveURL(/\/login/);
});
