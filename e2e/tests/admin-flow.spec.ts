import { test, expect } from "@playwright/test";

test.describe("Admin E2E Flow", () => {
  test("admin can login, view project, see documents, and open chat", async ({ page }) => {
    // Login
    await page.goto("/login");
    await page.fill('input[type="email"]', "admin@builddocs.ai");
    await page.fill('input[type="password"]', "builddocs123");
    await page.click('button[type="submit"]');

    // Wait for dashboard
    await page.waitForURL(/\/dashboard/);
    await expect(page.locator("text=Projects")).toBeVisible();

    // Click on the demo project
    await page.click("text=Riverside Commercial Complex");
    await page.waitForURL(/\/projects\//);

    // Navigate to documents
    await page.click("text=Documents");
    await page.waitForURL(/\/documents/);

    // Should see documents in the library
    await expect(page.locator("table")).toBeVisible();

    // Navigate to chat
    await page.goto(page.url().replace("/documents", "/chat"));
    await page.waitForURL(/\/chat/);

    // Should see chat interface
    await expect(page.locator("text=Ask your project documents")).toBeVisible();

    // Create a new chat and send a message
    await page.click("text=New Chat");
    await page.fill('input[placeholder*="Ask about"]', "What documents are in this project?");
    await page.click('button:has(svg)'); // Send button

    // Wait for response (may timeout if AI services are not running)
    // In CI, we just verify the UI is functional
    await page.waitForTimeout(2000);
  });

  test("admin can navigate to members page", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "admin@builddocs.ai");
    await page.fill('input[type="password"]', "builddocs123");
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);

    await page.click("text=Riverside Commercial Complex");
    await page.waitForURL(/\/projects\//);

    await page.click("text=Team Members");
    await page.waitForURL(/\/members/);

    // Should see member table
    await expect(page.locator("text=Alex Chen")).toBeVisible();
    await expect(page.locator("text=Sarah Martinez")).toBeVisible();
  });

  test("admin can navigate to audit log", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', "admin@builddocs.ai");
    await page.fill('input[type="password"]', "builddocs123");
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard/);

    await page.click("text=Riverside Commercial Complex");
    await page.click("text=Audit Log");
    await page.waitForURL(/\/audit/);

    await expect(page.locator("text=Audit Log")).toBeVisible();
  });
});
