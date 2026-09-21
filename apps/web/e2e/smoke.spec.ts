import { test, expect } from '@playwright/test';

test.describe('PGCB Portal Critical User Journeys', () => {
  
  test('Homepage loads and displays Bangla-first content', async ({ page }) => {
    await page.goto('/');
    
    // Check main branding
    await expect(page.locator('h1')).toContainText('পাওয়ার গ্রিড প্রকৌশলী সমিতি');
    
    // Check CTA presence
    const registerBtn = page.getByRole('link', { name: /সদস্যপদ আবেদন/ });
    await expect(registerBtn).toBeVisible();
  });

  test('Public certificate verification handles invalid tokens', async ({ page }) => {
    await page.goto('/certificate/invalid-token-123');
    
    // Should show error state
    await expect(page.getByText('সনদপত্রটি খুঁজে পাওয়া যায়নি')).toBeVisible();
  });

  test('Circular directory filters correctly', async ({ page }) => {
    await page.goto('/circulars');
    
    // Wait for the CSR to fetch (or SSR to load)
    await page.waitForLoadState('networkidle');
    
    // Click the "Office Order" filter
    await page.getByRole('button', { name: 'অফিস আদেশ' }).click();
    
    // The active filter should update the URL or UI state
    await expect(page.getByRole('button', { name: 'অফিস আদেশ' })).toHaveClass(/bg-primary/);
  });
});
