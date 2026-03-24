import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  webServer: {
    command: "echo 'Assuming services are already running via docker compose'",
    port: 3000,
    reuseExistingServer: true,
  },
});
