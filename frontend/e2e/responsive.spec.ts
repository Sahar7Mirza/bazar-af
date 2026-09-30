import { expect, test } from "@playwright/test";

test("mobile layout: menu works and nothing overflows horizontally", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Menu" }).click();
  await page.getByRole("link", { name: "Shop", exact: true }).click();
  await expect(page).toHaveURL(/\/products/);
  await expect(page.locator("a.prod").first()).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});
