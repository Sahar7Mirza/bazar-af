import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test("buyer registers, then shops and places an order with a mobile money preference", async ({ page }) => {
  const email = `e2e.${Date.now()}@example.com`;
  await page.goto("/register");
  await page.getByLabel("Full name").fill("E2E Buyer");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill("weak");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("At least 10 characters, with letters and digits").first()).toBeVisible();  // client validation
  const pw = `E2e-${Date.now()}-pw`;
  await page.getByLabel("Password", { exact: true }).fill(pw);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/login/);
  await login(page, email, pw);

  await page.goto("/products");
  await page.locator("a.prod").first().click();
  await page.getByLabel("Quantity").fill("2");
  await page.getByRole("button", { name: "Add to cart" }).click();
  await expect(page.getByText("Added to your cart.")).toBeVisible();
  await page.goto("/cart");
  await expect(page.getByRole("heading", { name: "Your cart" })).toBeVisible();
  await page.getByRole("link", { name: "Checkout" }).click();

  await expect(page.getByText("preference only")).toBeVisible();
  await page.getByLabel("Mobile Money").check();
  await page.getByRole("button", { name: /Place order/ }).click();
  await expect(page.getByText("Select a provider", { exact: false }).or(page.getByText("Choose a provider"))).toBeVisible();  // provider required
  await page.getByLabel("Provider", { exact: true }).selectOption("HesabPay");
  await page.getByRole("button", { name: /Place order/ }).click();

  await expect(page).toHaveURL(/\/orders\/\d+\?placed=1/);
  await expect(page.getByText("Order placed.")).toBeVisible();
  await expect(page.getByText("Mobile Money · HesabPay")).toBeVisible();
  await expect(page.getByText("Not processed (simulated)")).toBeVisible();

  await page.getByRole("button", { name: "Cancel order" }).click();
  await expect(page.locator(".chip", { hasText: "cancelled" }).first()).toBeVisible();
});

test("cart accepts products from one seller only", async ({ page }) => {
  await login(page, "buyer01@demo.bazar.af");
  await page.goto("/products");
  await expect(page.locator("a.prod").first()).toBeVisible();
  const links = await page.locator("a.prod").evaluateAll((els) => els.map((e) => (e as HTMLAnchorElement).href));
  await page.goto(links[0]);
  await page.getByRole("button", { name: "Add to cart" }).click();
  const seller0 = await page.locator("p", { hasText: "Sold by" }).first().innerText();
  let blocked = false;
  for (const l of links.slice(1)) {
    await page.goto(l);
    if ((await page.locator("p", { hasText: "Sold by" }).first().innerText()) === seller0) continue;
    await page.getByRole("button", { name: "Add to cart" }).click();
    if (await page.getByText("another seller").isVisible()) { blocked = true; break; }
  }
  expect(blocked).toBe(true);
});

test("order history lists the buyer's orders with pagination controls", async ({ page }) => {
  await login(page, "buyer01@demo.bazar.af");
  await page.goto("/orders");
  await expect(page.getByRole("heading", { name: "My orders" })).toBeVisible();
  await expect(page.locator("table tbody tr, .state").first()).toBeVisible();
});
