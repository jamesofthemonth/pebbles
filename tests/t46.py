import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8773','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
SET="""(st=>{st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})"""
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8773/tests/app.html');await pg.wait_for_timeout(300);await S.at(pg,'2026-11-02T08:00:00+11:00')
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#freshBtn');await pg.wait_for_timeout(400);await pg.click('#setBtn');await pg.wait_for_timeout(1200)
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const g=st.groups[0].id;const ids=['pa','pb'];ids.forEach((id,i)=>st.projects[id]={id,kind:'work',name:'Proj '+'AB'[i],tasks:[],group:g});
    st.pebbles=[{id:'a',pid:ids[0],date:'2026-11-02',start:9*60,dur:60,trans:true,session:[]},{id:'b',pid:ids[1],date:'2026-11-02',start:10*60+10,dur:60,trans:true,session:[]}];("""+SET+""")(st)})()""")
  await pg.reload();await pg.wait_for_timeout(1300)
  async def get():
    st=await S.state(pg);return {p['id']:(p['start'],p['dur'],p.get('trans'),p.get('tlen')) for p in st['pebbles']}
  print('start',await get())
  n=await pg.evaluate("(()=>{const t=document.querySelector('.trans');return [t.offsetWidth,getComputedStyle(t).getPropertyValue('--step')]})()");print('trans width/step',n)
  B=pg.locator(".pebble[data-id='b']")
  async def dragb(mins):
    bb=await B.bounding_box();x=bb['x']+bb['width']/2;await pg.mouse.move(x,bb['y']+30);await pg.mouse.down();await pg.mouse.move(x+mins*2.8,bb['y']+30,steps=10);await pg.mouse.up();await pg.wait_for_timeout(600)
  await dragb(15);g=await get();S.check(g['b'][0]==10*60+25 and g['a'][3]==25,'moving the next pebble later stretches the transition',g)
  await dragb(-15);g=await get();S.check(g['b'][0]==10*60+10 and g['a'][3]==10,'moving it back shrinks the transition',g)
  await dragb(-10);g=await get();S.check(g['b'][0]==10*60 and g['a'][2] is False,'moving it right up joins them (no transition)',g)
  # restore a transition via + and test left-edge resize
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));st.pebbles.find(p=>p.id==='a').trans=true;st.pebbles.find(p=>p.id==='a').tlen=10;st.pebbles.find(p=>p.id==='b').start=610;("""+SET+""")(st)})()""");await pg.reload();await pg.wait_for_timeout(1300)
  lz=await B.locator('.pb-rzl').bounding_box();await pg.mouse.move(lz['x']+lz['width']/2,lz['y']+30);await pg.mouse.down();await pg.mouse.move(lz['x']+lz['width']/2-5*2.8,lz['y']+30,steps=6);await pg.mouse.up();await pg.wait_for_timeout(600)
  g=await get();S.check(g['b'][0]==605 and g['b'][0]+g['b'][1]==670 and g['a'][3]==5,'pulling its left edge earlier shortens the transition',g)
  # stem alignment while scrolling
  await pg.locator(".pebble[data-id='a']").click();await pg.wait_for_timeout(700)
  r=await pg.evaluate("(()=>{const tl=document.querySelector('.timeline').getBoundingClientRect(),d=document.querySelector('.drawer').getBoundingClientRect(),p=document.querySelector('.pebble.sel').getBoundingClientRect();return [Math.round(tl.bottom-d.top),Math.round(document.querySelector('.track').getBoundingClientRect().bottom-p.bottom),getComputedStyle(document.querySelector('.timeline')).borderBottomLeftRadius]})()")
  S.check(abs(r[0])<=1 and abs(r[1])<=1 and r[2]=='0px','drawer docks to the timeline and the selected pebble reaches its edge',r)
  await pg.evaluate("document.getElementById('scroller').scrollLeft=0");await pg.wait_for_timeout(200)
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','stem.png'),clip={'x':0,'y':300,'width':1280,'height':260})
  # wrap pill + notes title + no auto tick
  await pg.keyboard.press('Escape');await pg.mouse.click(5,5)
  await S.at(pg,'2026-11-02T09:57:00+11:00');ph=await pg.inner_text('#nowPhase');S.check('wrap' in ph.lower() and await pg.locator('#nowPhase.wrapup').count()==1,'wrap up shows in the top right',ph)
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','wrap.png'),clip={'x':0,'y':60,'width':1280,'height':170})
  t=await pg.inner_text('#dayNotes .lh .t');S.check('today' in t.lower(),'day notes read today’s notes',t)
  await pg.evaluate("window.__setNow(Date.now()+4*60000)");await pg.wait_for_timeout(2500);S.check(await pg.locator('.bigtick').count()==0,'no tick when a pebble simply ends')
  wk=await (await pg.query_selector('.week')).bounding_box();await pg.screenshot(path=os.path.join(ROOT,'tests','shots','week46.png'),clip={'x':0,'y':0,'width':1280,'height':wk['y']+wk['height']+70})
  S.check(await pg.locator('#todayBtn').count()==0,'today link removed')
  S.check(not S.errs,'no errors',S.errs[:2]);await b.close()
asyncio.run(main());srv.terminate()
