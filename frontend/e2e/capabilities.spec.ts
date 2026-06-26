import { test, expect } from '@playwright/test'
test('capabilities page lists implemented platform and QA capabilities', async ({ page }) => {
  await page.goto('/capabilities')
  for (const text of ['Nmap','NetExec','Nuclei','BloodHound','Evidence Manager','Reporting Engine','Worker Queue','Alembic migrations']) {
    await expect(page.getByText(text).first()).toBeVisible()
  }
})
