import { expect, test } from '@playwright/test'

import { mockApi } from './helpers'

test('home page exposes the main navigation', async ({ page }) => {
  await mockApi(page)
    await page.goto('/')

  await expect(page.getByText('OpenAD Zero', { exact: true }).first()).toBeVisible()
  await expect(page.getByRole('link', { name: /nouvelle mission/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /capabilities/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /settings/i })).toBeVisible()
})
