import streamlit as st
import requests
import re
import time
from functools import lru_cache

# ─── ページ設定 ────────────────────────────────────────
st.set_page_config(
    page_title="ぼくのともだち",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── 定数／モデル設定 ──────────────────────────────────
API_KEY    = st.secrets["general"]["api_key"]
MODEL_NAME = "gemini-2.0-flash-lite"

# ─── CSS／JavaScript 埋め込み ───────────────────────────
st.markdown("""
<style>
  /* チャット領域 */
  #chat-container {
    display: flex;
    flex-direction: column;
    padding: 10px;
    padding-bottom: 120px;  /* 入力欄と重ならない余白 */
    height: calc(100vh - 140px);
    overflow-y: auto;
  }
  .chat-bubble {
    max-width: 70%;
    margin: 6px;
    padding: 10px 14px;
    border-radius: 18px;
    word-wrap: break-word;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.4;
  }
  .bubble-yukari { background-color: #DCF8C6; align-self: flex-start; }
  .bubble-shinya { background-color: #E0F7FA; align-self: flex-end; }
  .bubble-minoru { background-color: #FCE4EC; align-self: flex-start; }

  /* ローディングスケルトン */
  .chat-bubble.loading {
    background-color: #f0f0f0;
    color: transparent;
    position: relative;
  }
  .chat-bubble.loading::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(
      90deg,
      rgba(255,255,255,0) 0%,
      rgba(255,255,255,0.6) 50%,
      rgba(255,255,255,0) 100%
    );
    animation: shimmer 1.2s infinite;
    border-radius: 18px;
  }
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  /* 入力エリア固定 */
  #input-area {
    position: fixed;
    bottom: 0; left: 0;
    width: 100%;
    background-color: #fff;
    box-shadow: 0 -2px 6px rgba(0,0,0,0.1);
    padding: 12px 20px;
  }
  /* ラベルは必須だが、ここで非表示に */
  #input-area label {
    display: none !important;
  }
  #input-area textarea {
    width: 80%; height: 50px;
    resize: none;
    border-radius: 12px;
    border: 1px solid #ccc;
    padding: 8px;
    font-size: 16px;
  }
  #input-area button {
    width: 15%;
    margin-left: 5%;
    padding: 10px;
    font-size: 16px;
    border: none;
    border-radius: 12px;
    background-color: #4CAF50;
    color: white;
    cursor: pointer;
  }
</style>
<script>
  // 自動スクロール
  function scrollToBottom() {
    const el = document.getElementById("chat-container");
    if (el) el.scrollTop = el.scrollHeight;
  }
  window.addEventListener("DOMContentLoaded", scrollToBottom);
</script>
""", unsafe_allow_html=True)

# ─── 同期API呼び出し＋リトライ ─────────────────────────────
@lru_cache(maxsize=128)
def fetch_response(prompt: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/"
        f"v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    )
    headers = {"Content-Type": "application/json"}
    payload = {"contents":[{"parts":[{"text":prompt}]}]}
    for retry in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            cands = data.get("candidates", [])
            if not cands:
                return "（回答なし）"
            content = cands[0]["content"]
            if isinstance(content, dict) and "parts" in content:
                return "".join(p.get("text","") for p in content["parts"]).strip()
            return str(content).strip()
        except Exception:
            time.sleep(2 ** retry)
    return "通信エラーが発生しました。オフラインモードです。"

# ─── UI描画ヘルパー ─────────────────────────────────────
def render_loading_skeleton():
    st.markdown(
        '<div class="chat-bubble loading">　</div>',
        unsafe_allow_html=True
    )

def render_chat_bubble(name: str, msg: str):
    cls = {"ゆかり":"bubble-yukari","しんや":"bubble-shinya","みのる":"bubble-minoru"}[name]
    safe = msg.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    st.markdown(f'<div class="chat-bubble {cls}">{safe}</div>', unsafe_allow_html=True)

# ─── セッションステート初期化 ─────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []  # List[Tuple[str,str]]

# ─── 入力フォーム＋送信処理 ─────────────────────────────────
st.markdown('<div id="input-area">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True):
    user_q = st.text_area(
        label="質問",        # 空文字ではなく必須
        placeholder="質問を入力…",
        key="input_q",
        height=50
    )
    send_btn = st.form_submit_button("送信")
st.markdown('</div>', unsafe_allow_html=True)

if send_btn and user_q.strip():
    st.session_state.history.append(("user", user_q))
    render_loading_skeleton()
    resp = fetch_response(user_q)
    st.session_state.history.append(("ai", resp))
    st.session_state.input_q = ""
    st.rerun()

# ─── チャット履歴表示エリア ─────────────────────────────────
st.markdown('<div id="chat-container">', unsafe_allow_html=True)
for role, text in st.session_state.history:
    if role == "user":
        render_chat_bubble("しんや", text)
    else:
        render_chat_bubble("ゆかり", text)
st.markdown('</div>', unsafe_allow_html=True)
