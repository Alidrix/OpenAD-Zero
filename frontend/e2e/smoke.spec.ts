import { test, expect } from '@playwright/test'
test('home, settings and capabilities load', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('OpenAD Zero').first()).toBeVisible()
  await page.getByRole('link', { name: /settings/i }).click()
  await expect(page.getByText(/settings|system/i).first()).toBeVisible()
  await page.getByRole('link', { name: /capabilities/i }).click()
  await expect(page.getByText(/capabilities/i).first()).toBeVisible()
})
