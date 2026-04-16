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
  
  // Open filters (Updated selector to match "Filtros")
  const showFiltersBtn = page.getByRole('button', { name: /Filtros/i });
  await showFiltersBtn.click();
  
  // Check if first accordion is expanded (Updated to match "Área")
  const areaFilter = page.getByText('Área', { exact: true });
  await expect(areaFilter).toBeVisible();
});

test('Course detail page responsiveness', async ({ page }) => {
  await page.goto('http://localhost:3000/');
  
  // Wait for courses to load
  await page.waitForSelector('article h3');
  
  const firstCourseLink = page.locator('article h3').first();
  await firstCourseLink.click();
  
  // Check Tabs (Updated to match "GENERAL")
  const generalTab = page.getByText(/GENERAL/i);
  await expect(generalTab).toBeVisible();
  
  // Check ROI Section (Updated selector to match the dark background section)
  const roiSection = page.locator('section.bg-\\[\\#0A0F1C\\]');
  await expect(roiSection).toBeVisible();
  
  // Check Leads form
  const leadForm = page.locator('form').first();
  await expect(leadForm).toBeVisible();
});
