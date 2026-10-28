"""Bump the offline worker's version and refresh its file list. Run before every publish."""
import os,re,json,time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sw=os.path.join(ROOT,'sw.js');s=open(sw).read()
files=['./','index.html','manifest.webmanifest']+['icons/'+f for f in sorted(os.listdir(os.path.join(ROOT,'icons')))]+['sounds/'+f for f in sorted(os.listdir(os.path.join(ROOT,'sounds')))]
ver='pebbles-'+time.strftime('%Y%m%d-%H%M%S')
s=re.sub(r"const VERSION='[^']*';",f"const VERSION='{ver}';",s);s=re.sub(r"const FILES=\[.*?\];","const FILES="+json.dumps(files)+";",s,flags=re.S)
open(sw,'w').write(s);print('sw.js ->',ver)
