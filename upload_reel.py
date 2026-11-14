import json,os,sys,time,urllib.request,urllib.parse
API="https://graph.facebook.com/v23.0"
T=open(os.path.join(os.path.dirname(__file__),"token.txt")).read().strip()
IG=json.load(open(os.path.join(os.path.dirname(__file__),"config.json"),encoding="utf8"))["ig_id"]
video,capfile,thumb=sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1500
cap=open(capfile,encoding="utf8").read().strip()
def post(path,**p):
    p["access_token"]=T
    r=urllib.request.urlopen(urllib.request.Request(f"{API}/{path}",data=urllib.parse.urlencode(p).encode(),method="POST"))
    return json.load(r)
def get(path,**p):
    p["access_token"]=T; return json.load(urllib.request.urlopen(f"{API}/{path}?"+urllib.parse.urlencode(p)))
c=post(f"{IG}/media",media_type="REELS",upload_type="resumable",caption=cap,share_to_feed="true",thumb_offset=str(thumb))
cid=c["id"]; print("container",cid)
data=open(video,"rb").read()
req=urllib.request.Request(c["uri"],data=data,method="POST",headers={"Authorization":f"OAuth {T}","offset":"0","file_size":str(len(data))})
print("upload",json.load(urllib.request.urlopen(req)))
for i in range(60):
    s=get(cid,fields="status_code,status"); print(s.get("status_code"))
    if s.get("status_code")=="FINISHED": break
    if s.get("status_code")=="ERROR": print(s); sys.exit(1)
    time.sleep(10)
m=post(f"{IG}/media_publish",creation_id=cid); print("published",m["id"])
print(get(m["id"],fields="permalink"))
