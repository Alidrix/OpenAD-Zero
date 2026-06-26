import { expect, type Page } from '@playwright/test'
export async function openDemoMission(page: Page) {
  await page.goto('/')
  await expect(page.getByText('OpenAD Zero').first()).toBeVisible()
  const demo = page.getByText('Demo Windows AD Lab').first()
  if (await demo.isVisible().catch(() => false)) await demo.click()
}
export async function expectText(page: Page, text: string | RegExp) {
  await expect(page.getByText(text).first()).toBeVisible()
}
