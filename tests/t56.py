import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8784','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
SET="""(st=>{st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));localStorage.removeItem('pebble-planner-v1-base');const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})"""
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8784/tests/app.html');await pg.wait_for_timeout(300);await S.at(pg,'2026-11-02T08:00:00+11:00')
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#freshBtn');await pg.wait_for_timeout(400);await pg.click('#setBtn');await pg.wait_for_timeout(1200)
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const g=st.groups[0].id;
    st.projects.pa={id:'pa',kind:'work',name:'Kalorama EOI',group:g,tasks:[{id:'t1',text:'Draft statement',done:false},{id:'t2',text:'Budget',done:false,rs:2},{id:'t3',text:'Site plan',done:false}]};
    st.projects.pb={id:'pb',kind:'work',name:'Jon call',group:st.groups[1].id,tasks:[]};
    st.pebbles=[{id:'y1',pid:'pa',date:'2026-10-30',start:540,dur:60,trans:true,session:['t1','t2'],plan:60},{id:'y2',pid:'pa',date:'2026-10-29',start:540,dur:80,trans:true,session:[],plan:60},{id:'y3',pid:'pa',date:'2026-10-28',start:540,dur:75,trans:true,session:[],plan:60}];("""+SET+""")(st)})()""")
  await pg.reload();await pg.wait_for_timeout(1300)
  rv=await pg.inner_text('#review');S.check('Draft statement' in rv and 'Budget' in rv,'review shows unfinished session tasks from Friday',rv[:120])
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','review.png'),clip={'x':0,'y':200,'width':1280,'height':200})
  await pg.locator('#review [data-rv="today"][data-tid="t2"]').click();await pg.wait_for_timeout(700)
  st=await S.state(pg);tp=[p for p in st['pebbles'] if p['date']=='2026-11-02'];t2=[t for t in st['projects']['pa']['tasks'] if t['id']=='t2'][0]
  S.check(len(tp)==1 and 't2' in tp[0]['session'] and t2['rs']==3,'"today" books it into a pebble today and counts the move',(tp,t2))
  S.check(await pg.locator('.drawer .task .rs').count()>=1,'task moved on 3 times shows ↻3')
  S.check('usually runs' in (await pg.inner_text('.drawer')).lower(),'drawer shows how this project usually runs',(await pg.locator('.drawer .runs').all_inner_texts()))
  await pg.locator('#review [data-rv="drop"][data-tid="t1"]').click();await pg.wait_for_timeout(500);S.check(await pg.locator('#review').is_hidden(),'"later" clears the review')
  # repeat weekly
  await pg.locator('.pebble').first.click();await pg.wait_for_timeout(600)
  await pg.locator('#pnRep [data-rep="week"]').click();await pg.wait_for_timeout(500)
  await pg.click('#wkNext');await pg.wait_for_timeout(600)
  st=await S.state(pg);rep=[p for p in st['pebbles'] if p['date']=='2026-11-09'];S.check(len(rep)==1 and rep[0].get('rep'),'weekly repeat appears next Monday',rep)
  await pg.locator('.pebble').first.hover();await pg.wait_for_timeout(100);await pg.keyboard.press('Delete');await pg.wait_for_timeout(600)
  await pg.click('#wkPrev');await pg.wait_for_timeout(400);await pg.click('#wkNext');await pg.wait_for_timeout(600)
  st=await S.state(pg);S.check(not [p for p in st['pebbles'] if p['date']=='2026-11-09'],'a deleted repeat stays deleted')
  await pg.locator('#wkHome').click();await pg.wait_for_timeout(500)
  # hover + D duplicate
  n0=len((await S.state(pg))['pebbles']);await pg.locator('.pebble').first.hover();await pg.keyboard.press('Escape');await pg.mouse.move(5,5);await pg.locator('.pebble').first.hover();await pg.wait_for_timeout(100);await pg.keyboard.press('d');await pg.wait_for_timeout(600)
  S.check(len((await S.state(pg))['pebbles'])==n0+1,'hover + D duplicates a pebble')
  await pg.keyboard.press('Escape');await pg.mouse.click(5,5)
  # chip pop drag onto timeline
  n1=len((await S.state(pg))['pebbles']);chip=pg.locator('#adds .chip[data-gid]').nth(1);await chip.hover();await pg.wait_for_timeout(1000)
  it=pg.locator('.chippop button').first;ib=await it.bounding_box();sc=await pg.locator('#scroller').bounding_box()
  await pg.mouse.move(ib['x']+20,ib['y']+10);await pg.mouse.down();await pg.mouse.move(sc['x']+500,sc['y']+80,steps=12);await pg.wait_for_timeout(100)
  prev=await pg.locator('.slot[data-for="drop"]').count();await pg.mouse.up();await pg.wait_for_timeout(700)
  st=await S.state(pg);jp=len(st['pebbles'])-n1;S.check(prev==1 and jp==1,'drag a project from the chip pop onto the timeline',(prev,jp))
  # drag a task onto the timeline
  await pg.keyboard.press('Escape');await pg.mouse.click(5,5);await pg.click('#docBtn');await pg.wait_for_timeout(600)
  await pg.locator('.pl-item',has_text='Kalorama EOI').click();await pg.wait_for_timeout(500)
  h=pg.locator('.card [data-role="bl"] [data-tid="t3"] .handle');hb=await h.bounding_box();sc=await pg.locator('#scroller').bounding_box()
  await pg.mouse.move(hb['x']+5,hb['y']+5);await pg.mouse.down();await pg.mouse.move(sc['x']+800,sc['y']+80,steps=15);await pg.wait_for_timeout(100);await pg.mouse.up();await pg.wait_for_timeout(700)
  st=await S.state(pg);tp=[p for p in st['pebbles'] if p['date']=='2026-11-02' and 't3' in (p.get('session') or [])];S.check(len(tp)==1,'drag a task onto the timeline books it',tp)
  # quick typing
  await pg.keyboard.press('Escape');await pg.click('#docBtn');await pg.wait_for_timeout(300);await pg.mouse.click(5,5)
  await pg.keyboard.press('n');await pg.wait_for_timeout(600);await pg.fill('#pkFind','jon call 45m 4pm');await pg.wait_for_timeout(200)
  prs=await pg.inner_text('.pk-parse');await pg.press('#pkFind','Enter');await pg.wait_for_timeout(600)
  st=await S.state(pg);q=[p for p in st['pebbles'] if p.get('pid')=='pb' and p['start']==16*60];S.check(len(q)==1 and q[0]['dur']==45,'typing "jon call 45m 4pm" books it at 4pm for 45 min',(prs,q))
  # free time nudge
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));st.projects.pa.tasks.push({id:'t9',text:'Insurance form',done:false,due:'2026-11-04'});st.pebbles=st.pebbles.filter(p=>p.date!=='2026-11-02'||p.start>=16*60);("""+SET+""")(st)})()""")
  await S.at(pg,'2026-11-02T13:00:00+11:00');nx=await pg.inner_text('#nowNext');S.check('Insurance form' in nx,'free time offers the most urgent unbooked task',nx)
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','free.png'),clip={'x':0,'y':60,'width':1280,'height':140})
  S.check(not S.errs,'no errors',S.errs[:3]);await b.close()
asyncio.run(main());srv.terminate()
