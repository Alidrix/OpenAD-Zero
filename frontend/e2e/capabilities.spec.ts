import { test, expect } from '@playwright/test'
test('capabilities page lists core capabilities', async ({ page }) => {
  await page.goto('/capabilities')
  for (const name of [/Nmap/i,/NetExec/i,/Nuclei/i,/BloodHound/i,/Report/i,/Worker|Queue/i]) await expect(page.getByText(name).first()).toBeVisible()
})
