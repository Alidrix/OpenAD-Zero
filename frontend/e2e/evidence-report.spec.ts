import { test, expect } from '@playwright/test'
test('evidence and report pages load for seeded mission', async ({ page, request }) => {
  const missions=await (await request.get('/api/missions')).json(); const mission=missions.find((m:any)=>m.name==='Demo Windows AD Lab') || missions[0]; expect(mission).toBeTruthy()
  await page.goto(`/missions/${mission.id}/evidence`); await expect(page.getByText(/Evidence|Demo/i).first()).toBeVisible()
  await page.goto(`/missions/${mission.id}/report`); await expect(page.getByText(/Generate|Latest|Report/i).first()).toBeVisible()
})
