import { test, expect } from '@playwright/test'
test('lab operations shows progress phases timeline and sync', async ({ page, request }) => {
  const missions=await (await request.get('/api/missions')).json(); const mission=missions.find((m:any)=>m.name==='Demo Windows AD Lab') || missions[0]; expect(mission).toBeTruthy()
  await page.goto(`/missions/${mission.id}/lab`)
  for (const text of [/progress/i,/phase/i,/timeline/i,/sync/i]) await expect(page.getByText(text).first()).toBeVisible()
})
