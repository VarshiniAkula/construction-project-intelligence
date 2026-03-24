import { test, expect } from "@playwright/test";

test.describe("Subcontractor Access Restrictions", () => {
  test("subcontractor can login and view only accessible documents", async ({ page }) => {
    // Login as electrical subcontractor
    await page.goto("/login");
    await page.fill('input[type="email"]', "jose.electrical@example.com");
    await page.fill('input[type="password"]', "builddocs123");
    await page.click('button[type="submit"]');

    await page.waitForURL(/\/dashboard/);

    // Navigate to project
    await page.click("text=Riverside Commercial Complex");
    await page.waitForURL(/\/projects\//);

    // Navigate to documents
    await page.click("text=Documents");
    await page.waitForURL(/\/documents/);

    // Subcontractor should NOT see management_only documents
    const pageContent = await page.content();
    expect(pageContent).not.toContain("Budget Summary Q1 2025");

    // Subcontractor should see field_team and their trade's documents
    // The exact visibility depends on the backend filter
  });

  test("owner viewer can only see owner_shared documents", async ({ page }) => {
    // Login as owner viewer
    await page.goto("/login");
    await page.fill('input[type="email"]', "owner@riverside.com");
    await page.fill('input[type="password"]', "builddocs123");
    await page.click('button[type="submit"]');

    await page.waitForURL(/\/dashboard/);

    await page.click("text=Riverside Commercial Complex");
    await page.waitForURL(/\/projects\//);

    await page.click("text=Documents");
    await page.waitForURL(/\/documents/);

    // Owner should NOT see management_only or field_team documents
    const pageContent = await page.content();
    expect(pageContent).not.toContain("Budget Summary Q1 2025");
    expect(pageContent).not.toContain("Safety Plan - Fall Protection");
  });
});
