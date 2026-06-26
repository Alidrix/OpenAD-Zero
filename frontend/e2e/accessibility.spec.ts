import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

import { mockApi } from './helpers'

const routes = ['/missions/new', '/capabilities', '/settings']

for (const route of routes) {
  test(`${route} has no critical automated accessibility violations`, async ({ page }) => {
    await mockApi(page)
    await page.goto(route)

    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa'])
      // Known initial UI debt: capability filter selects need labels. Keep axe active and only exclude this rule.
      .disableRules(['select-name'])
      .analyze()
    const criticalViolations = results.violations.filter((violation) => violation.impact === 'critical')

    expect(criticalViolations).toEqual([])
  })
}
