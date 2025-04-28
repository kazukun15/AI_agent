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

# ─── レスポンシブ用ビューポート ────────────────────────
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
""", unsafe_allow_html=True)

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
    padding-bottom: calc(100px + env(safe-area-inset-bottom));
    height: calc(100vh - 120px);
    overflow-y: auto;
  }
  .chat-bubble {
    max-width: 90%;
    margin: 6px 0;
    padding: 14px 18px;
    border-radius: 20px;
    word-wrap: break-word;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    font-size: 20px;
    line-height: 1.5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }
  .bubble-yukari { background-color: #DCF8C6; align-self: flex-start; }
  .bubble-shinya { background-color: #E0F7FA; align-self: flex-end; }
  .bubble-minoru { background-color: #FCE4EC; align-self: flex-start; }

  .chat-bubble.loading {
    background-color: #e0e0e0;
    color: transparent;
    position: relative;
  }
  .chat-bubble.loading::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
      90deg,
      rgba(255,255,255,0) 0%,
      rgba(255,255,255,0.6) 50%,
      rgba(255,255,255,0) 100%
    );
    animation: shimmer 1.2s infinite;
    border-radius: 20px;
  }
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  #input-area {
    position: fixed;
    bottom: env(safe-area-inset-bottom);
    left: 0;
    width: 100%;
    background-color: #fff;
    box-shadow: 0 -2px 6px rgba(0,0,0,0.1);
    padding: 8px 12px;
  }
  #input-area label { display: none !important; }
  #input-area input {
    width: 70%;
    height: 56px;
    padding: 0 14px;
    font-size: 20px;
    border-radius: 28px;
    border: 1px solid #ccc;
    vertical-align: middle;
  }
  #input-area button {
    width: 25%;
    height: 56px;
    margin-left: 5%;
    font-size: 20px;
    border: none;
    border-radius: 28px;
    background-color: #4CAF50;
    color: #fff;
    cursor: pointer;
  }
</style>
<script>
// 自動スクロール
const scrollToBottom = () => {
  const el = document.getElementById("chat-container");
  if (el) el.scrollTop = el.scrollHeight;
};
window.addEventListener("DOMContentLoaded", scrollToBottom);
</script>
""", unsafe_allow_html=True)

# ─── 同期API呼び出し＋リトライ ─────────────────────────────
@lru_cache(maxsize=128)
def fetch_response(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents":[{"parts":[{"text":prompt}]}]}
    result = None

    for retry in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            cands = data.get("candidates", [])
            if not cands:
                result = "（回答なし）"
            else:
                content = cands[0]["content"]
                if isinstance(content, dict) and "parts" in content:
                    result = "".join(p.get("text","") for p in content["parts"]).strip()
                else:
                    result = str(content).strip()
            break
        except Exception:
            time.sleep(2 ** retry)
            continue

    if result is None:
        return "通信エラーが発生しました。オフラインモードです。"
    return result

# ─── UI描画ヘルパー ─────────────────────────────────────
def render_loading_skeleton():
    st.markdown('<div class="chat-bubble loading">　</div>', unsafe_allow_html=True)

def render_chat_bubble(name: str, msg: str):
    cls = {
        "ゆかり": "bubble-yukari",
        "しんや": "bubble-shinya",
        "みのる": "bubble-minoru"
    }[name]
    safe = msg.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    st.markdown(f'<div class="chat-bubble {cls}">{safe}</div>', unsafe_allow_html=True)

# ─── セッションステート初期化 ─────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ─── 入力フォーム＋送信処理 ─────────────────────────────────
st.markdown('<div id="input-area">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True):
    user_q = st.text_input(
        label="質問",
        placeholder="質問を入力…",
        key="input_q",
        label_visibility="collapsed"
    )
    send_btn = st.form_submit_button("送信")
st.markdown('</div>', unsafe_allow_html=True)

if send_btn and user_q.strip():
    st.session_state.history.append(("user", user_q))
    render_loading_skeleton()
    resp = fetch_response(user_q)
    st.session_state.history.append(("ai", resp))
    st.rerun()

# ─── チャット表示＋スクロール呼び出し ───────────────────────
st.markdown('<div id="chat-container">', unsafe_allow_html=True)
for role, text in st.session_state.history:
    render_chat_bubble("しんや" if role=="user" else "ゆかり", text)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<script>scrollToBottom();</script>", unsafe_allow_html=True)
