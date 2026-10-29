import{test,expect}from'@playwright/test';
async function signup(page){await page.goto('/register');await page.getByLabel('Your name').fill('Hindi Test');await page.getByLabel('Email address').fill(`hindi-${Date.now()}@example.com`);await page.getByLabel('Password',{exact:true}).fill('multilingual-password-123');await page.getByRole('button',{name:'Create account'}).click();await expect(page).toHaveURL(/\/app$/);}
test('Hindi persists across routes and reload; place weather and Hindi PDF work',async({page})=>{
 await signup(page);await page.getByLabel('Language / भाषा').selectOption('hi');await expect(page.locator('html')).toHaveAttribute('lang','hi');await expect(page.getByRole('heading',{name:'फिर से स्वागत है, Hindi।'})).toBeVisible();
 await page.reload();await expect(page.getByRole('heading',{name:'फिर से स्वागत है, Hindi।'})).toBeVisible();
 for(const [name,title] of [['मेरे खेत','मेरे खेत'],['जाँच का इतिहास','जाँच का इतिहास'],['रिपोर्ट','रिपोर्ट'],['दोबारा जाँच','दोबारा जाँच की निगरानी'],['विशेषज्ञ सहायता','विशेषज्ञ सहायता'],['सेटिंग्स','प्रोफ़ाइल और सेटिंग्स'],['सहायता और जानकारी','सहायता और जानकारी']]){await page.getByRole('link',{name,exact:true}).click();await expect(page.locator('main h1')).toHaveText(title);}
 await page.getByRole('link',{name:'मौसम और परिस्थितियाँ',exact:true}).click();await expect(page.getByLabel('Latitude',{exact:true})).toHaveCount(0);await expect(page.getByLabel('Longitude',{exact:true})).toHaveCount(0);
 await page.getByLabel('शहर, गाँव या पिन कोड').fill('Lucknow');await page.getByRole('button',{name:'स्थान खोजें',exact:true}).click();await expect(page.getByRole('heading',{name:'अपना स्थान चुनें'})).toBeVisible({timeout:20000});await page.locator('.place-choice').first().click();await expect(page.getByRole('heading',{name:'परिस्थितियों की जानकारी'})).toBeVisible({timeout:20000});await expect(page.getByText('तापमान',{exact:true})).toBeVisible();
 await page.screenshot({path:'../../../work/hindi-weather.png',fullPage:true});
 await page.getByRole('link',{name:'पौधे की जाँच',exact:true}).click();await page.getByLabel('पौधे की तस्वीर',{exact:true}).setInputFiles(process.env.TEST_IMAGE||'../../../work/test-leaf.png');await page.getByLabel('आपने क्या देखा?').fill('पत्तियों पर धब्बे दिखाई दिए।');await page.getByRole('button',{name:'तस्वीर सहेजें और आकलन करें'}).click();await expect(page.getByRole('heading',{name:'आपकी फसल का निरीक्षण'})).toBeVisible({timeout:20000});
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'रिपोर्ट डाउनलोड करें'}).click();await(await download).saveAs('../../../work/hindi-browser-report.pdf');
 await page.screenshot({path:'../../../work/hindi-result.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../../work/hindi-mobile.png',fullPage:true});
 await page.getByLabel('Language / भाषा').selectOption('en');await expect(page.getByRole('heading',{name:'Your crop observation'})).toBeVisible();await expect(page.getByText('पत्तियों पर धब्बे दिखाई दिए।')).toBeVisible();
});
test('device location requests weather and denied permission offers search',async({page,context})=>{
 await signup(page);await page.getByRole('link',{name:'Weather & context',exact:true}).click();
 await context.grantPermissions(['geolocation']);await context.setGeolocation({latitude:26.84,longitude:80.94});await page.getByRole('button',{name:'Use my location'}).click();await expect(page.getByRole('heading',{name:'Conditions in context'})).toBeVisible({timeout:20000});
 await context.clearPermissions();await page.addInitScript(()=>{navigator.geolocation.getCurrentPosition=(_ok,fail)=>fail({code:1})});await page.reload();await page.getByRole('button',{name:'Use my location'}).click();await expect(page.getByRole('alert')).toContainText('Location permission was denied');
});
