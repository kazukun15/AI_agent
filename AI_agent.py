import streamlit as st
import requests
import re
import time
from functools import lru_cache

st.set_page_config(page_title="ぼくのともだち", layout="wide", initial_sidebar_state="collapsed")

API_KEY    = st.secrets["general"]["api_key"]
MODEL_NAME = "gemini-2.0-flash-lite"

st.markdown("""
<style>
  /* チャット領域：下部余白を160pxに拡大 */
  #chat-container {
    display: flex;
    flex-direction: column;
    padding: 10px;
    padding-bottom: 160px;  
    height: calc(100vh - 180px);
    overflow-y: auto;
  }
  /* バブル間隔とパディング */
  .chat-bubble {
    max-width: 70%;
    margin: 4px 0;
    padding: 8px 12px;
    border-radius: 18px;
    word-wrap: break-word;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }
  .bubble-yukari { background-color: #DCF8C6; align-self: flex-start; }
  .bubble-shinya { background-color: #E0F7FA; align-self: flex-end; }
  .bubble-minoru { background-color: #FCE4EC; align-self: flex-start; }

  /* ローディングスケルトン */
  .chat-bubble.loading {
    margin: 4px 0;
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
  #input-area label { display: none !important; }
  #input-area input {
    width: 80%; height: 40px;
    padding: 6px 10px;
    font-size: 16px;
    border-radius: 12px;
    border: 1px solid #ccc;
  }
  #input-area button {
    width: 15%;
    margin-left: 5%;
    height: 40px;
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

@lru_cache(maxsize=128)
def fetch_response(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
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
        except:
            time.sleep(2 ** retry)
    return "通信エラーが発生しました。オフラインモードです。"

def render_loading_skeleton():
    st.markdown('<div class="chat-bubble loading">　</div>', unsafe_allow_html=True)

def render_chat_bubble(name: str, msg: str):
    cls = {"ゆかり":"bubble-yukari","しんや":"bubble-shinya","みのる":"bubble-minoru"}[name]
    safe = msg.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    st.markdown(f'<div class="chat-bubble {cls}">{safe}</div>', unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

# 入力フォーム
st.markdown('<div id="input-area">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True):
    user_q = st.text_input(label="質問", placeholder="質問を入力…", key="input_q", label_visibility="collapsed")
    send_btn = st.form_submit_button("送信")
st.markdown('</div>', unsafe_allow_html=True)

# メッセージ送信
if send_btn and user_q.strip():
    st.session_state.history.append(("user", user_q))
    render_loading_skeleton()
    resp = fetch_response(user_q)
    st.session_state.history.append(("ai", resp))
    st.rerun()

# チャット表示＋直後に自動スクロール呼び出し
st.markdown('<div id="chat-container">', unsafe_allow_html=True)
for role, text in st.session_state.history:
    if role == "user":
        render_chat_bubble("しんや", text)
    else:
        render_chat_bubble("ゆかり", text)
st.markdown('</div>', unsafe_allow_html=True)
# 新規メッセージ後にもスクロールをトリガー
st.markdown("<script>scrollToBottom();</script>", unsafe_allow_html=True)
