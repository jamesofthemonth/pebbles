# Updates: a new sw.js version shows an update button; clicking it loads the new version, plan kept.
import asyncio,os,subprocess,time,json,re,shutil,tempfile
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP=tempfile.mkdtemp();shutil.copytree(ROOT,TMP+'/app',ignore=shutil.ignore_patterns('.git','tests'));APP=TMP+'/app'
srv=subprocess.Popen(['python3','-m','http.server','8789','--bind','127.0.0.1'],cwd=APP,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
res=[];ok=lambda c,w,d='':(res.append(('PASS' if c else 'FAIL')+'  '+w+('  ['+str(d)+']' if d!='' else '')),print(res[-1]))
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':900});pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8789/');await pg.wait_for_timeout(2500)
  await pg.reload();await pg.wait_for_timeout(1500)
  ok(await pg.evaluate("!!navigator.serviceWorker.controller"),'offline worker in control')
  await pg.locator('#adds [data-addm]').click();await pg.wait_for_timeout(400);await pg.keyboard.type('Studio');await pg.keyboard.press('Enter');await pg.click('#docClose');await pg.wait_for_timeout(300)
  await pg.locator('#adds .chip[data-gid]').first.click();await pg.wait_for_timeout(400);await pg.fill('#pkFind','Keep me 30m');await pg.press('#pkFind','Enter');await pg.wait_for_timeout(800)
  # publish a "new version": change index.html marker + sw version
  h=open(APP+'/index.html').read().replace('</body>','<i id="newver"></i></body>');open(APP+'/index.html','w').write(h)
  w=open(APP+'/sw.js').read();w=re.sub(r"const VERSION='[^']*'","const VERSION='pebbles-test-next'",w);open(APP+'/sw.js','w').write(w)
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#updBtn');await pg.wait_for_timeout(3000)
  ok(await pg.locator('#newver').count()==0,'does not reload by itself')
  ok(await pg.locator('#updNow').is_visible(),'update button appears at the top')
  await pg.click('#setBtn');await pg.evaluate('scrollTo(0,0)');await pg.wait_for_timeout(500)
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','update_button.png'),clip={'x':0,'y':0,'width':1280,'height':120})
  await pg.click('#updNow');await pg.wait_for_timeout(2500)
  ok(await pg.locator('#newver').count()==1,'clicking it loads the new version')
  ok(await pg.locator('#updNow').is_hidden(),'button gone after updating')
  st=await pg.evaluate("JSON.parse(localStorage.getItem('pebble-planner-v1'))")
  ok(any(p.get('pid') and st['projects'][p['pid']]['name'].startswith('Keep me') for p in st['pebbles']),'plan kept through the update')
  ok(await pg.evaluate("caches.keys()")==['pebbles-test-next'] or 'pebbles-test-next' in await pg.evaluate("caches.keys()"),'old cache replaced',await pg.evaluate("caches.keys()"))
  ok(not errs,'no script errors',errs[:3]);await b.close()
asyncio.run(main());srv.terminate();shutil.rmtree(TMP)
print('\nFAILS',sum(r.startswith('FAIL') for r in res))
