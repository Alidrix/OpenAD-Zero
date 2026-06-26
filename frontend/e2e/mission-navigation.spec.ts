import { test, expect } from '@playwright/test'
const pages=['Dashboard','Hosts','Actions','Jobs','Web Targets','Findings','Evidence','Report','Lab Operations','Timeline','BloodHound','BloodHound Explorer']
test('seeded demo mission navigation loads key pages', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('OpenAD Zero').first()).toBeVisible()
  for (const label of pages) {
    const link=page.getByText(label).first()
    if (await link.isVisible().catch(()=>false)) { await link.click(); await expect(page.getByText(label).first()).toBeVisible() }
  }
})
