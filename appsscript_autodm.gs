// Runlog 자동 DM — 구글 Apps Script판 (1분마다 구글 서버에서 실행, 컴퓨터 꺼도 됨)
// 토큰: 프로젝트 설정 → 스크립트 속성 IG_TOKEN
// 게시물별 자료 링크: 깃허브 config.json 을 읽음 (저장소에서 고치면 바로 반영)
const API = "https://graph.facebook.com/v23.0";
const CONFIG_URL = "https://raw.githubusercontent.com/sponge0129-cmd/runlog-autodm/master/config.json";
const FIRST = "댓글 고마워요! 🙌 자료는 @{me} 팔로워분께 보내 드려요.\n팔로우하셨다면 이 메시지에 아무 말이나 답장 주세요. 바로 링크 보내 드릴게요!";

function token_() { return PropertiesService.getScriptProperties().getProperty("IG_TOKEN"); }

function call_(path, method, params) {
  params = params || {};
  params.access_token = token_();
  const q = Object.keys(params).map(k => {
    const v = typeof params[k] === "object" ? JSON.stringify(params[k]) : params[k];
    return encodeURIComponent(k) + "=" + encodeURIComponent(v);
  }).join("&");
  const opt = { muteHttpExceptions: true, method: method === "POST" ? "post" : "get" };
  let url = API + "/" + path;
  if (method === "POST") { opt.payload = q; opt.contentType = "application/x-www-form-urlencoded"; }
  else url += "?" + q;
  const r = UrlFetchApp.fetch(url, opt);
  if (r.getResponseCode() >= 300) { console.log("API 오류", path, r.getResponseCode(), r.getContentText().slice(0, 300)); return null; }
  return JSON.parse(r.getContentText());
}

// 상태 저장: 9KB 제한이 있어 여러 칸에 나눠 저장
function load_() {
  const p = PropertiesService.getScriptProperties();
  const n = Number(p.getProperty("st_n") || 0);
  let s = ""; for (let i = 0; i < n; i++) s += p.getProperty("st_" + i) || "";
  return s ? JSON.parse(s) : { wm: 0, pending: {}, done: [], replied: [] };
}
function save_(st) {
  const p = PropertiesService.getScriptProperties();
  const s = JSON.stringify(st), parts = {};
  let n = 0; for (let i = 0; i < s.length; i += 8000) parts["st_" + (n++)] = s.slice(i, i + 8000);
  parts.st_n = String(n);
  p.setProperties(parts);
}

function run() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try { main_(); } finally { lock.releaseLock(); }
}

function main_() {
  const cfg = JSON.parse(UrlFetchApp.fetch(CONFIG_URL + "?t=" + Date.now()).getContentText());
  const IG = cfg.ig_id, DAYS = cfg.days || 7;
  const info = mid => (cfg.posts || {})[mid] || cfg.default;
  const st = load_();
  const me = (call_(IG, "GET", { fields: "username" }) || {}).username || "runlog.ai";
  const now = Date.now(), cut = now - DAYS * 86400000;
  const since = Math.max(cut, (st.wm || 0) - 15 * 60000);   // 15분 겹쳐 읽어 늦게 잡히는 댓글도 놓치지 않음
  let newest = st.wm || 0;

  // 1) 새 댓글 → 첫 DM (사람·게시물마다 1번)
  const media = ((call_(IG + "/media", "GET", { fields: "id,timestamp", limit: 20 }) || {}).data) || [];
  media.forEach(m => {
    if (Date.parse(m.timestamp) < cut - 30 * 86400000) return;
    const cs = ((call_(m.id + "/comments", "GET", { fields: "id,text,timestamp,from{id,username}", limit: 50 }) || {}).data) || [];
    cs.forEach(c => {
      const t = Date.parse(c.timestamp), who = c.from || {};
      if (t > newest) newest = t;
      if (t < since || !who.id || who.username === me) return;
      const key = who.id + ":" + m.id;
      if (st.done.indexOf(key) >= 0 || st.pending[key] || st.replied.indexOf(c.id) >= 0) return;
      const r = call_(IG + "/messages", "POST", { recipient: { comment_id: c.id }, message: { text: FIRST.replace("{me}", me).replace("{name}", info(m.id).name).replace("{link}", info(m.id).link) } });
      st.replied.push(c.id);
      if (r) st.done.push(key);
      console.log("첫 DM", who.username, r ? "ok" : "실패");
    });
  });
  st.wm = Math.max(st.wm || 0, Math.min(newest, now));

  // 2) 답장한 사람 → 팔로우 확인 → 링크
  Object.keys(st.pending).forEach(key => {
    const p = st.pending[key];
    if (now - p.at > DAYS * 86400000) { delete st.pending[key]; return; }
    const conv = call_(IG + "/conversations", "GET", { platform: "instagram", user_id: p.uid, fields: "messages{from,created_time}" }) || {};
    const replied = (conv.data || []).some(cv => ((cv.messages || {}).data || []).some(x => (x.from || {}).id === p.uid && Date.parse(x.created_time) > p.at - 60000));
    if (!replied) return;
    const prof = call_(p.uid, "GET", { fields: "username,is_user_follow_business" }) || {};
    const it = info(p.post);
    if (prof.is_user_follow_business) {
      if (call_(IG + "/messages", "POST", { recipient: { id: p.uid }, message: { text: "팔로우 확인했어요 ✅\n「" + it.name + "」 여기 있어요 👇\n" + it.link } })) {
        st.done.push(key); delete st.pending[key]; console.log("링크 전송", p.user);
      }
    } else if (!p.nudged) {
      call_(IG + "/messages", "POST", { recipient: { id: p.uid }, message: { text: "아직 팔로우가 확인되지 않아요 🥲 @" + me + " 팔로우 후 한 번 더 답장 주세요!" } });
      p.nudged = now; console.log("팔로우 요청", p.user);
    }
  });

  st.done = st.done.slice(-1500); st.replied = st.replied.slice(-1500);
  save_(st);
  console.log("완료: 게시물", media.length, "/ 대기", Object.keys(st.pending).length, "/ 전송", st.done.length);
}

// 한 번만 실행: 1분마다 run 을 돌리는 트리거 설치
function setup() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("run").timeBased().everyMinutes(1).create();
}
