import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test("seller manages products end to end", async ({ page }) => {
  await login(page, "seller01@demo.bazar.af");
  await expect(page).toHaveURL("/seller");
  await expect(page.getByText("To confirm")).toBeVisible();
  await page.getByRole("link", { name: "Products" }).click();
  await page.getByRole("link", { name: "Add product" }).first().click();

  await page.getByRole("button", { name: "Save product" }).click();
  await expect(page.getByText("Enter a product name")).toBeVisible();  // validation
  const name = `E2E Tea ${Date.now()}`;
  await page.getByLabel("Product name").fill(name);
  await page.getByLabel("Price (AFN)").fill("-3");
  await page.getByRole("button", { name: "Save product" }).click();
  await expect(page.getByText("Enter a price of 0 or more")).toBeVisible();
  await page.getByLabel("Price (AFN)").fill("45.50");
  await page.getByLabel("Stock").fill("12");
  await page.getByRole("button", { name: "Save product" }).click();

  await expect(page).toHaveURL(/\/seller\/products$/);
  await page.getByLabel("Search your products").fill(name);
  const row = page.getByRole("row", { name: new RegExp(name) });
  await expect(row).toBeVisible();
  await expect(row).toContainText("45.5 AFN");

  await row.getByRole("button", { name: "Hide" }).click();
  await expect(row).toContainText("hidden");
  page.once("dialog", (d) => d.accept());
  await row.getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("heading", { name: "No products yet" })).toBeVisible();
});

test("seller processes an incoming order through the status flow", async ({ browser }) => {
  const b = await browser.newPage();
  await login(b, "buyer05@demo.bazar.af");
  const pid = (await (await b.request.get("/api/proxy/products?seller_id=1&page_size=1")).json()).items[0].id;
  await b.goto(`/products/${pid}`);
  await b.getByRole("button", { name: "Add to cart" }).click();
  await b.goto("/checkout");
  await b.getByRole("button", { name: /Place order/ }).click();
  await expect(b).toHaveURL(/\/orders\/(\d+)\?placed=1/);
  const orderUrl = b.url().replace("?placed=1", "");
  await b.close();

  // seller01 owns seller_id 1
  const s = await browser.newPage();
  await login(s, "seller01@demo.bazar.af");
  await s.goto(orderUrl);
  for (const [button, status] of [["Confirm order", "confirmed"], ["Mark ready", "ready"], ["Mark completed", "completed"]] as const) {
    await s.getByRole("button", { name: button }).click();
    await expect(s.locator(".row.between .chip").first()).toHaveText(status);
  }
  await expect(s.getByRole("button", { name: "Cancel order" })).toHaveCount(0);
  await s.close();
});
