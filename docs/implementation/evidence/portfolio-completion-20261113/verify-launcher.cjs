const { chromium } = require(process.cwd() + '/node_modules/playwright');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({viewport:{width:1440,height:900}});
    const errors=[]; page.on('pageerror', error=>errors.push(error.message));
    const credentials=JSON.parse(fs.readFileSync(process.env.CADRISYN_E2E_FIXTURE_DIR+'/credentials.json','utf8'));
    const health=await page.request.get('http://127.0.0.1:8002/health/');
    if(health.status()!==200) throw Error('API health failed');
    await page.goto('http://127.0.0.1:3001/sign-in');
    await page.getByLabel('Username',{exact:true}).fill(credentials.username);
    await page.getByLabel('Password',{exact:true}).fill(credentials.password);
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.waitForURL(/\/app\/markets\/?$/);
    await page.getByRole('region',{name:'Historical price',exact:true}).waitFor();
    const session=await page.request.get('http://127.0.0.1:3001/api/v1/session/');
    const watchlist=await page.request.get('http://127.0.0.1:3001/api/v1/watchlist/');
    if(session.status()!==200 || !(await session.json()).authenticated || watchlist.status()!==200) throw Error('Authenticated integration failed');
    await page.screenshot({path:process.env.CADRISYN_E2E_FIXTURE_DIR+'/launcher-markets-1440.png',fullPage:true});
    await page.getByRole('link',{name:'Research',exact:true}).first().click();
    await page.getByRole('heading',{name:'Exploratory research',exact:true}).waitFor();
    await page.screenshot({path:process.env.CADRISYN_E2E_FIXTURE_DIR+'/launcher-research-1440.png',fullPage:true});
    if(errors.length) throw Error(errors.join('\n'));
    console.log(JSON.stringify({result:'PASS',api_health:health.status(),session:session.status(),watchlist:watchlist.status(),authenticated:true,research_visible:true,page_errors:errors,frontend:'http://127.0.0.1:3001',api:'http://127.0.0.1:8002'}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
