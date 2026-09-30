import { expect, type Page } from "@playwright/test";

export const PW = process.env.E2E_PASSWORD ?? "";
if (!PW) throw new Error("Set E2E_PASSWORD to the SEED_PASSWORD used when seeding the database");

export async function login(page: Page, email: string, password = PW) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}
