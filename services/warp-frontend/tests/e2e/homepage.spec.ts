import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('loads successfully', async ({ page }) => {
    await page.goto('/');

    // Check page loads with correct title
    await expect(page).toHaveTitle(/Employa/i);
  });

  test('displays main heading', async ({ page }) => {
    await page.goto('/');

    // Check main heading is visible (spike page still shows old heading)
    await expect(
      page.getByRole('heading', { name: /Firebase Hosting.*Next\.js 15 SSR Spike/i })
    ).toBeVisible();
  });

  test('shows test results section', async ({ page }) => {
    await page.goto('/');

    // Check test results section exists
    await expect(page.getByText(/Test Results/i)).toBeVisible();
    await expect(page.getByText(/Server-Side Rendering/i)).toBeVisible();
    await expect(page.getByText(/Secret Manager Integration/i)).toBeVisible();
  });

  test('page is accessible', async ({ page }) => {
    await page.goto('/');

    // Basic accessibility checks
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toBeVisible();

    // Check for proper document structure
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });
});
