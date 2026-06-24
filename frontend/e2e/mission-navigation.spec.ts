import { test, expect } from '@playwright/test'
const paths=['','/hosts','/actions','/findings','/bloodhound','/bloodhound/explorer']
test('demo mission navigation pages load', async ({ page, request }) => {
  const missions=await (await request.get('/api/missions')).json()
  const mission=missions.find((m:any)=>m.name==='Demo Windows AD Lab') || missions[0]
  expect(mission).toBeTruthy()
  for (const suffix of paths) {
    await page.goto(`/missions/${mission.id}${suffix}`)
    await expect(page.getByText(/OpenAD Zero|Demo Windows AD Lab|Hosts|Actions|Findings|BloodHound/i).first()).toBeVisible()
  }
})
