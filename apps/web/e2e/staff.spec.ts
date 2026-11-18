import { expect, test } from "@playwright/test";

test("an unsigned visit opens the sign-in page", async ({ page }) => {
  await page.goto("/overview");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("a reader can open the overview", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Work email").fill("reader@ngreen.demo");
  await page.getByLabel("Password").fill("demo-pass");
  await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
  await expect(page.getByText("live calling disabled")).toBeVisible();
});
