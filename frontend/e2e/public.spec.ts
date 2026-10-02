import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("landing page shows hero, categories and live products", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("small businesses");
  await expect(page.getByText("No real payments are processed").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Browse by category" })).toBeVisible();
  await expect(page.locator("a.prod").first()).toBeVisible();
});

test("search, filter, sort and paginate the catalogue", async ({ page }) => {
  await page.goto("/products");
  await expect(page.locator("a.prod").first()).toBeVisible();
  await page.getByLabel("Search products").fill("naan");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page).toHaveURL(/q=naan/);
  await expect(page.locator("a.prod").first()).toBeVisible();
  const names = await page.locator("a.prod strong").allTextContents();
  expect(names.length).toBeGreaterThan(0);
  expect(names.every((n) => /naan/i.test(n))).toBeTruthy();
  await page.getByLabel("Search products").fill("zzzz-no-such-product");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.getByRole("heading", { name: "No products found" })).toBeVisible();   // empty state
  await page.getByRole("button", { name: "Clear filters" }).first().click();
  await page.getByLabel("Sort").selectOption("price:asc");
  await expect(page.locator("a.prod").first()).toBeVisible();
  await page.getByRole("button", { name: "Next →" }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(page.getByText(/Page 2 of/)).toBeVisible();
});

test("product detail page", async ({ page }) => {
  await page.goto("/products");
  await page.locator("a.prod").first().click();
  await expect(page.getByRole("button", { name: "Add to cart" })).toBeVisible();
  await expect(page.getByText(/AFN/).first()).toBeVisible();
});

test("unknown product shows an error state, not a crash", async ({ page }) => {
  await page.goto("/products/99999999");
  await expect(page.locator(".state[role=alert]")).toContainText(/not found/i);
});

test("landing and catalogue have no serious accessibility violations", async ({ page }) => {
  for (const url of ["/", "/products", "/login", "/register"]) {
    await page.goto(url);
    await page.waitForLoadState("networkidle");
    const res = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    const bad = res.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(bad.map((v) => `${url}: ${v.id}`), JSON.stringify(bad.map((v) => v.nodes.map((n) => n.html).slice(0, 2)))).toEqual([]);
  }
});
