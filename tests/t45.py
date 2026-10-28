import asyncio,os,subprocess,time,sys,json
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8772','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
S=Sim()
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8772/tests/app.html');await pg.wait_for_timeout(300);await S.at(pg,'2026-11-02T20:40:00+11:00')
  await pg.click('#setBtn');await pg.wait_for_timeout(400);await pg.click('#freshBtn');await pg.wait_for_timeout(400);await pg.click('#setBtn')
  # chip hover popover
  await pg.locator('#adds .chip[data-gid]').nth(3).hover();await pg.wait_for_timeout(300);early=await pg.locator('.chippop.on').count();await pg.wait_for_timeout(700)
  items=await pg.locator('.chippop button').all_inner_texts();S.check(early==0 and len(items)>0,'hovering a chip pops its projects after a pause',items)
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','chippop.png'),clip={'x':0,'y':180,'width':700,'height':200})
  await pg.locator('.chippop button').first.click();await pg.wait_for_timeout(500)
  st=await S.state(pg);S.check(len(st['pebbles'])==1,'clicking a project in the pop adds it',[st['projects'][p['pid']]['name'] for p in st['pebbles']])
  await pg.keyboard.press('Escape');await pg.mouse.click(5,5)
  # activity hover pop
  await pg.locator('#adds .chip[data-kind="break"]').hover();await pg.wait_for_timeout(1000)
  S.check(await pg.locator('.chippop.on button').count()>=3,'break chip pops its activities',await pg.locator('.chippop button').all_inner_texts())
  await pg.locator('.chippop button',has_text='Lunch').click();await pg.wait_for_timeout(500)
  # selected activity look
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','actsel.png'),clip={'x':0,'y':330,'width':1280,'height':300})
  col=await pg.evaluate("(()=>{const e=document.querySelector('.pebble.sel');return [getComputedStyle(e).backgroundColor,getComputedStyle(e).color]})()")
  S.check(col[0]!=col[1],'selected activity keeps readable colours',col)
  await pg.keyboard.press('Escape');await pg.mouse.click(5,5)
  # late night: pebble 23:00-01:00
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const pid=Object.keys(st.projects).find(k=>st.projects[k].kind==='work');st.pebbles=[{id:'late',pid,date:'2026-11-02',start:23*60,dur:120,pomo:false,intent:'',trans:true,session:[]}];st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));const m=JSON.parse(localStorage.getItem('__mdb'));m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})()""")
  await S.at(pg,'2026-11-03T00:30:00+11:00')
  nm=await pg.inner_text('#nowName');S.check(nm!='Nothing else planned today' and 'Free' not in nm,'at 12:30am the late pebble is still running',nm)
  dsel=await pg.locator('#days .day.on').get_attribute('data-d');S.check(dsel=='2026-11-02','view stays on Monday after midnight',dsel)
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','late.png'))
  # resize past 5am limit
  print('pre',[(p['id'],p['date'],p['start'],p['dur']) for p in (await S.state(pg))['pebbles']])
  el=pg.locator(".pebble[data-id='late']");rz=el.locator('.pb-rz');await rz.scroll_into_view_if_needed();rb=await rz.bounding_box();print('rz',rb)
  await pg.mouse.move(rb['x']+rb['width']/2,rb['y']+20);await pg.mouse.down();await pg.mouse.move(rb['x']+500*2.8,rb['y']+20,steps=15);await pg.mouse.up();await pg.wait_for_timeout(600)
  st=await S.state(pg);print('post',[(p['id'],p['date'],p['start'],p['dur']) for p in st['pebbles']]);p=[q for q in st['pebbles'] if q['id']=='late'][0];S.check(p['start']+p['dur']==29*60,'cannot run past 5am',(p['start'],p['dur']))
  await S.at(pg,'2026-11-03T05:01:00+11:00');dsel=await pg.locator('#days .day.on').get_attribute('data-d');S.check(dsel=='2026-11-03','after 5am it moves to Tuesday',dsel)
  # left resize + magnet on Tuesday
  await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const pid=Object.keys(st.projects).find(k=>st.projects[k].kind==='work');const br=Object.keys(st.projects).find(k=>st.projects[k].name==='Short break');
    st.pebbles=[{id:'a',pid,date:'2026-11-03',start:9*60,dur:60,trans:false,session:[]},{id:'b',pid:br,date:'2026-11-03',start:12*60,dur:15,trans:true,session:[]}];st.savedAt=Date.now()+9000;localStorage.setItem('pebble-planner-v1',JSON.stringify(st));const m=JSON.parse(localStorage.getItem('__mdb'));m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})()""")
  await pg.reload();await pg.wait_for_timeout(1300)
  brk=pg.locator(".pebble[data-id='b']");bb=await brk.bounding_box();lz=await brk.locator('.pb-rzl').bounding_box()
  await pg.mouse.move(lz['x']+lz['width']/2,lz['y']+30);await pg.mouse.down();await pg.mouse.move(lz['x']+lz['width']/2-30*2.8,lz['y']+30,steps=10);await pg.mouse.up();await pg.wait_for_timeout(600)
  st=await S.state(pg);b2=[p for p in st['pebbles'] if p['id']=='b'][0];S.check(b2['start']==11*60+30 and b2['start']+b2['dur']==12*60+15,'activity resized backwards from its left edge',(b2['start'],b2['dur']))
  # magnet: move 'a' so its end is 6 min before b
  a=pg.locator(".pebble[data-id='a']");ab=await a.bounding_box();shift=(11*60+30-6-(10*60))*2.8
  await pg.mouse.move(ab['x']+ab['width']/2,ab['y']+30);await pg.mouse.down();await pg.mouse.move(ab['x']+ab['width']/2+shift,ab['y']+30,steps=14);await pg.mouse.up();await pg.wait_for_timeout(600)
  st=await S.state(pg);a2=[p for p in st['pebbles'] if p['id']=='a'][0];b2=[p for p in st['pebbles'] if p['id']=='b'][0]
  S.check(a2['start']+a2['dur']==b2['start'],'small gap closes: pebble snaps against its neighbour',(a2['start'],a2['dur'],b2['start']))
  # chapter marks
  ch=await pg.eval_on_selector_all('.chapm','els=>els.map(e=>e.textContent)');S.check(len(ch)>=1,'month shown as a chapter mark in the week strip',ch)
  await pg.click('#wkPrev');await pg.wait_for_timeout(400);ch=await pg.eval_on_selector_all('.chapm','els=>els.map(e=>e.textContent)');S.check(len(ch)==2,'bridging week shows both months',ch)
  wk=await (await pg.query_selector('.week')).bounding_box();await pg.screenshot(path=os.path.join(ROOT,'tests','shots','chap.png'),clip={'x':0,'y':wk['y']-4,'width':1280,'height':wk['height']+8})
  S.check(not S.errs,'no errors',S.errs[:2]);await b.close()
asyncio.run(main());srv.terminate()
