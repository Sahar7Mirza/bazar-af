import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test("admin approves a pending seller", async ({ page }) => {
  await login(page, "admin@demo.bazar.af");
  await expect(page).toHaveURL("/admin");
  await expect(page.getByText("Approved sellers")).toBeVisible();
  await page.goto("/admin/sellers?status=pending");
  const rows = page.locator("tbody tr");
  const before = await rows.count();
  test.skip(before === 0, "no pending sellers left in this database");
  await rows.first().getByRole("button", { name: "Approve" }).click();
  await expect(rows).toHaveCount(before - 1);
});

test("admin lists users, searches and sees audit entries", async ({ page }) => {
  await login(page, "admin@demo.bazar.af");
  await page.goto("/admin/users");
  await page.getByLabel("Search users").fill("buyer01");
  await expect(page.getByRole("cell", { name: "buyer01@demo.bazar.af" })).toBeVisible();
  await page.goto("/admin/audit");
  await page.getByLabel("Filter by action").fill("auth.login");
  await expect(page.locator("tbody tr").first()).toContainText("auth.login");
});

test("research dashboard shows statistics from the survey", async ({ page }) => {
  await login(page, "admin@demo.bazar.af");
  await page.goto("/admin/research");
  await expect(page.getByText("Demo data.")).toBeVisible();
  await expect(page.getByRole("progressbar", { name: "Progress towards target" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "What drives willingness to adopt?" })).toBeVisible();
  await expect(page.getByText(/OLS regression/)).toBeVisible();
  await expect(page.getByRole("table", { name: /Correlation matrix/ })).toBeVisible();
  await page.getByLabel("Respondent type", { exact: true }).selectOption("buyer");
  await expect(page.getByText(/n = \d+/).first()).toBeVisible();
  const csv = await page.request.get("/api/proxy/admin/research/export.csv");
  expect(csv.status()).toBe(200);
  expect(csv.headers()["content-type"]).toContain("text/csv");
});
