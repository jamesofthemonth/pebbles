# Locked pebbles: never pushed by other pebbles, still movable/resizable themselves.
import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8791','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
SET="""(st=>{st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));localStorage.removeItem('pebble-planner-v1-base');const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})"""
D='2026-11-02'
async def setup(pg,pebs):
  await pg.evaluate("""(pebs=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const g=st.groups[0].id;
    st.projects.pa={id:'pa',kind:'work',name:'Alpha',group:g,tasks:[]};st.projects.pb={id:'pb',kind:'work',name:'Beta',group:g,tasks:[]};st.projects.pc={id:'pc',kind:'work',name:'Meeting',group:g,tasks:[]};
    st.pebbles=pebs;("""+SET+""")(st)})""",pebs);await pg.reload();await pg.wait_for_timeout(1300)
def P(i,pid,st,du,**k):return dict(id=i,pid=pid,date=D,start=st,dur=du,trans=k.get('trans',False),session=[],**({'lock':True} if k.get('lock') else {}))
def mine(st):return {p['id']:(p['start'],p['dur']) for p in st['pebbles'] if p['date']==D}
async def drag(pg,sel,part,dmin,ppm):
  b=await pg.locator(f'.pebble[data-id="{sel}"]').bounding_box();x=b['x']+(b['width']-2 if part=='end' else b['width']/2);y=b['y']+b['height']/2
  await pg.mouse.move(x,y);await pg.mouse.down();await pg.mouse.move(x+dmin*ppm,y,steps=12);await pg.wait_for_timeout(100);await pg.mouse.up();await pg.wait_for_timeout(700)
async def main():
 async with async_playwright() as Pw:
  b=await Pw.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8791/tests/app.html');await pg.wait_for_timeout(300);await S.at(pg,'2026-11-02T07:00:00+11:00')
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#freshBtn');await pg.wait_for_timeout(400);await pg.click('#setBtn');await pg.wait_for_timeout(800)
  base=[P('a','pa',540,60),P('b','pb',600,55),P('L','pc',660,60,lock=True),P('c','pb',720,30)]
  await setup(pg,base);ppm=(await pg.locator('.pebble[data-id="a"]').bounding_box())['width']/60
  S.check(await pg.locator('.pebble.locked[data-id="L"]').count()==1,'locked pebble shows the lock mark')
  await drag(pg,'a','end',30,ppm);m=mine(await S.state(pg))
  S.check(m['L']==(660,60),'stretching a chain into a locked pebble leaves it where it is',m)
  S.check(m['a']==(540,90) and m['b'][0]>=720 and m['c'][0]>=m['b'][0]+55,'the pushed pebble goes after the locked one',m)
  await setup(pg,[P('a','pa',540,60),P('L','pc',660,60,lock=True)])
  await drag(pg,'a','end',60,ppm);m=mine(await S.state(pg));S.check(m['L']==(660,60) and m['a'][0]+m['a'][1]<=660,'stretching stops at a locked pebble',m)
  await setup(pg,[P('a','pa',540,30),P('L','pc',660,60,lock=True)])
  await drag(pg,'a','mid',135,ppm);m=mine(await S.state(pg));S.check(m['L']==(660,60) and (m['a'][0]>=720 or m['a'][0]+30<=660),'moving onto a locked pebble lands beside it, not on it',m)
  await setup(pg,[P('L','pc',660,60,lock=True),P('c','pb',720,30)])
  await drag(pg,'L','mid',30,ppm);m=mine(await S.state(pg));S.check(m['L']==(690,60) and m['c'][0]>=750,'a locked pebble can still be moved itself, and pushes others',m)
  await drag(pg,'L','end',-15,ppm);m=mine(await S.state(pg));S.check(m['L']==(690,45),'…and its end can still be changed',m)
  # dragging two joined pebbles onto a lock: one lands before it, one after
  await setup(pg,[P('a','pa',540,60),P('b','pb',600,60),P('L','pc',720,60,lock=True)])
  await drag(pg,'a','mid',75,ppm);m=mine(await S.state(pg))
  S.check(m['L']==(720,60) and m['a'][0]+60<=720 and m['b'][0]>=780,'joined pair dropped on a lock: first fits before it, second after',m)
  await setup(pg,[P('a','pa',540,60),P('b','pb',600,60),P('L','pc',720,60,lock=True)])
  await drag(pg,'a','mid',150,ppm);m=mine(await S.state(pg))
  S.check(m['L']==(720,60) and m['a']==(660,60) and m['b'][0]>=780,'first pebble mostly over the lock\'s first half: tucked in before it',m)
  await setup(pg,[P('a','pa',540,60),P('b','pb',600,60),P('L','pc',720,60,lock=True)])
  await drag(pg,'a','mid',200,ppm);m=mine(await S.state(pg))
  S.check(m['L']==(720,60) and m['a'][0]>=780 and m['b'][0]>=m['a'][0]+60,'pair dropped mostly past the lock: both go after',m)
  # finish early: pebbles after the lock stay put
  await setup(pg,[P('f','pa',480,60,trans=True),P('g','pb',550,30),P('L','pc',600,60,lock=True),P('h','pb',660,30)])
  await S.at(pg,'2026-11-02T08:20:00+11:00');await pg.click('#finishNow');await pg.wait_for_timeout(800);m=mine(await S.state(pg))
  S.check(m['L']==(600,60) and m['h']==(660,30) and m['g'][0]<550,'finishing early moves the day up only as far as the lock',m)
  # toggles
  await S.at(pg,'2026-11-02T07:00:00+11:00');await setup(pg,[P('a','pa',540,60)])
  await pg.locator('.pebble[data-id="a"]').hover();await pg.wait_for_timeout(150);await pg.keyboard.press('l');await pg.wait_for_timeout(500)
  S.check((await S.state(pg))['pebbles'][0].get('lock') is True,'hover + L locks')
  await pg.locator('.pebble[data-id="a"]').click();await pg.wait_for_timeout(500)
  S.check(await pg.locator('#pnLock').is_checked(),'drawer shows it locked');await pg.locator('#pnLock').uncheck();await pg.wait_for_timeout(500)
  S.check(not (await S.state(pg))['pebbles'][0].get('lock'),'drawer switch unlocks')
  await pg.locator('#pnLock').check();await pg.wait_for_timeout(400);await pg.screenshot(path=os.path.join(ROOT,'tests','shots','lock.png'),clip={'x':0,'y':300,'width':1280,'height':420})
  S.check(not S.errs,'no errors',S.errs[:3]);await b.close()
asyncio.run(main());srv.terminate();print('\nFAILS',S.fails)
