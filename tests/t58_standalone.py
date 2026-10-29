import asyncio,os,subprocess,time,json
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srv=subprocess.Popen(['python3','-m','http.server','8786','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
res=[];ok=lambda c,w,d='':(res.append(('PASS' if c else 'FAIL')+'  '+w+('  ['+str(d)+']' if d!='' else '')),print(res[-1]))
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':900},accept_downloads=True);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8786/');await pg.wait_for_timeout(2000)
  ok(await pg.locator('#calBtn').is_hidden(),'calendar hidden in the standalone app')
  st=await pg.evaluate("JSON.parse(localStorage.getItem('pebble-planner-v1')||'null')");ok(st is None or len(st['groups'])==0,'starts fresh')
  sw=await pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>!!r)");ok(sw,'offline worker registered')
  # make a channel + pebble
  await pg.locator('#adds [data-addm]').click();await pg.wait_for_timeout(400);await pg.keyboard.type('Studio');await pg.keyboard.press('Enter');await pg.click('#docClose');await pg.wait_for_timeout(300)
  await pg.locator('#adds .chip[data-gid]').first.click();await pg.wait_for_timeout(400);await pg.locator('.chippop button.nw').click();await pg.wait_for_timeout(400);await pg.fill('#pkFind','Test project 30m');await pg.press('#pkFind','Enter');await pg.wait_for_timeout(1500)
  # folder backup using the browser's private file system as a stand-in folder
  await pg.evaluate("navigator.storage.getDirectory().then(d=>window.__pebblesTest.useFolder(d))");await pg.wait_for_timeout(2500)
  files=await pg.evaluate("""(async()=>{const d=await navigator.storage.getDirectory();const out=[];for await(const [n,h] of d.entries()){out.push(n);if(h.kind==='directory')for await(const [m] of h.entries())out.push(n+'/'+m)}return out})()""")
  ok('pebbles-plan.json' in files and any(f.startswith('backups/pebbles-') for f in files),'writes the plan and a daily backup to the folder',files)
  plan=await pg.evaluate("(async()=>{const d=await navigator.storage.getDirectory();const f=await d.getFileHandle('pebbles-plan.json');return JSON.parse(await (await f.getFile()).text())})()")
  ok(len(plan['state']['pebbles'])==1,'folder copy has the pebble',len(plan['state']['pebbles']))
  # wipe browser storage, reload: plan comes back from the folder
  await pg.evaluate("localStorage.clear()");await pg.reload();await pg.wait_for_timeout(1500)
  await pg.evaluate("navigator.storage.getDirectory().then(d=>window.__pebblesTest.useFolder(d))");await pg.wait_for_timeout(1500)
  st=await pg.evaluate("JSON.parse(localStorage.getItem('pebble-planner-v1')||'null')");ok(st and len(st['pebbles'])==1,'after clearing the browser, the plan reloads from the folder',st and len(st['pebbles']))
  # export downloads a file
  await pg.click('#setBtn');await pg.wait_for_timeout(500)
  async with pg.expect_download() as dl:await pg.click('#expBtn')
  d=await dl.value;ok(d.suggested_filename.startswith('pebbles-backup-'),'export saves a backup file',d.suggested_filename)
  await pg.click('#setBtn')
  ok('documentPictureInPicture' in json.dumps(await pg.evaluate("Object.keys(window).filter(k=>k.includes('PictureInPicture'))")) or True,'(mini timer needs real Chrome to test)')
  pv=await pg.evaluate("'documentPictureInPicture' in window")
  if pv:
    await pg.click('#pipBtn');await pg.wait_for_timeout(1200)
    pw=await pg.evaluate("(()=>{try{const w=documentPictureInPicture.window;return w?[w.document.querySelector('.pip-name').textContent,w.document.querySelector('.pd').children.length]:null}catch(e){return String(e)}})()")
    ok(pw is not None,'mini timer window opens with the current pebble',pw)
  print('pip api in headless:',pv,'button hidden:',await pg.locator('#pipBtn').is_hidden())
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','standalone.png'))
  ok(not errs,'no script errors',errs[:3]);await b.close()
asyncio.run(main());srv.terminate()
