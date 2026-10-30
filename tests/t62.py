# Drops fit the gap, drags snap to the timeline's 5-minute marks, phase colour in the tab/taskbar icon.
import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8790','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
SET="""(st=>{st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));localStorage.removeItem('pebble-planner-v1-base');const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})"""
D='2026-11-02'
async def setup(pg,pebs):
  await pg.evaluate("""(pebs=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const g=st.groups[0].id;
    st.projects.pa={id:'pa',kind:'work',name:'Alpha',group:g,tasks:[]};st.projects.pb={id:'pb',kind:'work',name:'Beta',group:g,tasks:[]};st.projects.pc={id:'pc',kind:'work',name:'Gamma',group:g,tasks:[]};
    st.pebbles=pebs;("""+SET+""")(st)})""",pebs);await pg.reload();await pg.wait_for_timeout(1300)
def mine(st):return sorted([(p['id'],p['start'],p['dur']) for p in st['pebbles'] if p['date']==D],key=lambda x:x[1])
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8790/tests/app.html');await pg.wait_for_timeout(300);await S.at(pg,'2026-11-02T07:00:00+11:00')
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#freshBtn');await pg.wait_for_timeout(400);await pg.click('#setBtn');await pg.wait_for_timeout(800)
  # --- drop into a 40 min gap between two pebbles
  await setup(pg,[{'id':'a','pid':'pa','date':D,'start':540,'dur':60,'trans':True,'tlen':10,'session':[]},{'id':'b','pid':'pb','date':D,'start':640,'dur':60,'trans':True,'session':[]}])
  pa=await pg.locator('.pebble[data-id="a"]').bounding_box();pw=pa['width']/60
  await pg.locator('#adds .chip[data-gid]').first.click();await pg.wait_for_timeout(300)
  it=pg.locator('.chippop button',has_text='Gamma');ib=await it.bounding_box()
  tx=pa['x']+pa['width']+15*pw+12;ty=pa['y']+pa['height']/2
  await pg.mouse.move(ib['x']+20,ib['y']+10);await pg.mouse.down();await pg.mouse.move(tx,ty,steps=14);await pg.wait_for_timeout(150)
  sl=await pg.locator('.slot[data-for="drop"]').bounding_box();await pg.mouse.up();await pg.wait_for_timeout(800)
  st=await S.state(pg);m=mine(st);new=[x for x in m if x[0] not in('a','b')]
  S.check([x for x in m if x[0] in('a','b')]==[('a',540,60),('b',640,60)],'existing pebbles stay put',m)
  S.check(new and new[0][1]==610 and new[0][2]==25,'dropped pebble fits the gap: 10:10 for 25 min (+5 min transition)',new)
  S.check(sl and abs(sl['width']-25*pw)<3,'outline shows the fitted size while dragging',sl and round(sl['width']/pw))
  # --- task gap smaller than 5+transition: fills without a transition
  await setup(pg,[{'id':'a','pid':'pa','date':D,'start':540,'dur':60,'trans':False,'session':[]},{'id':'b','pid':'pb','date':D,'start':605,'dur':60,'trans':True,'session':[]}])
  pa=await pg.locator('.pebble[data-id="a"]').bounding_box()
  await pg.locator('#adds .chip[data-gid]').first.click();await pg.wait_for_timeout(300)
  ib=await pg.locator('.chippop button',has_text='Gamma').bounding_box()
  await pg.mouse.move(ib['x']+20,ib['y']+10);await pg.mouse.down();await pg.mouse.move(pa['x']+pa['width']+14,ty,steps=14);await pg.wait_for_timeout(150);await pg.mouse.up();await pg.wait_for_timeout(800)
  m=mine(await S.state(pg));S.check(m==[('a',540,60),(m[1][0],600,5),('b',605,60)],'5 min gap gets a 5 min pebble, nothing moves',m)
  # --- drag snaps to the timeline's marks, not to steps from an off-grid start
  await setup(pg,[{'id':'x','pid':'pa','date':D,'start':633,'dur':27,'trans':False,'session':[]}])
  xb=await pg.locator('.pebble[data-id="x"]').bounding_box();pw=xb['width']/27
  await pg.mouse.move(xb['x']+xb['width']/2,xb['y']+xb['height']/2);await pg.mouse.down();await pg.mouse.move(xb['x']+xb['width']/2+13*pw,xb['y']+xb['height']/2,steps=10);await pg.mouse.up();await pg.wait_for_timeout(700)
  m=mine(await S.state(pg));S.check(m[0][1]%5==0 and m[0][1] in(645,650),'moved pebble lands on a 5-minute mark',m)
  await setup(pg,[{'id':'x','pid':'pa','date':D,'start':633,'dur':27,'trans':False,'session':[]}])
  xb=await pg.locator('.pebble[data-id="x"]').bounding_box()
  await pg.mouse.move(xb['x']+xb['width']-2,xb['y']+xb['height']/2);await pg.mouse.down();await pg.mouse.move(xb['x']+xb['width']-2+8*pw,xb['y']+xb['height']/2,steps=8);await pg.mouse.up();await pg.wait_for_timeout(700)
  m=mine(await S.state(pg));S.check((m[0][1]+m[0][2])%5==0,'stretched end lands on a 5-minute mark',m)
  # --- finish: next pebble stays on the grid
  await setup(pg,[{'id':'f','pid':'pa','date':D,'start':480,'dur':60,'trans':True,'tlen':10,'session':[]},{'id':'g','pid':'pb','date':D,'start':550,'dur':60,'trans':True,'session':[]},{'id':'h','pid':'pc','date':D,'start':620,'dur':30,'trans':True,'session':[]}])
  await S.at(pg,'2026-11-02T08:02:00+11:00')
  await pg.click('#finBtn') if await pg.locator('#finBtn').count() else await pg.locator('button',has_text='finish').first.click()
  await pg.wait_for_timeout(800);m=mine(await S.state(pg))
  S.check(all(x[1]%5==0 for x in m if x[0]!='f'),'after finish, later pebbles sit on 5-minute marks',m)
  # --- phase colour
  await setup(pg,[{'id':'w','pid':'pa','date':D,'start':480,'dur':60,'trans':True,'session':[]}])
  await S.at(pg,'2026-11-02T08:20:00+11:00');await pg.wait_for_timeout(1200)
  ic=await pg.evaluate("document.querySelector('link[rel=icon]').href");tt=await pg.title()
  S.check(ic.startswith('data:image/svg') and tt.startswith('⚫'),'working: icon takes the channel colour, title marked',(ic[:60],tt))
  await S.at(pg,'2026-11-02T08:57:00+11:00');seen=set()
  for i in range(5):
    seen.add(await pg.evaluate("document.querySelector('link[rel=icon]').href"));await pg.wait_for_timeout(500)
  S.check(len(seen)>=2,'wrapping up: icon flashes',len(seen))
  S.check(not S.errs,'no errors',S.errs[:3]);await b.close()
asyncio.run(main());srv.terminate();print('\nFAILS',S.fails)
