import streamlit as st
import requests
import re

# ========================
#    定数／設定
# ========================
API_KEY    = st.secrets["general"]["api_key"]
MODEL_NAME = "gemini-2.0-flash-lite"   # 高速 Flash-Lite モデル
PERSONAS   = ["ゆかり", "しんや", "みのる"]

# ========================
#    CSS／JS 埋め込み
# ========================
st.markdown("""
<style>
  /* チャット領域 */
  #chat-container {
    display: flex;
    flex-direction: column;
    padding: 10px;
    padding-bottom: 100px;  /* 入力欄と重ならない余白 */
    height: calc(100vh - 120px);
    overflow-y: auto;
  }
  .chat-bubble {
    max-width: 70%;
    margin: 5px;
    padding: 10px 14px;
    border-radius: 16px;
    word-wrap: break-word;
    box-shadow: 0 1px 1px rgba(0,0,0,0.1);
  }
  .bubble-yukari { background-color: #DCF8C6; align-self: flex-start; }
  .bubble-shinya { background-color: #E0F7FA; align-self: flex-end; }
  .bubble-minoru { background-color: #FCE4EC; align-self: flex-start; }

  /* 入力エリア固定 */
  #input-area {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #FFFFFF;
    padding: 10px 20px;
    box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
  }
</style>
<script>
  // 自動スクロール
  function scrollToBottom() {
    const el = document.getElementById("chat-container");
    if (el) el.scrollTop = el.scrollHeight;
  }
  window.onload = scrollToBottom;
</script>
""", unsafe_allow_html=True)

# ========================
#    セッションステート初期化
# ========================
if "discussion" not in st.session_state:
    st.session_state.discussion = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""

# ========================
#    質問分析・パラメータ調整
# ========================
def analyze_question(q: str) -> int:
    score = 0
    for w in ["困った","悩み","苦しい","辛い"]:
        if w in q: score += 1
    for w in ["理由","原因","仕組み","方法"]:
        if w in q: score -= 1
    return score

def adjust_params(q: str) -> dict:
    if analyze_question(q) > 0:
        return {
            "ゆかり": {"style": "情熱的", "detail": "感情に寄り添う回答"},
            "しんや": {"style": "共感的", "detail": "心情を重視した解説"},
            "みのる": {"style": "柔軟",   "detail": "多面的な視点での提案"},
        }
    else:
        return {
            "ゆかり": {"style": "論理的", "detail": "具体的な解説を重視"},
            "しんや": {"style": "分析的", "detail": "データ・事実に基づく説明"},
            "みのる": {"style": "客観的", "detail": "中立的な視点からの考察"},
        }

# ========================
#    Gemini API 呼び出し
# ========================
def call_gemini(prompt: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/"
        f"v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        if res.status_code != 200:
            return f"APIエラー: ステータスコード {res.status_code}"
        data = res.json()
        cands = data.get("candidates", [])
        if not cands:
            return "（回答なし）"
        content = cands[0].get("content", "")
        if isinstance(content, dict):
            parts = content.get("parts", [])
            return "".join(p.get("text","") for p in parts).strip()
        return str(content).strip()
    except Exception as e:
        return f"通信失敗: {e}"

# ========================
#    会話生成・表示ヘルパー
# ========================
def gen_discussion(q: str) -> str:
    params = adjust_params(q)
    prompt = f"【ユーザーの質問】\n{q}\n\n"
    for name, cfg in params.items():
        prompt += f"{name}は【{cfg['style']}】で、{cfg['detail']}。\n"
    prompt += "\n以上の設定で3人が友達同士のように自然に会話してください。"
    return call_gemini(prompt)

def gen_summary(disc: str) -> str:
    prompt = f"以下は3人の会話です：\n{disc}\n\nこの内容を踏まえたまとめを自然な日本語で作成してください。"
    return call_gemini(prompt)

def render_bubbles(text: str):
    for line in text.split("\n"):
        m = re.match(r"^(ゆかり|しんや|みのる):\s*(.+)$", line)
        if m:
            name, msg = m.groups()
            cls = {
                "ゆかり":"bubble-yukari",
                "しんや":"bubble-shinya",
                "みのる":"bubble-minoru"
            }[name]
            st.markdown(f'<div class="chat-bubble {cls}">{msg}</div>', unsafe_allow_html=True)

# ========================
#    アプリ本体
# ========================
st.title("ぼくのともだち")

# — チャット履歴表示エリア —
st.markdown('<div id="chat-container">', unsafe_allow_html=True)
if st.session_state.discussion:
    render_bubbles(st.session_state.discussion)
if st.session_state.summary:
    st.markdown(f'**まとめ:** {st.session_state.summary}')
st.markdown('</div>', unsafe_allow_html=True)

# — 入力エリア（固定） —
st.markdown('<div id="input-area">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True, enter_to_submit=True):
    user_q = st.text_area(
        label="質問",
        placeholder="質問を入力…",
        key="input_q",
        height=150,
        label_visibility="collapsed"
    )
    send_btn    = st.form_submit_button("送信")
    summary_btn = st.form_submit_button("まとめ表示")
st.markdown('</div>', unsafe_allow_html=True)

# — 送信処理 —
if send_btn and user_q.strip():
    st.session_state.discussion = gen_discussion(user_q)
    st.session_state.summary    = ""
    st.experimental_rerun()
if summary_btn and st.session_state.discussion:
    st.session_state.summary = gen_summary(st.session_state.discussion)
    st.experimental_rerun()
