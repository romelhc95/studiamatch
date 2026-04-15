import { test, expect } from '@playwright/test';

test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE size

test('Hero section scaling', async ({ page }) => {
  await page.goto('http://localhost:3000/');
  
  const heroTitle = page.locator('h1');
  await expect(heroTitle).toBeVisible();
  
  // Check font size on mobile (should be text-3xl, approx 30px)
  const fontSize = await heroTitle.evaluate((el) => window.getComputedStyle(el).fontSize);
  console.log(`Hero Font Size: ${fontSize}`);
  
  // Ensure it doesn't overflow horizontally
  const boundingBox = await heroTitle.boundingBox();
  const viewportWidth = page.viewportSize()?.width || 0;
  expect(boundingBox?.width).toBeLessThanOrEqual(viewportWidth);
});

test('Smart filters (Accordions) mobile behavior', async ({ page }) => {
  await page.goto('http://localhost:3000/');
  
  // Open filters
  const showFiltersBtn = page.getByRole('button', { name: /Mostrar Filtros/i });
  await showFiltersBtn.click();
  
  // Check if first accordion is expanded
  const areaFilter = page.getByText('Área / Tema', { exact: false });
  await expect(areaFilter).toBeVisible();
  
  // Check for empty options (should not be visible if stats logic works)
  // We can't easily check "what's not there" without knowing the DB state, 
  // but we can check if the ones that are there have counts > 0.
  const counts = page.locator('span.text-\\[9px\\]');
  const countTexts = await counts.allTextContents();
  for (const text of countTexts) {
    expect(parseInt(text)).toBeGreaterThan(0);
  }
});

test('Course detail page responsiveness', async ({ page }) => {
  // Navigate to first course available
  await page.goto('http://localhost:3000/');
  const firstCourseLink = page.locator('article h3').first();
  await firstCourseLink.click();
  
  // Check Tabs
  const tabsContainer = page.locator('.flex.items-center.gap-4.bg-slate-100');
  await expect(tabsContainer).toBeVisible();
  
  // Check if tabs are wrapped (stacked) or scrollable
  const isWrapped = await tabsContainer.evaluate((el) => window.getComputedStyle(el).flexWrap === 'wrap');
  console.log(`Tabs are wrapped: ${isWrapped}`);
  
  // Check Brochure vs Leads form
  const brochureBtn = page.getByText(/Descargar Brochure/i);
  const leadForm = page.locator('form').first();
  
  if (await brochureBtn.isVisible()) {
    const brochureBox = await brochureBtn.boundingBox();
    const formBox = await leadForm.boundingBox();
    
    // On mobile, they should be in a vertical flow, not overlapping
    if (brochureBox && formBox) {
       expect(Math.abs(brochureBox.y - formBox.y)).toBeGreaterThan(100); 
    }
  }
  
  // Check Opportunity Banner
  const banner = page.locator('.bg-amber-50');
  if (await banner.isVisible()) {
    const bannerBox = await banner.boundingBox();
    console.log(`Banner height: ${bannerBox?.height}`);
    expect(bannerBox?.height).toBeLessThan(150); // Should be compact
  }
});
