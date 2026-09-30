import { defineConfig, devices } from "@playwright/test";

// Expects the API (seeded with `python -m app.seed --reset`) and the web app to be running; see README "Testing".
export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  retries: process.env.CI ? 1 : 0,
  workers: 1,  // tests share one seeded database
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] }, testIgnore: /responsive\.spec\.ts/ },
    { name: "mobile", use: { ...devices["Pixel 7"] }, testMatch: /responsive\.spec\.ts/ },
  ],
});
