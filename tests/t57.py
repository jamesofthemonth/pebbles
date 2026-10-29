import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
INIT2=INIT.replace("localStorage.setItem('pebble-planner-v1-demo','1')","localStorage.removeItem('pebble-planner-v1-demo')")
srv=subprocess.Popen(['python3','-m','http.server','8785','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch()
  # 1: someone with the old example plan saved gets a clean slate
  ctx=await b.new_context(viewport={'width':1280,'height':900});pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8785/tests/app.html');await pg.wait_for_timeout(1300);await pg.locator('#adds .chip[data-kind="break"]').click();await pg.wait_for_timeout(1500)
  st=await S.state(pg);print('demo state example:',st.get('example'),len(st['groups']))
  await pg.evaluate("localStorage.removeItem('pebble-planner-v1-demo')")
  pg2=await ctx.new_page();await pg2.add_init_script(INIT2);pg2.on('pageerror',lambda e:S.errs.append(str(e)));await pg.close()
  await pg2.goto('http://127.0.0.1:8785/tests/app.html');await pg2.wait_for_timeout(2500)
  st=await S.state(pg2);S.check(len(st['groups'])==0 and len(st['pebbles'])==0 and not st['example'],'old example plan is cleared to a fresh start',(len(st['groups']),len(st['pebbles'])))
  acts=[p['name'] for p in st['projects'].values()];S.check(len(acts)==10 and all(p['kind']!='work' for p in st['projects'].values()),'only break and exercise activities remain',acts)
  m=json.loads(await pg2.evaluate("localStorage.getItem('__mdb')"));rs=m['data/users/james/state']['state'];S.check(len(rs['groups'])==0,'the synced copy is cleared too',len(rs['groups']))
  await pg2.screenshot(path=os.path.join(ROOT,'tests','shots','fresh.png'))
  # build from nothing: new channel, new project via chip, pebble
  await pg2.locator('#adds [data-addm]').click();await pg2.wait_for_timeout(500);await pg2.keyboard.type('TARRMACstudio');await pg2.keyboard.press('Enter');await pg2.wait_for_timeout(300)
  await pg2.click('#docClose');await pg2.wait_for_timeout(300);await pg2.locator('#adds .chip[data-gid]').first.click();await pg2.wait_for_timeout(500);await pg2.locator('.chippop button.nw').click();await pg2.wait_for_timeout(400)
  await pg2.fill('#pkFind','Kalorama EOI 90m');await pg2.press('#pkFind','Enter');await pg2.wait_for_timeout(600)
  st=await S.state(pg2);S.check(len(st['groups'])==1 and len(st['pebbles'])==1 and st['pebbles'][0]['dur']==90,'from empty: add a channel, then a 90 min project pebble',(st['groups'],[(p['dur'],st['projects'][p['pid']]['name']) for p in st['pebbles']]))
  await pg2.keyboard.press('n');await pg2.wait_for_timeout(500);S.check(await pg2.locator('#pkFind').count()==1,'N works with one channel')
  S.check(not S.errs,'no errors',S.errs[:3]);await b.close()
asyncio.run(main());srv.terminate()
