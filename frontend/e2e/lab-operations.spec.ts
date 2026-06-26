import { test, expect } from '@playwright/test'
test('lab operations shows progress, phases and timeline', async ({ page }) => {
  await page.goto('/')
  const lab=page.getByText('Lab Operations').first(); if (await lab.isVisible().catch(()=>false)) await lab.click()
  for (const text of [/Progress|score/i,/Phase|Scope validation/i,/Timeline|mission/i,/Sync operations|Sync/i]) {
    await expect(page.getByText(text).first()).toBeVisible()
  }
})
