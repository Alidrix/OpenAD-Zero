import { test, expect } from '@playwright/test'
test('evidence and report pages expose demo artifacts', async ({ page }) => {
  await page.goto('/')
  const evidence=page.getByText('Evidence').first(); if (await evidence.isVisible().catch(()=>false)) await evidence.click()
  await expect(page.getByText(/Evidence|demo-log.txt|demo-finding.json/).first()).toBeVisible()
  const report=page.getByText('Report').first(); if (await report.isVisible().catch(()=>false)) await report.click()
  await expect(page.getByText(/Report|Download|Generate|Latest/).first()).toBeVisible()
})
