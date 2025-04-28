import streamlit as st
import requests
import re
import time
from functools import lru_cache

# ページ設定
st.set_page_config(
    page_title="ぼくのともだち",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_KEY    = st.secrets["general"]["api_key"]
MODEL_NAME = "gemini-2.0-flash-lite"

# CSS／JS
st.markdown("""
<style>
  /* メッセージ領域 */
  #chat-container {
    display: flex;
    flex-direction: column;
    padding: 10px;
    padding-bottom: 80px;   /* 入力欄と重ならない余白 */
    height: calc(100vh - 100px);
    overflow-y: auto;
  }
  .chat-bubble {
    max-width: 75%;
    margin: 6px 0;
    padding: 10px 14px;
    border-radius: 20px;
    word-wrap: break-word;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.4;
  }
  .bubble-yukari { background-color: #DCF8C6; align-self: flex-start; }
  .bubble-shinya { background-color: #E0F7FA; align-self: flex-end; }
  .bubble-minoru { background-color: #FCE4EC; align-self: flex-start; }

  /* 入力欄固定 */
  #input-area {
    position: fixed;
    bottom: 0; left: 0;
    width: 100%;
    background-color: #ffffff;
    box-shadow: 0 -2px 6px rgba(0,0,0,0.1);
    padding: 8px 16px;
  }
  #input-area label { display: none !important; }
  #input-area input {
    width: 75%;
    height: 40px;
    padding: 0 12px;
    font-size: 16px;
    border-radius: 20px;
    border: 1px solid #ccc;
    vertical-align: middle;
  }
  #input-area button {
    width: 20%;
    height: 40px;
    margin-left: 5%;
    font-size: 16px;
    border: none;
    border-radius: 20px;
    background-color: #4CAF50;
    color: #fff;
    cursor: pointer;
  }
</style>
<script>
  function scrollToBottom() {
    const el = document.getElementById("chat-container");
    if (el) el.scrollTop = el.scrollHeight;
  }
  window.addEventListener("DOMContentLoaded", scrollToBottom);
</script>
""", unsafe_allow_html=True)

# 同期API呼び出し＋リトライ
@lru_cache(maxsize=128)
def fetch_response(prompt: str) -> str:
    url     = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents":[{"parts":[{"text":prompt}]}]}
    result  = None
    for retry in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            data  = r.json()
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
        except:
            time.sleep(2 ** retry)
    return result or "通信エラーが発生しました。"

# UI描画ヘルパー
def render_chat_bubble(name: str, msg: str):
    cls = {"ゆかり":"bubble-yukari","しんや":"bubble-shinya","みのる":"bubble-minoru"}[name]
    safe = msg.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    st.markdown(f'<div class="chat-bubble {cls}">{safe}</div>', unsafe_allow_html=True)

# セッション初期化
if "history" not in st.session_state:
    st.session_state.history = []

# メッセージ表示エリア
st.markdown('<div id="chat-container">', unsafe_allow_html=True)
for role, text in st.session_state.history:
    render_chat_bubble("しんや" if role=="user" else "ゆかり", text)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<script>scrollToBottom();</script>", unsafe_allow_html=True)

# 入力エリア（下部固定）
st.markdown('<div id="input-area">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True):
    user_q  = st.text_input(label="質問", placeholder="質問を入力…", key="input_q", label_visibility="collapsed")
    send_btn = st.form_submit_button("送信")
st.markdown('</div>', unsafe_allow_html=True)

# 送信処理
if send_btn and user_q.strip():
    st.session_state.history.append(("user", user_q))
    resp = fetch_response(user_q)
    st.session_state.history.append(("ai", resp))
    st.rerun()
