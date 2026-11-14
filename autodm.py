# Runlog 자동 DM — 댓글 감지 → 팔로우 확인 → 자료 링크 (무료, 직접 만든 프로그램)
# 시스템 사용자 토큰(만료 없음) + graph.facebook.com, 몇 분마다 내 계정 댓글을 직접 확인.
import json, os, time, urllib.parse, urllib.request

API = "https://graph.facebook.com/v23.0"
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(HERE, "token.txt"), encoding="utf8").read().strip()
STATE = os.path.join(HERE, "state.json")
CFG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf8"))
IG_ID = CFG["ig_id"]                     # runlog.ai 인스타 계정 번호
DAYS = CFG.get("days", 7)                # 개인 답장은 댓글 후 7일 안에만 가능
DRY = os.environ.get("DRY") == "1"       # 1이면 보내지 않고 할 일만 출력

def call(path, method="GET", **params):
    params["access_token"] = TOKEN
    if method == "GET":
        req = urllib.request.Request(f"{API}/{path}?{urllib.parse.urlencode(params)}")
    else:
        body = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v) for k, v in params.items()}
        req = urllib.request.Request(f"{API}/{path}", urllib.parse.urlencode(body).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print("API 오류", path, e.code, e.read().decode("utf8", "ignore")[:300])
        return None

def send(recipient, text):
    if DRY:
        print("  [시험] 보낼 DM →", recipient, "|", text.replace("\n", " / ")[:80]); return {"dry": 1}
    return call(f"{IG_ID}/messages", "POST", recipient=recipient, message={"text": text})

def ts(s): return time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))

try: st = json.load(open(STATE, encoding="utf8"))
except FileNotFoundError: st = {"seen": [], "pending": {}, "done": []}

me = call(IG_ID, fields="username") or {}
ME_NAME = me.get("username", "runlog.ai")
cut = time.time() - DAYS * 86400

# 게시물별 자료: config의 posts에 있으면 그것, 없으면 default
def post_info(mid): return CFG.get("posts", {}).get(mid) or CFG["default"]

FIRST = ("댓글 고마워요! 🙌 자료는 @{me} 팔로워분께 보내 드려요.\n"
         "팔로우하셨다면 이 메시지에 아무 말이나 답장 주세요. 바로 링크 보내 드릴게요!")

# 1) 최근 게시물의 새 댓글 → 첫 DM (댓글 하나당 1번, 같은 사람은 1번)
media = (call(f"{IG_ID}/media", fields="id,timestamp", limit=20) or {}).get("data", [])
for m in media:
    if ts(m["timestamp"]) < cut - 86400 * 30: continue
    res = call(f"{m['id']}/comments", fields="id,text,timestamp,from{id,username}", limit=50) or {}
    for c in res.get("data", []):
        cid, who = c["id"], c.get("from", {})
        uid = who.get("id")
        if cid in st["seen"] or not uid or who.get("username") == ME_NAME: continue
        st["seen"].append(cid)
        if ts(c["timestamp"]) < cut: continue
        if uid in st["done"] or uid in st["pending"]: continue
        pi = post_info(m["id"])
        r = send({"comment_id": cid}, FIRST.format(me=ME_NAME, name=pi["name"], link=pi["link"]))
        if r: st["done"].append(uid)
        print("첫 DM", who.get("username"), "ok" if r else "실패")

# 2) 답장한 사람 → 팔로우 확인 → 링크
def replied(uid):
    conv = call(f"{IG_ID}/conversations", platform="instagram", user_id=uid,
                fields="messages{from,created_time}") or {}
    for cv in conv.get("data", []):
        for msg in cv.get("messages", {}).get("data", []):
            if msg.get("from", {}).get("id") == uid: return True
    return False

for uid, info in list(st["pending"].items()):
    if not replied(uid): continue
    prof = call(uid, fields="username,is_user_follow_business") or {}
    post = post_info(info["post"])
    if prof.get("is_user_follow_business"):
        txt = f"팔로우 확인했어요 ✅\n「{post['name']}」 여기 있어요 👇\n{post['link']}"
        if send({"id": uid}, txt):
            st["done"].append(uid); st["pending"].pop(uid)
            print("링크 전송", info["user"])
    elif not info.get("nudged"):
        send({"id": uid}, f"아직 팔로우가 확인되지 않아요 🥲 @{ME_NAME} 팔로우 후 한 번 더 답장 주세요!")
        info["nudged"] = int(time.time())
        print("팔로우 요청", info["user"])

st["seen"] = st["seen"][-5000:]
if not DRY:
    json.dump(st, open(STATE, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(time.strftime("%m-%d %H:%M"), "완료: 게시물", len(media), "/ 대기", len(st["pending"]), "/ 전송", len(st["done"]))
