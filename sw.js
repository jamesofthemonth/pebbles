/* Pebbles service worker. Bump VERSION whenever you publish, so installed copies pick up the new files.
   Pages: network first (you get updates when online), falling back to the saved copy offline.
   Everything else: saved copy first. Your plan itself lives in the browser and your backup folder, never in this cache. */
const VERSION='pebbles-20261029-173456';
const FILES=["./", "index.html", "manifest.webmanifest", "icons/favicon.svg", "icons/icon-180.png", "icons/icon-192.png", "icons/icon-32.png", "icons/icon-512.png", "icons/maskable-512.png", "sounds/bell.mp3", "sounds/deep-chime.mp3", "sounds/deep-click.mp3", "sounds/drop-error.mp3", "sounds/futuristic-beep.mp3", "sounds/futuristic-tap.mp3", "sounds/glass-ping.mp3", "sounds/mission-complete.mp3", "sounds/notification.mp3", "sounds/pop-minimal.mp3", "sounds/pop-up-open.mp3", "sounds/soft-notification.mp3", "sounds/swipe-cancel.mp3", "sounds/swipe-soft.mp3", "sounds/tap-light.mp3"];
self.addEventListener('install',e=>{e.waitUntil(caches.open(VERSION).then(c=>c.addAll(FILES.map(f=>new Request(f,{cache:'reload'})))).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==VERSION&&k!=='pebbles-fonts').map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);
  if(r.mode==='navigate'){e.respondWith(fetch(r.url,{cache:'no-cache',credentials:'same-origin'}).then(res=>{if(res.ok){const cp=res.clone();caches.open(VERSION).then(c=>c.put('index.html',cp))}return res}).catch(()=>caches.match('index.html')));return}
  if(u.origin===location.origin){e.respondWith(caches.match(r).then(hit=>hit||fetch(r).then(res=>{const cp=res.clone();caches.open(VERSION).then(c=>c.put(r,cp));return res})));return}
  if(/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)){e.respondWith(caches.open('pebbles-fonts').then(c=>c.match(r).then(hit=>{const net=fetch(r).then(res=>{c.put(r,res.clone());return res}).catch(()=>hit);return hit||net})))}
});
