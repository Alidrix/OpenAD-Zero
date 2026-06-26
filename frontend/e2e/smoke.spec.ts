import { test, expect } from '@playwright/test'
test('home page, settings and capabilities are accessible', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('OpenAD Zero').first()).toBeVisible()
  await expect(page.getByRole('navigation').or(page.getByText('Settings').first())).toBeVisible()
  await page.getByText('Settings').first().click(); await expect(page).toHaveURL(/settings/)
  await page.getByText('Capabilities').first().click(); await expect(page).toHaveURL(/capabilities/)
})
