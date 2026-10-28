import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8779','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
SET="""(st=>{st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));localStorage.removeItem('pebble-planner-v1-base');const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})"""
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8779/tests/app.html');await pg.wait_for_timeout(300);await S.at(pg,'2026-11-02T07:00:00+11:00')
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#freshBtn');await pg.wait_for_timeout(400);await pg.click('#setBtn');await pg.wait_for_timeout(1200)
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const g=st.groups[0].id;['pa','pb','pc','pd'].forEach((id,i)=>st.projects[id]={id,kind:'work',name:'Proj '+'ABCD'[i],tasks:[],group:g});
    st.pebbles=[{id:'a',pid:'pa',date:'2026-11-02',start:540,dur:55,trans:true,session:[]},{id:'b',pid:'pb',date:'2026-11-02',start:600,dur:30,trans:true,session:[]},{id:'c',pid:'pc',date:'2026-11-02',start:635,dur:30,trans:true,session:[]},{id:'d',pid:'pd',date:'2026-11-02',start:780,dur:60,trans:true,session:[]}];("""+SET+""")(st)})()""")
  await pg.reload();await pg.wait_for_timeout(1300)
  async def get():
    st=await S.state(pg);return {p['id']:(p['start'],p['dur'],p.get('tlen')) for p in st['pebbles']}
  g=await get();print('loaded',g)
  S.check(await pg.locator(".trans[data-id='c']").count()==0,'no transition drawn into the free time after C',await pg.eval_on_selector_all('.trans','e=>e.map(x=>x.dataset.id)'))
  A=pg.locator(".pebble[data-id='a']");rz=await A.locator('.pb-rz').bounding_box();x=rz['x']+rz['width']/2
  await pg.mouse.move(x,rz['y']+30);await pg.mouse.down();await pg.mouse.move(x+5*2.8,rz['y']+30,steps=6);await pg.mouse.up();await pg.wait_for_timeout(600)
  g=await get();S.check(g['a'][1]==60 and g['a'][2]==5 and g['b'][0]==605,'stretching 55→60 keeps the 5 min transition (no extra jump)',g)
  # alt-drag B alone
  B=pg.locator(".pebble[data-id='b']");bb=await B.bounding_box();x=bb['x']+bb['width']/2
  await pg.keyboard.down('Alt');await pg.mouse.move(x,bb['y']+30);await pg.mouse.down();await pg.mouse.move(x+20*2.8,bb['y']+30,steps=8);await pg.mouse.up();await pg.keyboard.up('Alt');await pg.wait_for_timeout(600)
  g=await get();S.check(g['b'][0]==625 and g['c'][0]==660,'Alt-drag moves B on its own; C is only pushed because B reached it',g)
  # wheel scroll
  sl0=await pg.evaluate("document.getElementById('scroller').scrollLeft");await pg.mouse.move(640,(await A.bounding_box())['y']+30);await pg.mouse.wheel(0,300);await pg.wait_for_timeout(300);s_plain=await pg.evaluate("document.getElementById('scroller').scrollLeft");await pg.keyboard.down('Control');await pg.mouse.wheel(0,300);await pg.keyboard.up('Control');await pg.wait_for_timeout(300)
  sl1=await pg.evaluate("document.getElementById('scroller').scrollLeft");S.check(s_plain==sl0 and sl1!=sl0,'plain wheel leaves the timeline alone; ctrl + wheel scrolls it sideways',(sl0,s_plain,sl1))
  # stem shape
  await A.click();await pg.wait_for_timeout(700)
  r=await pg.evaluate("(()=>{const tl=document.querySelector('.timeline').getBoundingClientRect(),d=document.querySelector('.drawer').getBoundingClientRect();return Math.round(tl.bottom-d.top)})()")
  S.check(abs(r)<=1,'drawer docks under the timeline',r)
  await pg.keyboard.press('Escape');await pg.mouse.click(5,5);await pg.wait_for_timeout(1500)
  # two devices: page2 shares storage but has its own memory
  p2=await ctx.new_page();await p2.add_init_script(INIT);p2.on('pageerror',lambda e:S.errs.append('p2 '+str(e)));await p2.goto('http://127.0.0.1:8779/tests/app.html');await p2.wait_for_timeout(1500)
  # device 1 adds a day note (not seen by device 2)
  dn=pg.locator('#dayNotes [data-nadd]');await dn.fill('note from laptop');await dn.press('Enter');await pg.wait_for_timeout(1500)
  # device 2 adds a pebble from a chip
  await p2.locator('#adds .chip[data-kind="break"]').click();await p2.wait_for_timeout(1800)
  st=await p2.evaluate("JSON.parse(JSON.parse(localStorage.getItem('__mdb'))['data/users/james/state'].state?JSON.stringify(JSON.parse(localStorage.getItem('__mdb'))['data/users/james/state'].state):'{}')")
  S.check(any(n['text']=='note from laptop' for n in st['notes']) and len(st['pebbles'])==5,'edits from both devices kept after sync',(len(st['pebbles']),[n['text'] for n in st['notes']]))
  S.check(not S.errs,'no errors',S.errs[:3]);await b.close()
asyncio.run(main());srv.terminate()
