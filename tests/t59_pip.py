import asyncio,os,subprocess,time,json
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
srv=subprocess.Popen(['python3','-m','http.server','8787','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
async def main():
 async with async_playwright() as P:
  b=await P.chromium.launch();ctx=await b.new_context(viewport={'width':1280,'height':900});pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.goto('http://127.0.0.1:8787/');await pg.wait_for_timeout(800)
  await pg.evaluate("""(()=>{const d=new Date(),t=d.getHours()*60+d.getMinutes(),iso=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
    const st={projects:{pa:{id:'pa',kind:'work',name:'Kalorama EOI',group:'g1',tasks:[{id:'t1',text:'Draft concept statement',done:false},{id:'t2',text:'Budget table',done:false}]}},pebbles:[{id:'a',pid:'pa',date:iso,start:t-20,dur:50,pomo:true,trans:true,session:['t1','t2']}],groups:[{id:'g1',name:'TARRMACstudio',color:0}],notes:[],histMonths:[],settings:null,v:8,savedAt:Date.now()};
    delete st.settings;localStorage.setItem('pebble-planner-v1',JSON.stringify(st))})()""")
  await pg.reload();await pg.wait_for_timeout(1500)
  await pg.click('#pipBtn');await pg.wait_for_timeout(1500)
  pages=ctx.pages;print('pages',len(pages))
  for p in pages:
    if p!=pg:
      await p.set_viewport_size({'width':330,'height':178});await p.wait_for_timeout(500);await p.screenshot(path=os.path.join(ROOT,'tests','shots','pip.png'))
      await p.locator('.pip-task input').click();await p.wait_for_timeout(800)
      print('after tick, task shown:',await p.inner_text('.pip-task'))
  await pg.screenshot(path=os.path.join(ROOT,'tests','shots','pip-main.png'),clip={'x':0,'y':60,'width':1280,'height':140})
  print('errors',errs);await b.close()
asyncio.run(main());srv.terminate()
