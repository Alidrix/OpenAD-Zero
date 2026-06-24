import { expect, Page } from '@playwright/test'
export async function openDemoMission(page: Page) {
  await page.goto('/')
  const demo = page.getByText('Demo Windows AD Lab').first()
  if (await demo.count()) await demo.click()
  else await page.goto('/missions/new')
}
export async function expectText(page: Page, text: string | RegExp) { await expect(page.getByText(text).first()).toBeVisible({ timeout: 15000 }) }
