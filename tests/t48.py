import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8775','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
SET="""(st=>{st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})"""
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8775/tests/app.html');await pg.wait_for_timeout(300);await S.at(pg,'2026-11-02T07:00:00+11:00')
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#freshBtn');await pg.wait_for_timeout(400);await pg.click('#setBtn');await pg.wait_for_timeout(1200)
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const g=st.groups[0].id;['pa','pb','pc','pd'].forEach((id,i)=>st.projects[id]={id,kind:'work',name:'Proj '+'ABCD'[i],tasks:[],group:g});
    st.pebbles=[{id:'a',pid:'pa',date:'2026-11-02',start:540,dur:60,trans:true,tlen:10,session:[]},{id:'b',pid:'pb',date:'2026-11-02',start:610,dur:30,trans:false,session:[]},{id:'c',pid:'pc',date:'2026-11-02',start:640,dur:30,trans:true,session:[]},{id:'d',pid:'pd',date:'2026-11-02',start:780,dur:60,trans:true,session:[]}];("""+SET+""")(st)})()""")
  await pg.reload();await pg.wait_for_timeout(1300)
  async def get():
    st=await S.state(pg);return {p['id']:(p['start'],p['dur'],p.get('tlen')) for p in st['pebbles']}
  A=pg.locator(".pebble[data-id='a']");bb=await A.bounding_box();x=bb['x']+bb['width']/2
  await pg.mouse.move(x,bb['y']+30);await pg.mouse.down();await pg.mouse.move(x+30*2.8,bb['y']+30,steps=10);await pg.wait_for_timeout(100);tip=await pg.inner_text('.dragtip');await pg.mouse.up();await pg.wait_for_timeout(600)
  g=await get();S.check(g['a'][0]==570 and g['b'][0]==640 and g['c'][0]==670 and g['d'][0]==780,'moving A carries B (via transition) and C (touching) along; D after a gap stays',(g,tip))
  # moving B (attached to A by transition) later stretches transition and carries C
  B=pg.locator(".pebble[data-id='b']");bb=await B.bounding_box();x=bb['x']+bb['width']/2
  await pg.mouse.move(x,bb['y']+30);await pg.mouse.down();await pg.mouse.move(x+10*2.8,bb['y']+30,steps=8);await pg.mouse.up();await pg.wait_for_timeout(600)
  g=await get();S.check(g['a'][2]==20 and g['b'][0]==650 and g['c'][0]==680,'moving B later stretches its transition and carries C',g)
  # drag A off the timeline: only A removed
  bb=await A.bounding_box();x=bb['x']+bb['width']/2;await pg.mouse.move(x,bb['y']+30);await pg.mouse.down();await pg.mouse.move(x,bb['y']+260,steps=12);await pg.mouse.up();await pg.wait_for_timeout(600)
  g=await get();S.check('a' not in g and 'b' in g and 'c' in g,'dragging A off removes only A',g)
  await pg.keyboard.press('Control+z');await pg.wait_for_timeout(700)
  # transition pop stays still
  t=pg.locator('.trans').first;await t.click();await pg.wait_for_timeout(300)
  pos=[]
  for i in range(3):
    pl=await pg.locator('.tpop [data-t="+"]').bounding_box();pos.append(round(pl['x']));await pg.locator('.tpop [data-t="+"]').click();await pg.wait_for_timeout(150)
  S.check(len(set(pos))==1,'transition + button stays in place while tapping',pos)
  print(await get())
  S.check(not S.errs,'no errors',S.errs[:2]);await b.close()
asyncio.run(main());srv.terminate()
