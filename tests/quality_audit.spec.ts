import { test, expect } from '@playwright/test';

test.describe('Search and Filter UX Quality Audit', () => {
  test.beforeEach(async ({ page }) => {
    // We assume the dev server is running on localhost:3000
    await page.goto('http://localhost:3000/');
  });

  test('Dropdowns should be visible and not clipped', async ({ page }) => {
    // Click on "Institución" dropdown
    const instBtn = page.getByRole('button', { name: /Institución/i });
    await instBtn.click();
    
    // Check if DMC is visible
    const dmcOption = page.getByRole('button', { name: /DMC/i });
    await expect(dmcOption).toBeVisible();
    
    // Verify it's not clipped (check if it's within viewport)
    const box = await dmcOption.boundingBox();
    expect(box).not.toBeNull();
    const viewportSize = page.viewportSize();
    if (box && viewportSize) {
      expect(box.y + box.height).toBeLessThanOrEqual(viewportSize.height);
      expect(box.x + box.width).toBeLessThanOrEqual(viewportSize.width);
    }
  });

  test('Cascading filters logic', async ({ page }) => {
    // Initially check count
    const initialResults = await page.locator('p:has-text("resultados encontrados")').innerText();
    const initialCount = parseInt(initialResults.split(' ')[0]);

    // Select Institution "DMC"
    await page.getByRole('button', { name: /Institución/i }).click();
    await page.getByRole('button', { name: /DMC/i }).click();

    // Results should decrease
    await expect(page.locator('p:has-text("resultados encontrados")')).not.toHaveText(initialResults);
    
    // Check if "Limpiar todo" is visible
    await expect(page.getByRole('button', { name: /Limpiar todo/i })).toBeVisible();
  });

  test('URL Persistence after navigation', async ({ page }) => {
    // Apply filter
    await page.getByRole('button', { name: /Institución/i }).click();
    await page.getByRole('button', { name: /DMC/i }).click();
    
    // Verify URL has param
    await expect(page).toHaveURL(/.*inst=DMC/);
    
    // Navigate to a course
    await page.locator('article a').first().click();
    await expect(page).toHaveURL(/.*\/courses\/.*/);
    
    // Go back
    await page.goBack();
    
    // Verify URL still has param and filter is active
    await expect(page).toHaveURL(/.*inst=DMC/);
    await expect(page.getByRole('button', { name: /DMC/i })).toBeVisible();
  });
});
