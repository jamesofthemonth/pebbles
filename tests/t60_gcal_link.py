# Standalone calendar via the user's own Apps Script web app (faked with page.route).
import asyncio,os,subprocess,time,json,re,urllib.parse as up
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srv=subprocess.Popen(['python3','-m','http.server','8787','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
res=[];ok=lambda c,w,d='':(res.append(('PASS' if c else 'FAIL')+'  '+w+('  ['+str(d)+']' if d!='' else '')),print(res[-1]))
URL='https://script.google.com/macros/s/FAKEID/exec'
calls=[]
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':900},permissions=['clipboard-read','clipboard-write']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  state={'key':None}
  async def handle(route):
    q=dict(up.parse_qsl(up.urlparse(route.request.url).query));calls.append(q.get('a'))
    if q.get('key')!=state['key']:return await route.fulfill(status=200,content_type='application/json',body=json.dumps({'error':'key'}),headers={'access-control-allow-origin':'*'})
    if q.get('a')=='cals':body={'calendars':[{'id':'james@x','summary':'James'},{'id':'tarrmac@x','summary':'TARRMAC'}]}
    else:
      f=int(q['from']);import datetime as dt
      day=DAY
      body={'events':{'james@x':[{'id':'e1','summary':'Site meeting','start':{'dateTime':day+'T10:00:00'+TZ},'end':{'dateTime':day+'T11:30:00'+TZ}},{'id':'e2','summary':'Declined thing','start':{'dateTime':day+'T13:00:00'+TZ},'end':{'dateTime':day+'T14:00:00'+TZ},'attendees':[{'self':True,'responseStatus':'declined'}]}],
                      'tarrmac@x':[{'id':'e3','summary':'Install week','start':{'date':day},'end':{'date':day}}]}}
    await route.fulfill(status=200,content_type='application/json',body=json.dumps(body),headers={'access-control-allow-origin':'*'})
  await pg.route(re.compile(r'https://script\.google\.com/.*'),handle)
  await pg.goto('http://127.0.0.1:8787/');await pg.wait_for_timeout(1500)
  global TZ
  off=await pg.evaluate("-new Date().getTimezoneOffset()");TZ=('+' if off>=0 else '-')+'%02d:%02d'%(abs(off)//60,abs(off)%60)
  global DAY;DAY=await pg.evaluate("(d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'))(new Date())")
  ok(await pg.locator('#calBtn').is_hidden(),'calendar button hidden until linked')
  ok(not calls,'no calendar requests before a link is saved',calls)
  await pg.click('#setBtn');await pg.wait_for_timeout(500)
  ok(await pg.locator('#s-calendars').count()==1,'calendars section in standalone settings')
  await pg.click('#gasCopy');await pg.wait_for_timeout(300)
  scr=await pg.evaluate("navigator.clipboard.readText()")
  m=re.search(r"const KEY = '([0-9a-f]{32})'",scr);ok(m and 'doGet' in scr and 'createEvent' not in scr,'script copied with a random key, read only')
  state['key']=m.group(1)
  open('/tmp/gas.js','w').write(scr);ok(subprocess.run(['node','--check','/tmp/gas.js']).returncode==0,'copied script is valid JavaScript')
  await pg.click('#gasMan');await pg.wait_for_timeout(300)
  man=json.loads(await pg.evaluate("navigator.clipboard.readText()"));ok(man['oauthScopes']==['https://www.googleapis.com/auth/calendar.readonly'],'manifest limits Google permission to read only',man['oauthScopes'])
  await pg.fill('#calUrlIn','https://example.com/x');await pg.click('#calLink button');await pg.wait_for_timeout(300)
  ok(not (await pg.evaluate("JSON.parse(localStorage.getItem('pebble-planner-v1'))"))['settings']['calUrl'],'rejects a non Apps Script link')
  await pg.fill('#calUrlIn',URL);await pg.click('#calLink button');await pg.wait_for_timeout(2500)
  ok(not await pg.locator('#calBtn').is_hidden(),'calendar button shows once linked')
  names=await pg.locator('#calSet .calname').all_inner_texts();ok(len(names)==2,'calendar list shows both calendars',names)
  await pg.click('#setBtn');await pg.wait_for_timeout(1500)
  row=await pg.locator('#calrow').inner_text();ok('Install week' in row,'all-day event in the calendar row',row)
  tl=await pg.evaluate("Array.from(document.querySelectorAll('.calev')).map(e=>e.textContent)")
  ok(any('Site meeting' in t for t in tl) and not any('Declined' in t for t in tl),'timed event on the timeline, declined one left out',tl)
  n=len(calls);await pg.reload();await pg.wait_for_timeout(2500)
  tl=await pg.evaluate("Array.from(document.querySelectorAll('.calev')).map(e=>e.textContent)");ok(any('Site meeting' in t for t in tl),'still linked after reload',tl)
  ev=[c for c in calls[n:] if c=='events'];ok(len(ev)==1,'one request per week covers every calendar',calls[n:])
  # wrong key -> clear message, no crash
  state['key']='nope';await pg.reload();await pg.wait_for_timeout(2500)
  row=await pg.locator('#calrow').inner_text();ok('isn’t working' in row,'bad key shows a link message',row)
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','gcal_link.png'))
  ok(not errs,'no script errors',errs[:3]);await b.close()
asyncio.run(main());srv.terminate()
print('\nFAILS',sum(r.startswith('FAIL') for r in res))
