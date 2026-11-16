import json,os,sys,time,urllib.request,urllib.parse
API="https://graph.facebook.com/v23.0"; H=os.path.dirname(os.path.abspath(__file__))
T=open(os.path.join(H,"token_insights.txt")).read().strip(); IG=json.load(open(os.path.join(H,"config.json"),encoding="utf8"))["ig_id"]
capfile=sys.argv[1]; vids=sys.argv[2:]
cap=open(capfile,encoding="utf8").read().strip()
def post(path,**p):
    p["access_token"]=T
    try: return json.load(urllib.request.urlopen(urllib.request.Request(f"{API}/{path}",data=urllib.parse.urlencode(p).encode(),method="POST")))
    except urllib.error.HTTPError as e: print(e.read().decode()[:400]); raise
def get(path,**p): p["access_token"]=T; return json.load(urllib.request.urlopen(f"{API}/{path}?"+urllib.parse.urlencode(p)))
def wait(cid):
    for _ in range(60):
        s=get(cid,fields="status_code"); 
        if s.get("status_code")=="FINISHED": return
        if s.get("status_code")=="ERROR": print(get(cid,fields="status")); sys.exit(1)
        time.sleep(5)
kids=[]
for v in vids:
    c=post(f"{IG}/media",media_type="VIDEO",is_carousel_item="true",upload_type="resumable")
    data=open(v,"rb").read()
    r=json.load(urllib.request.urlopen(urllib.request.Request(c["uri"],data=data,method="POST",headers={"Authorization":f"OAuth {T}","offset":"0","file_size":str(len(data))})))
    print(os.path.basename(v),r.get("success")); kids.append(c["id"])
for k in kids: wait(k)
c=post(f"{IG}/media",media_type="CAROUSEL",children=",".join(kids),caption=cap)["id"]; wait(c)
m=post(f"{IG}/media_publish",creation_id=c); print("published",m["id"]); print(get(m["id"],fields="permalink"))
