import asyncio,json,os,subprocess,time,datetime,traceback
from playwright.async_api import async_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
src=open(os.path.join(ROOT,'index.html')).read()
open(os.path.join(ROOT,'tests','app.html'),'w').write(src)
os.makedirs(os.path.join(ROOT,'tests','shots'),exist_ok=True)
def ev(d,h,m,title,cal='me'):
  return {"id":f"{cal}{d}{h}{m}","summary":title,"start":{"dateTime":f"{d}T{h:02d}:{m:02d}:00+11:00"},"end":{"dateTime":f"{d}T{h+1:02d}:{m:02d}:00+11:00"}}
EVENTS=[ev('2026-11-02',10,0,'Site meeting with council'),ev('2026-11-03',14,0,'Dentist'),ev('2026-11-04',9,30,'Jon weekly'),ev('2026-11-05',16,0,'TARRMAC review','tm')]
INIT="""
(()=>{try{localStorage.setItem('pebble-planner-v1-demo','1')}catch(e){}const RD=Date;let off=+(localStorage.getItem('__off')||0);
 window.__setNow=ms=>{off=ms-RD.now();localStorage.setItem('__off',String(off))};
 class D extends RD{constructor(...a){if(a.length===0)super(RD.now()+off);else super(...a)}static now(){return RD.now()+off}}
 window.Date=D;
 const mdb=()=>JSON.parse(localStorage.getItem('__mdb')||'{}'),wdb=o=>localStorage.setItem('__mdb',JSON.stringify(o));const subs={};
 const doc=path=>({get:async()=>{const v=mdb()[path];return {exists:!!v,data:()=>v?JSON.parse(JSON.stringify(v)):undefined,metadata:{}}},
   set:async v=>{const o=mdb();o[path]=JSON.parse(JSON.stringify(v));wdb(o);(subs[path]||[]).forEach(cb=>cb({exists:true,data:()=>JSON.parse(JSON.stringify(v)),metadata:{hasPendingWrites:false}}))},
   onSnapshot:(cb)=>{(subs[path]=subs[path]||[]).push(cb);setTimeout(()=>{const v=mdb()[path];cb({exists:!!v,data:()=>v,metadata:{}})},50);return ()=>{}}});
 const EV=%s;
 window.claude={use:async n=>{
  if(n==='db')return {doc};
  if(n==='user')return {id:async()=>'james'};
  if(n==='mcp')return {callTool:async(server,tool,input)=>{if(tool==='list_calendars')return {payload:{calendars:[{id:'me',summary:'james@jamesmorton.com.au'},{id:'tm',summary:'jamesmorton@tarrmacstudio.com'}]}};
    const s=input.startTime.slice(0,10),e=input.endTime.slice(0,10);return {payload:{events:EV.filter(x=>(input.calendarId==='tm')===(x.id.startsWith('tm'))&&x.start.dateTime.slice(0,10)>=s&&x.start.dateTime.slice(0,10)<=e)}}}};
  if(n==='downloads')return {save:async()=>{}};
  return null}};
})();""" % json.dumps(EVENTS)
class Sim:
  def __init__(s):s.log=[];s.fails=0;s.errs=[]
  def check(s,ok,what,detail=''):
    s.log.append(('PASS' if ok else 'FAIL')+'  '+what+(('  ['+str(detail)+']') if detail!='' else ''));s.fails+=0 if ok else 1;print(s.log[-1],flush=True)
  def note(s,t):s.log.append('---- '+t);print(s.log[-1],flush=True)
  async def state(s,pg):
    await pg.wait_for_timeout(700);return await pg.evaluate("JSON.parse(localStorage.getItem('pebble-planner-v1'))")
  async def at(s,pg,iso,reload=True):
    ms=int(datetime.datetime.fromisoformat(iso).timestamp()*1000)
    await pg.evaluate(f"window.__setNow({ms})")
    if reload:await pg.reload();await pg.wait_for_timeout(1400)
  async def shot(s,pg,name):await pg.screenshot(path=os.path.join(ROOT,'tests','shots',name+'.png'),full_page=False)
