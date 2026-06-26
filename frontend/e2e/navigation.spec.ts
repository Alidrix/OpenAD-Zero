import { expect, test } from '@playwright/test'

import { mockApi } from './helpers'

const routes = [
  { path: '/missions/new', heading: /nouvelle mission|mission/i },
  { path: '/capabilities', heading: /capabilities/i },
  { path: '/settings', heading: /settings/i },
]

for (const route of routes) {
  test(`${route.path} loads without starting a scan`, async ({ page }) => {
    await mockApi(page)
    await page.goto(route.path)

    await expect(page.locator('body')).toContainText(route.heading)
    await expect(page.getByText('OpenAD Zero', { exact: true }).first()).toBeVisible()
  })
}
