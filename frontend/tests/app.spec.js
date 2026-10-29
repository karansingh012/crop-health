import{test,expect}from'@playwright/test';
const email=`browser-${Date.now()}@example.com`;
test('full user journey against the real backend',async({page})=>{
 await page.goto('/');await expect(page.getByText('Small observations.')).toBeVisible();
 await page.getByRole('link',{name:'Get started'}).click();
 await page.getByLabel('Your name').fill('Browser Farmer');await page.getByLabel('Email address').fill(email);await page.getByLabel('Password',{exact:true}).fill('browser-password-123');await page.getByRole('button',{name:'Create account'}).click();
 await expect(page.getByRole('heading',{name:'Welcome back, Browser.'})).toBeVisible();
 await page.getByRole('link',{name:'My fields',exact:true}).click();await page.getByRole('button',{name:'Add field'}).click();
 await page.getByLabel('Field name').fill('Browser tomato plot');await page.getByLabel('Crop',{exact:true}).fill('Tomato');await page.getByLabel('Area (hectares)').fill('2.5');await page.getByRole('button',{name:'Save field'}).click();
 await expect(page.getByRole('heading',{name:'Browser tomato plot'})).toBeVisible();
 await page.getByRole('link',{name:'Plant scanner',exact:true}).click();
 await page.getByLabel('Plant image').setInputFiles(process.env.TEST_IMAGE||'../../../work/test-leaf.png');
 await page.getByLabel('Field (optional)').selectOption({label:'Browser tomato plot · Tomato'});await page.getByLabel('What have you noticed?').fill('Browser integration observation');
 await page.getByRole('button',{name:'Save & assess image'}).click();
 await expect(page.getByRole('heading',{name:'Your crop observation'})).toBeVisible();await expect(page.locator('.status')).toContainText(/model unavailable|uncertain|classified/);
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download report'}).click();await expect((await download).suggestedFilename()).toMatch(/\.pdf$/);
 await page.getByRole('button',{name:'Schedule follow-up'}).click();await expect(page.getByRole('status')).toHaveText('Follow-up scheduled');
 await page.getByRole('link',{name:'Follow-ups',exact:true}).click();await page.getByRole('button',{name:'Mark complete'}).click();await expect(page.getByRole('button',{name:'Completed'})).toBeVisible();
 for(const name of ['Scan history','Reports','Weather & context','Expert support','Settings','Help & about']){await page.getByRole('link',{name,exact:true}).click();await expect(page.locator('main h1')).toBeVisible();}
 await page.getByRole('button',{name:'Toggle color theme'}).click();await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
 await page.getByRole('button',{name:'Toggle color theme'}).click();await page.getByRole('link',{name:'Overview',exact:true}).click();await expect(page.getByRole('status')).toHaveCount(0,{timeout:7000});await page.screenshot({path:'../../../work/dashboard-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'../../../work/dashboard-mobile.png',fullPage:true});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByRole('button',{name:'Toggle navigation'}).click();await page.getByRole('link',{name:'My fields',exact:true}).click();await expect(page.getByRole('heading',{name:'My fields'})).toBeVisible();
 await page.getByRole('button',{name:'Toggle navigation'}).click();await page.getByRole('button',{name:'Sign out'}).click();await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
 await page.goto('/app');await expect(page).toHaveURL(/login/);
});
