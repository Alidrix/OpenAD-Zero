import type { Page } from '@playwright/test'

export async function mockApi(page: Page) {
  await page.route('**/api/capabilities/config', async (route) => {
    await route.fulfill({ json: { capabilities_enabled: true, safe_mode: true } })
  })
  await page.route('**/api/capabilities', async (route) => {
    await route.fulfill({
      json: [
        {
          id: 'quality_gate',
          name: 'Quality Gate',
          category: 'qa',
          status: 'implemented',
          mode: 'safe',
          risk_level: 1,
          requires_approval: false,
          execution: 'none',
          description: 'Backend lint, tests, frontend build, smoke tests and E2E checks.',
          evidence: false,
        },
      ],
    })
  })
  await page.route('**/api/health**', async (route) => {
    await route.fulfill({ json: { status: 'ok', service: 'openadzero' } })
  })
}
