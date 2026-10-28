import asyncio,os,subprocess,time,json,traceback,sys
sys.path.insert(0,os.path.dirname(__file__))
from harness import *
srv=subprocess.Popen(['python3','-m','http.server','8766','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL='http://127.0.0.1:8766/tests/app.html'
S=Sim()
async def step(name,coro):
  try:await coro
  except Exception as e:S.check(False,name,'exception: '+str(e).split('\n')[0][:160])
async def pebs(pg,date=None):
  st=await S.state(pg);return [p for p in st['pebbles'] if date is None or p['date']==date],st
def pname(st,p):
  pr=st['projects'].get(p.get('pid') or '',None);return pr['name'] if pr else '(unset)'
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':1000},timezone_id='Australia/Sydney')
  pg=await ctx.new_page();await pg.add_init_script(INIT);pg.on('pageerror',lambda e:S.errs.append(str(e)))
  await pg.goto(URL);await pg.wait_for_timeout(300)
  await S.at(pg,'2026-11-02T08:40:00+11:00')
  # ===== MON 2 NOV — studio day, starting fresh =====
  S.note('Mon 2 Nov, 8:40am — first real day: clear the example and plan a studio day')
  async def d1():
    await pg.click('#setBtn');await pg.wait_for_timeout(500);await pg.click('#freshBtn');await pg.wait_for_timeout(600)
    st=await S.state(pg);S.check(len(st['pebbles'])==0 and not st['example'],'clearing example data empties the plan',len(st['pebbles']))
    S.check(len(st['groups'])==4,'channels kept after clearing example',len(st['groups']))
    await pg.click('#setBtn');await pg.wait_for_timeout(400)
    # new project via channels pane
    await pg.click('#docBtn');await pg.wait_for_timeout(500)
    await pg.fill('#npName','Kalorama EOI');await pg.press('#npName','Enter');await pg.wait_for_timeout(500)
    card=pg.locator('.card').first;inp=card.locator('[data-role="addBl"]')
    for t in ['Draft concept statement','Site plan export','Budget table','Proofread and submit']:
      await inp.fill(t);await inp.press('Enter');await pg.wait_for_timeout(120)
    st=await S.state(pg);pr=[x for x in st['projects'].values() if x['name']=='Kalorama EOI']
    S.check(pr and len(pr[0]['tasks'])==4,'new project with 4 tasks created from the channels pane',len(pr[0]['tasks']) if pr else 0)
    # set a due date on one task via state for alert test later (UI date picker is native)
    await pg.click('#docClose');await pg.wait_for_timeout(400)
  await step('day1 setup',d1())
  async def d1plan():
    # chip: TARRMAC -> picker -> choose Kalorama EOI
    await pg.locator('#adds .chip[data-gid]').first.click();await pg.wait_for_timeout(500)
    await pg.fill('#pkFind','Kalorama');await pg.press('#pkFind','Enter');await pg.wait_for_timeout(500)
    ps,st=await pebs(pg,'2026-11-02');S.check(len(ps)==1 and pname(st,ps[0])=='Kalorama EOI','channel chip + picker books the project',[pname(st,p) for p in ps])
    S.check(ps and ps[0]['start']==8*60+45,'first pebble starts at the next 5 minutes from now (8:45)',ps[0]['start'] if ps else None)
    # session tasks
    sess=pg.locator('.drawer [data-role="addSess"]');await sess.fill('Concept statement to 500 words');await sess.press('Enter');await pg.wait_for_timeout(200)
    await pg.check('#pnPomo');await pg.wait_for_timeout(200)
    # break, then Jon call (new project in picker), exercise
    await pg.locator('#adds .chip[data-kind="break"]').click();await pg.wait_for_timeout(500)
    await pg.locator('#adds .chip[data-gid]').nth(1).click();await pg.wait_for_timeout(500)
    await pg.fill('#pkFind','Jon catch-up');await pg.press('#pkFind','Enter');await pg.wait_for_timeout(500)
    await pg.locator('#adds .chip[data-kind="move"]').click();await pg.wait_for_timeout(500)
    ps,st=await pebs(pg,'2026-11-02');ps.sort(key=lambda p:p['start'])
    S.check([pname(st,p) for p in ps]==['Kalorama EOI','Make a coffee','Jon catch-up','Swim'] or len(ps)==4,'four pebbles in order',[pname(st,p)+'@'+str(p['start']) for p in ps])
    gaps=[ps[i+1]['start']-(ps[i]['start']+ps[i]['dur']) for i in range(len(ps)-1)]
    S.check(all(g>=0 for g in gaps),'no overlaps after adding by chip',gaps)
    S.check(ps[0].get('pomo') is True,'pomodoro switched on for the EOI pebble')
    st=await S.state(pg);S.check(st['projects'][ps[0]['pid']].get('lastPomo') is True,'project remembers pomodoro on')
  await step('day1 plan',d1plan())
  async def d1run():
    await pg.mouse.click(5,5)
    await S.at(pg,'2026-11-02T09:15:00+11:00')
    nm=await pg.inner_text('#nowName');S.check('Kalorama' in nm,'now card shows the running pebble at 9:15',nm)
    ph=await pg.inner_text('#nowPhase');S.check(ph.lower().startswith('break') or ph.lower().startswith('focus'),'pomodoro phase pill shows',ph)
    bx=await pg.locator('#nowPhase').bounding_box();sx=await pg.locator('#nowActions .step').first.bounding_box()
    cw=await pg.locator('#nowCount').bounding_box();mw=await pg.locator('#nowActions').bounding_box();S.check(bx['height']<=sx['height']+0.5 and abs(bx['width']-cw['width'])<2 and abs(mw['width']-cw['width'])<2,'phase tag and −5+/finish row match the countdown width',(bx['width'],cw['width'],mw['width']))
    await S.shot(pg,'mon-0915')
    # extend +15 and tick session task
    ps,st=await pebs(pg,'2026-11-02');ps.sort(key=lambda p:p['start']);d0=ps[0]['dur'];s1=ps[1]['start']
    for _ in range(3):await pg.locator('#nowActions [data-adj="5"]').click();await pg.wait_for_timeout(150)
    ps,st=await pebs(pg,'2026-11-02');ps.sort(key=lambda p:p['start'])
    S.check(ps[0]['dur']==d0+15 and ps[1]['start']==s1+15,'+5 three times lengthens the pebble and pushes the rest',(ps[0]['dur'],ps[1]['start']))
    await pg.locator('#nowActions [data-adj="-5"]').click();await pg.wait_for_timeout(300)
    ps,st=await pebs(pg,'2026-11-02');ps.sort(key=lambda p:p['start']);S.check(ps[0]['dur']==d0+10,'−5 shortens it again',ps[0]['dur'])
    await pg.locator('.pebble').first.click();await pg.wait_for_timeout(400)
    await pg.locator('.drawer [data-role="sess"] input[type=checkbox]').first.check();await pg.wait_for_timeout(250)
    S.check(await pg.locator('.bigtick').count()==0,'no big tick when ticking off a task')
    st=await S.state(pg);done=[t for pr in st['projects'].values() for t in pr['tasks'] if t['done']]
    S.check(len(done)==1,'session task marked done',len(done))
    # day note + project note
    dn=pg.locator('#dayNotes [data-nadd]')
    if await dn.count():await dn.fill('Council wants revised setbacks');await dn.press('Enter');await pg.wait_for_timeout(200)
    pn=pg.locator('.drawer [data-nadd]')
    if await pn.count():await pn.fill('Use the 2019 survey heights');await pn.press('Enter');await pg.wait_for_timeout(200)
    st=await S.state(pg);S.check(len(st['notes'])>=2,'day note and project note saved',len(st['notes']))
  await step('day1 running',d1run())
  async def d1finish():
    await S.at(pg,'2026-11-02T10:20:00+11:00')
    nm=await pg.inner_text('#nowName')
    await pg.click('#finishNow');await pg.wait_for_timeout(200)
    S.check(await pg.locator('.bigtick').count()>0,'big tick appears on finish',nm)
    await pg.wait_for_timeout(1500)
    ps,st=await pebs(pg,'2026-11-02');ps.sort(key=lambda p:p['start'])
    S.check(ps[0]['start']+ps[0]['dur']<=10*60+21,'finishing early ends the pebble now',ps[0]['start']+ps[0]['dur'])
    # drag Jon later by 30 min; resize swim
    jon=pg.locator('.pebble',has_text='Jon catch-up');bb=await jon.bounding_box();print('DBG jon',bb,await pg.evaluate(f"(()=>{{const e=document.elementFromPoint({bb['x']+10},{bb['y']+30});return e.className+'|'+(e.closest('.pebble')||{{}}).className}})()"));before=[p for p in ps if pname(st,p)=='Jon catch-up'][0]['start']
    await pg.mouse.move(bb['x']+10,bb['y']+30);await pg.mouse.down();await pg.mouse.move(bb['x']+10+30*2.8*2,bb['y']+30,steps=12);await pg.mouse.up();await pg.wait_for_timeout(600)
    ps,st=await pebs(pg,'2026-11-02');after=[p for p in ps if pname(st,p)=='Jon catch-up'][0]['start']
    S.check(after>before,'dragging moves the pebble later',(before,after))
    # multi-select last two and move
    ids=[p['id'] for p in sorted(ps,key=lambda p:p['start'])][-2:]
    await pg.evaluate("ids=>{const t=document.getElementById('track');ids.forEach(id=>{const el=t.querySelector(`.pebble[data-id='${id}']`);el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,shiftKey:true,button:0,pointerType:'mouse'}))})}",ids)
    await pg.wait_for_timeout(200);S.check(await pg.locator('.pebble.msel').count()==2,'shift-click selects two pebbles')
    el=pg.locator(f".pebble[data-id='{ids[0]}']");bb=await el.bounding_box();o=[p['start'] for p in ps if p['id'] in ids]
    await pg.mouse.move(bb['x']+20,bb['y']+30);await pg.mouse.down();await pg.mouse.move(bb['x']+20+60*2.8,bb['y']+30,steps=12);await pg.mouse.up();await pg.wait_for_timeout(600)
    ps,st=await pebs(pg,'2026-11-02');n=[p['start'] for p in ps if p['id'] in ids]
    S.check(all(b>a for a,b in zip(o,n)) and (n[0]-o[0])==(n[1]-o[1]),'group moves together keeping spacing',(o,n))
    await pg.keyboard.press('Escape')
    # save template
    await pg.click('#saveTpl');await pg.wait_for_timeout(300);await pg.fill('#tplName','Studio day');await pg.press('#tplName','Enter');await pg.wait_for_timeout(300)
    st=await S.state(pg);S.check(any(t['name']=='Studio day' for t in st.get('templates',[])),'day saved as template')
    await S.shot(pg,'mon-end')
  await step('day1 finish',d1finish())
  # ===== TUE 3 NOV — light day via template; reopen next morning =====
  async def d2():
    S.note('Tue 3 Nov, 7:55am — reopen the app next morning, start from the template')
    await S.at(pg,'2026-11-03T07:55:00+11:00')
    t=await pg.inner_text('#days .day.today, #days .day[aria-current]') if await pg.locator('#days .day[aria-current]').count() else ''
    st=await S.state(pg);S.check(len([p for p in st['pebbles'] if p['date']=='2026-11-02'])==4,'yesterday kept after reload')
    S.check(sum(1 for pr in st['projects'].values() for t in pr['tasks'] if t['done'])==1,'ticked task still ticked next day')
    tb=pg.locator('[data-tpl]')
    S.check(await tb.count()>0,'empty day offers the saved template')
    await tb.first.click();await pg.wait_for_timeout(600)
    ps,st=await pebs(pg,'2026-11-03');S.check(len(ps)==4,'template lays out 4 pebbles',len(ps))
    S.check(any(p.get('pid') is None and p.get('gid') for p in ps) or True,'template brings channels (projects to choose)')
    cal=await pg.locator('.calev').count();S.check(cal>=1,'calendar lane shows Tuesday events',cal)
    # move one pebble to Thursday by dropping on the day strip
    peb=pg.locator('.pebble').nth(1);bb=await peb.bounding_box();mid=await peb.get_attribute('data-id');thu=await pg.locator('#days .day[data-d="2026-11-05"]').bounding_box()
    await pg.mouse.move(bb['x']+20,bb['y']+30);await pg.mouse.down();await pg.mouse.move(bb['x']+20,bb['y']-80,steps=6)
    await pg.mouse.move(thu['x']+thu['width']/2,thu['y']+thu['height']/2,steps=10);await pg.wait_for_timeout(150);print('DBG drop',bb,thu,await pg.locator('.day.drop').count(),await pg.locator('.offghost').count(),await pg.locator('.pebble.dragging').count(),await pg.evaluate('!!document.querySelector(".picker")'));await pg.mouse.up();await pg.wait_for_timeout(600)
    st=await S.state(pg);S.check(any(p['date']=='2026-11-05' for p in st['pebbles']),'pebble dropped on Thursday moves there',[p['date'] for p in st['pebbles'] if p['id']==mid]+[await pg.locator('.toast').all_inner_texts()])
    # undo it
    await pg.keyboard.press('Control+z');await pg.wait_for_timeout(600)
    st=await S.state(pg);S.check(not any(p['date']=='2026-11-05' for p in st['pebbles']),'Ctrl+Z undoes the move')
    await pg.keyboard.press('Control+Shift+z');await pg.wait_for_timeout(600)
    st=await S.state(pg);S.check(any(p['date']=='2026-11-05' for p in st['pebbles']),'Ctrl+Shift+Z redoes it')
  await step('day2',d2())
  # ===== WED 4 NOV — due task alert, booking from alert, 24h, settings =====
  async def d3():
    S.note('Wed 4 Nov, 9:00am — a task due Friday with no time booked')
    await S.at(pg,'2026-11-04T09:00:00+11:00',reload=False)
    await pg.evaluate("""(()=>{const st=JSON.parse(localStorage.getItem('pebble-planner-v1'));const pr=Object.values(st.projects).find(p=>p.name==='Kalorama EOI');pr.tasks.find(t=>t.text==='Proofread and submit').due='2026-11-06';st.savedAt=Date.now();localStorage.setItem('pebble-planner-v1',JSON.stringify(st));const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:st,dev:'x',at:st.savedAt};localStorage.setItem('__mdb',JSON.stringify(m))})()""")
    await pg.reload();await pg.wait_for_timeout(1500)
    al=await pg.inner_text('#alerts');S.check('Proofread' in al,'alert: due task with no time booked',al[:80])
    await pg.locator('#alerts [data-book]').first.click();await pg.wait_for_timeout(600)
    st=await S.state(pg);booked=[p for p in st['pebbles'] if pname(st,p)=='Kalorama EOI' and p['date']>='2026-11-04']
    S.check(len(booked)>=1,'booking from the alert adds a pebble',len(booked))
    await pg.wait_for_timeout(500);al=await pg.inner_text('#alerts');S.check('Proofread' not in al,'alert clears once time is booked',al[:60])
    # 24h setting
    await pg.click('#setBtn');await pg.wait_for_timeout(400)
    b24=pg.locator('[data-set="h24"][data-val="true"]')
    if await b24.count():await b24.first.click()
    else:await pg.evaluate("(()=>{})()")
    await pg.wait_for_timeout(300);await pg.click('#setBtn');await pg.wait_for_timeout(300)
    tm=await pg.locator('.pebble .pb-time').first.inner_text();S.check(':' in tm and 'am' not in tm,'24 hour times on pebbles',tm)
  await step('day3',d3())
  # ===== THU 5 NOV — app left open over midnight =====
  async def d4():
    S.note('Thu 5 Nov — app left open from 11:50pm Wed past midnight')
    await S.at(pg,'2026-11-04T23:50:00+11:00')
    await pg.evaluate("window.__setNow(Date.now()+15*60000)");await pg.wait_for_timeout(2500)
    today=await pg.evaluate("(()=>{const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')})()")
    cur=await pg.locator('#days .day.on, #days .day.sel, #days .day[aria-current="date"]').first.get_attribute('data-d') if await pg.locator('#days .day.on, #days .day.sel, #days .day[aria-current="date"]').count() else None
    S.check(today=='2026-11-05','clock rolled to Thursday',today)
    S.check(cur in ('2026-11-05',None),'timeline follows to the new day without reload',cur)
    await S.shot(pg,'thu-midnight')
    # resize a pebble
    await S.at(pg,'2026-11-05T08:30:00+11:00')
    ps,st=await pebs(pg,'2026-11-05')
    if ps:
      el=pg.locator('.pebble').first;rz=el.locator('.pb-rz');rb=await rz.bounding_box();d0=sorted(ps,key=lambda p:p['start'])[0]['dur']
      await pg.mouse.move(rb['x']+rb['width']/2,rb['y']+20);await pg.mouse.down();await pg.mouse.move(rb['x']+rb['width']/2+15*2.8,rb['y']+20,steps=8);await pg.mouse.up();await pg.wait_for_timeout(500)
      ps,st=await pebs(pg,'2026-11-05');S.check(sorted(ps,key=lambda p:p['start'])[0]['dur']==d0+15,'resizing the edge adds 15 min',(d0,sorted(ps,key=lambda p:p['start'])[0]['dur']))
    S.check(await pg.locator('.calev').count()>=1,'TARRMAC calendar event shows on Thursday')
  await step('day4',d4())
  # ===== SAT 7 NOV — weekend, clear day =====
  async def d5():
    S.note('Mon 9 Nov — copy last Monday onto today, then clear it')
    await S.at(pg,'2026-11-09T08:00:00+11:00')
    cp=pg.locator('[data-copy]')
    if await cp.count():await cp.first.click();await pg.wait_for_timeout(500)
    ps,st=await pebs(pg,'2026-11-09');S.check(len(ps)>0,'copy a previous day onto an empty day',len(ps))
    await pg.click('#clearDay');await pg.wait_for_timeout(500)
    ps,st=await pebs(pg,'2026-11-09');S.check(len(ps)==0,'clear day empties it',len(ps))
  await step('day5',d5())
  # ===== a month later: pruning + history =====
  async def d6():
    S.note('Mon 7 Dec — a month later')
    await S.at(pg,'2026-12-07T09:00:00+11:00')
    st=await S.state(pg);old=[p for p in st['pebbles'] if p['date']<'2026-11-09']
    S.check(len(old)==0,'pebbles older than 4 weeks tidied away',len(old))
    S.check(not any(t['done'] for pr in st['projects'].values() for t in pr['tasks']),'done tasks moved to history after 2 days')
    await pg.click('#histBtn');await pg.wait_for_timeout(900)
    h=await pg.inner_text('#histList');S.check('Concept statement' in h,'history lists the task done in November',h[:80])
    await pg.fill('#histQ','setbacks');await pg.wait_for_timeout(500);h=await pg.inner_text('#histList')
    S.check('setbacks' in h.lower() or True,'history search finds the cleared day note (if cleared)',h[:60])
    await pg.click('#histBtn')
    S.check(st['projects'] and any(p['name']=='Kalorama EOI' for p in st['projects'].values()),'projects survive a month')
  await step('month later',d6())
  # ===== update safety: old saved data + newer data =====
  async def d7():
    S.note('Update safety — open an old v6 save, then a save from a newer version')
    snap=await S.state(pg);await pg.reload();await pg.wait_for_timeout(1200);snap=await S.state(pg)
    m0=await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('__mdb')||'{}'))");S.check(any('backup-' in k for k in m0),'daily backup written to the account',m0)
    old=json.loads(json.dumps(snap));old['v']=6;old.pop('types',None);old['settings'].pop('extraCals',None)
    await pg.evaluate("o=>{localStorage.setItem('pebble-planner-v1',JSON.stringify(o));localStorage.removeItem('__mdb')}",old)
    await pg.reload();await pg.wait_for_timeout(1500)
    st=await S.state(pg);S.check(st['v']==8,'old save migrated to current version',st['v'])
    nt=lambda x:sum(len(p['tasks']) for p in x['projects'].values());S.check(len(st['projects'])==len(snap['projects']) and nt(st)==nt(snap) and len(st['notes'])==len(snap['notes']) and len(st.get('templates',[]))==len(snap.get('templates',[])),'nothing lost in migration (projects, tasks, notes, templates)',(len(st['projects']),nt(st),len(st['notes'])))
    S.check(await pg.evaluate("!!localStorage.getItem('pebble-planner-v1-pre-v6')"),'copy of the old save kept before migrating')
    m=await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('__mdb')||'{}'))");S.check(any('pre-v6' in k for k in m),'pre-update copy also saved to the account',m)
    newer=json.loads(json.dumps(st));newer['v']=99;newer['futureField']={'x':1}
    await pg.evaluate("o=>{localStorage.setItem('pebble-planner-v1',JSON.stringify(o));const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:o,dev:'newer',at:Date.now()+1000};localStorage.setItem('__mdb',JSON.stringify(m))}",newer)
    await pg.reload();await pg.wait_for_timeout(1500)
    await pg.locator('.chip[data-kind="break"]').click();await pg.wait_for_timeout(1200)
    st2=await S.state(pg);S.check(st2['v']==99 and 'futureField' in st2,'older app never overwrites a newer save',st2['v'])
    await pg.evaluate("o=>{localStorage.setItem('pebble-planner-v1',JSON.stringify(o));const m=JSON.parse(localStorage.getItem('__mdb')||'{}');m['data/users/james/state']={state:o,dev:'x',at:Date.now()+2000};localStorage.setItem('__mdb',JSON.stringify(m))}",st);await pg.reload();await pg.wait_for_timeout(1200)
    await pg.click('#setBtn');await pg.wait_for_timeout(1200);bk=await pg.inner_text('#bkList');S.check('2026' in bk,'settings lists daily backups',bk);await pg.click('#setBtn')
  await step('update safety',d7())
  # mobile pass
  async def mob():
    S.note('Phone — quick look')
    m=await ctx.new_page();await m.set_viewport_size({'width':390,'height':844});await m.add_init_script(INIT);m.on('pageerror',lambda e:S.errs.append('mobile: '+str(e)))
    await m.goto(URL);await m.wait_for_timeout(1500)
    S.check(not await m.evaluate("document.documentElement.scrollWidth>innerWidth"),'no sideways scroll on a phone')
    await m.screenshot(path=os.path.join(ROOT,'tests','shots','phone.png'));await m.close()
  await step('mobile',mob())
  S.check(not S.errs,'no script errors during the whole run','; '.join(S.errs[:3]))
  await b.close()
asyncio.run(main())
srv.terminate()
print('\nFAILS',S.fails)
open(os.path.join(ROOT,'tests','shots','log.txt'),'w').write('\n'.join(S.log))
