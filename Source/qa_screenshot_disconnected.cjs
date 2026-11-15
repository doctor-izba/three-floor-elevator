const {chromium}=require(process.env.ELEVATOR_PLAYWRIGHT_MODULE||'playwright');
const path=require('path');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1100},deviceScaleFactor:3});
 const page=await context.newPage();
 await page.goto('http://127.0.0.1:1888/dashboard/elevator');
 await page.getByRole('heading',{name:'Three floor elevator',exact:true}).waitFor();
 await page.locator('.sim-label').filter({hasText:'PLC DISCONNECTED'}).waitFor();
 await page.screenshot({path:path.join(__dirname,'qa/connected_disconnected.png'),fullPage:true});
 await browser.close();console.log('Captured actual disconnected HMI at 3x device pixel ratio');
})().catch(e=>{console.error(e);process.exit(1)});
