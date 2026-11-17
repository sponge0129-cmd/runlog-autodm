import json,os,sys,time,urllib.request,urllib.parse,urllib.error,subprocess
D=os.path.dirname(os.path.abspath(__file__))
API="https://graph.facebook.com/v23.0"
T=open(os.path.join(D,"token_insights.txt")).read().strip()
CFG=os.path.join(D,"config.json")
IG=json.load(open(CFG,encoding="utf8"))["ig_id"]
F="H:/내 드라이브/인스타_AI작업실/게시물/20261117_마케터도구9/"
LINK="https://viridian-bellflower-eca.notion.site/AI-9-41b593cca189811fb9d1e4e2aacacb69"
NAME="로기의 일주일 — 마케터 AI 도구 9개, 사용법·요청문"
COVER="https://raw.githubusercontent.com/sponge0129-cmd/runlog-autodm/master/media/mk9_cover.jpg"
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
subprocess.run(["git","-C",D,"add","config.json"]); subprocess.run(["git","-C",D,"commit","-qm","마케터9 릴스 자료 연결"]); subprocess.run(["git","-C",D,"push","-q"])
print("linked",time.strftime("%H:%M:%S"),flush=True)
print(get(mid,fields="permalink,timestamp"))

# raw 반영 확인
for i in range(40):
    try:
        r=urllib.request.urlopen(f"https://raw.githubusercontent.com/sponge0129-cmd/runlog-autodm/master/config.json?t={time.time()}").read().decode()
        if mid in r: print("raw ok",time.strftime("%H:%M:%S"),flush=True); break
    except Exception as e: print("raw err",e)
    time.sleep(15)
# 고정용 안내 댓글
print("comment",post(f"{mid}/comments",message="📌 댓글에 「도구」 남겨 주시면 9개 사용법이랑 바로 쓰는 요청문을 DM으로 보내 드려요!"),flush=True)
print("comments now",get(f"{mid}/comments",fields="id,text,username,timestamp"))
