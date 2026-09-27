import { expect, test } from "@playwright/test";

const PASSWORD = "violet-otter-sings-at-dawn";

function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

test("register → sign in → dashboard → profile → sign out", async ({ page }) => {
  const email = uniqueEmail("ana");

  await page.goto("/register");
  await page.getByLabel("Name").fill("Ana");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Check your inbox" })).toBeVisible();

  await page.getByRole("link", { name: "Continue to sign in" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("Welcome, Ana.")).toBeVisible();
  // Real data from the API: FREE plan limits and unverified email.
  await expect(page.getByText("Backtests per day")).toBeVisible();
  await expect(page.getByText(`Verify ${email} to run backtests.`, { exact: false })).toBeVisible();
  // No fabricated results: empty states only.
  await expect(page.getByText("No backtests yet")).toBeVisible();

  await page.getByRole("link", { name: "Settings" }).click();
  await page.getByLabel("Display name").fill("Ana María");
  await page.getByRole("button", { name: "Save profile" }).click();
  await expect(page.getByText("Profile updated.")).toBeVisible();
  await expect(page.getByTestId("user-name")).toHaveText("Ana María");

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login/);

  // Protected pages redirect to login and come back after signing in.
  await page.goto("/settings");
  await expect(page).toHaveURL(/\/login\?next=%2Fsettings/);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/settings$/);
});

test("wrong credentials show a generic error", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill(uniqueEmail("nobody"));
  await page.getByLabel("Password").fill("definitely-not-the-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Invalid email or password" }),
  ).toBeVisible();
});

test("weak password is rejected with a field error", async ({ page }) => {
  await page.goto("/register");
  await page.getByLabel("Name").fill("Bob");
  await page.getByLabel("Email").fill(uniqueEmail("bob"));
  await page.getByLabel("Password").fill("short");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Password must be at least 12 characters long.")).toBeVisible();
});

test("open redirects via ?next are ignored", async ({ page }) => {
  const email = uniqueEmail("eve");
  await page.request.get("/api/v1/auth/csrf");
  const csrf = (await page.context().cookies()).find((c) => c.name === "axq_csrf")?.value ?? "";
  const registered = await page.request.post("/api/v1/auth/register", {
    headers: { "X-AxiomQ-CSRF": csrf },
    data: { email, password: PASSWORD, display_name: "Eve" },
  });
  expect(registered.status()).toBe(202);

  await page.goto("/login?next=//evil.example.com");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/localhost:\d+\/dashboard$/);
});
