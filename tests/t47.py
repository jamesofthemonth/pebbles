import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8774','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
SET="""(st=>{st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})"""
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8774/tests/app.html');await pg.wait_for_timeout(300);await S.at(pg,'2026-11-02T07:00:00+11:00')
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#freshBtn');await pg.wait_for_timeout(400);await pg.click('#setBtn');await pg.wait_for_timeout(1200)
  # a(9-10) joined b(10-10:30) +5 trans c(10:35-11:05) | gap | d(13:00-14:00)
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const g=st.groups[0].id;const ids=['pa','pb','pc','pd'];ids.forEach((id,i)=>st.projects[id]={id,kind:'work',name:'Proj '+'ABCD'[i],tasks:[],group:g});
    st.pebbles=[{id:'a',pid:ids[0],date:'2026-11-02',start:540,dur:60,trans:false,session:[]},{id:'b',pid:ids[1],date:'2026-11-02',start:600,dur:30,trans:true,tlen:5,session:[]},{id:'c',pid:ids[2],date:'2026-11-02',start:635,dur:30,trans:true,session:[]},{id:'d',pid:ids[3],date:'2026-11-02',start:780,dur:60,trans:true,session:[]}];("""+SET+""")(st)})()""")
  await pg.reload();await pg.wait_for_timeout(1300)
  async def get():
    st=await S.state(pg);return {p['id']:(p['start'],p['dur']) for p in st['pebbles']}
  print('dom',await pg.eval_on_selector_all('.pebble','e=>e.map(x=>x.dataset.id)'),await get(),S.errs)
  A=pg.locator(".pebble[data-id='a']")
  async def stretch(mins):
    rz=await A.locator('.pb-rz').bounding_box();x=rz['x']+rz['width']/2;await pg.mouse.move(x,rz['y']+30);await pg.mouse.down();await pg.mouse.move(x+mins*2.8,rz['y']+30,steps=10)
    await pg.wait_for_timeout(120);tip=await pg.inner_text('.dragtip');await pg.mouse.up();await pg.wait_for_timeout(600);return tip
  tip=await stretch(20);g=await get();S.check(g['a']==(540,80) and g['b'][0]==620 and g['b'][1]==30 and g['c'][0]==655 and g['d'][0]==780,'stretching A pulls B and C along, D (after a gap) stays',(g,tip))
  tip=await stretch(-30);g=await get();S.check(g['a']==(540,50) and g['b'][0]==590 and g['c'][0]==625 and g['d'][0]==780,'shrinking A pulls the chain back earlier',(g,tip))
  tip=await stretch(200);g=await get();print('big stretch',g,tip);S.check(g['d'][0]>=g['c'][0]+g['c'][1],'chain running into D pushes D on instead of overlapping',g)
  S.check(not S.errs,'no errors',S.errs[:2]);await b.close()
asyncio.run(main());srv.terminate()
