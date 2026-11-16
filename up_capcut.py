import json,os,sys,time,urllib.request,urllib.parse,urllib.error,subprocess
D=os.path.dirname(os.path.abspath(__file__))
API="https://graph.facebook.com/v23.0"
T=open(os.path.join(D,"token_insights.txt")).read().strip()
CFG=os.path.join(D,"config.json")
IG=json.load(open(CFG,encoding="utf8"))["ig_id"]
F="H:/내 드라이브/인스타_AI작업실/게시물/20261115_캡컷대신클로드/"
LINK="https://viridian-bellflower-eca.notion.site/419593cca18981978e1cc6a6f22d835d"
NAME="편집 앱 0번 — 클로드한테 친 명령어 7줄"
COVER="https://raw.githubusercontent.com/sponge0129-cmd/runlog-autodm/master/media/capcut_cover.jpg"
cap=open(F+"캡션.txt",encoding="utf8").read().strip()
def call(req):
    try: return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        print("ERR",e.code,e.read().decode()[:800]); sys.exit(1)
def post(path,**p):
    p["access_token"]=T
    return call(urllib.request.Request(f"{API}/{path}",data=urllib.parse.urlencode(p).encode(),method="POST"))
def get(path,**p):
    p["access_token"]=T; return call(f"{API}/{path}?"+urllib.parse.urlencode(p))
c=post(f"{IG}/media",media_type="REELS",upload_type="resumable",caption=cap,share_to_feed="true",cover_url=COVER)
cid=c["id"]; print("container",cid,flush=True)
data=open(F+"reel.mp4","rb").read()
print("upload",call(urllib.request.Request(f"https://rupload.facebook.com/ig-api-upload/v23.0/{cid}",data=data,method="POST",headers={"Authorization":f"OAuth {T}","offset":"0","file_size":str(len(data))})),flush=True)
for i in range(60):
    s=get(cid,fields="status_code,status")
    if s.get("status_code")=="FINISHED": break
    if s.get("status_code")=="ERROR": print(s); sys.exit(1)
    time.sleep(10)
m=post(f"{IG}/media_publish",creation_id=cid); mid=m["id"]; print("published",mid,flush=True)
# 즉시 자동DM 연결
cfg=json.load(open(CFG,encoding="utf8"))
cfg["posts"][mid]={"link":LINK,"name":NAME}
json.dump(cfg,open(CFG,"w",encoding="utf8"),ensure_ascii=False,indent=2)
subprocess.run(["git","-C",D,"add","config.json"]); subprocess.run(["git","-C",D,"commit","-qm","캡컷 대신 클로드 릴스 자료 연결"]); subprocess.run(["git","-C",D,"push","-q"])
print("linked",time.strftime("%H:%M:%S"),flush=True)
print(get(mid,fields="permalink,timestamp"))
