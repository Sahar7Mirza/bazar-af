import { expect, test } from "@playwright/test";

test("anyone can complete the anonymous survey", async ({ page }) => {
  await page.goto("/survey");
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByText("Please tick the consent box")).toBeVisible();
  await page.getByLabel(/I am 18 or older/).check();
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByText("seller, buyer or other")).toBeVisible();
  await page.getByLabel("I am mainly a…").selectOption("seller");
  await page.getByRole("button", { name: "Next" }).click();
  for (let step = 0; step < 6; step++) {
    await page.getByRole("button", { name: /^(Next|Submit)$/ }).click();   // unanswered page is refused
    await expect(page.getByText("Please answer every statement on this page.")).toBeVisible();
    const groups = page.locator("fieldset.card");
    const n = await groups.count();
    for (let i = 0; i < n; i++) await groups.nth(i).locator("label").nth((i + step) % 4 + 1).click();
    await page.getByRole("button", { name: /^(Next|Submit)$/ }).click();
  }
  await expect(page.getByRole("heading", { name: /Thank you/ })).toBeVisible();
});
