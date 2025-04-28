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
  /* ==== チャット領域 ==== */
  #chat-container {
    display: flex;
    flex-direction: column;
    padding: 10px;
    padding-bottom: calc(80px + env(safe-area-inset-bottom));  
    height: calc(100vh - 100px);
    overflow-y: auto;
  }

  /* ==== チャットバブル ==== */
  .chat-bubble {
    max-width: 70%;
    margin: 6px 0;
    padding: 12px 16px;
    border-radius: 20px;
    word-wrap: break-word;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    font-size: 18px;
    line-height: 1.5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }
  .bubble-yukari { background-color: #DCF8C6; align-self: flex-start; }
  .bubble-shinya { background-color: #E0F7FA; align-self: flex-end; }
  .bubble-minoru { background-color: #FCE4EC; align-self: flex-start; }

  /* ==== ローディングスケルトン ==== */
  .chat-bubble.loading {
    background-color: #e0e0e0;
    color: transparent;
    position: relative;
  }
  .chat-bubble.loading::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.6) 50%, rgba(255,255,255,0) 100%);
    animation: shimmer 1.2s infinite;
    border-radius: 20px;
  }
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  /* ==== 入力エリア固定 ==== */
  #input-area {
    position: fixed;
    bottom: env(safe-area-inset-bottom);
    left: 0; width: 100%;
    background-color: #ffffff;
    box-shadow: 0 -2px 6px rgba(0,0,0,0.1);
    padding: 8px 12px;
  }
  #input-area label { display: none !important; }
  #input-area input {
    width: 75%; height: 48px;
    padding: 0 12px;
    font-size: 18px;
    border-radius: 24px;
    border: 1px solid #ccc;
    vertical-align: middle;
  }
  #input-area button {
    width: 20%; height: 48px;
    margin-left: 5%;
    font-size: 18px;
    border: none;
    border-radius: 24px;
    background-color: #4CAF50;
    color: #fff;
    cursor: pointer;
  }

  /* ==== モバイル専用調整 ==== */
  @media (max-width: 600px) {
    .chat-bubble { max-width: 90%; font-size: 20px; padding: 14px 18px; }
    #input-area input { width: 70%; font-size: 20px; height: 56px; }
    #input-area button { width: 25%; font-size: 20px; height: 56px; }
    #chat-container { padding-bottom: calc(100px + env(safe-area-inset-bottom)); height: calc(100vh - 120px); }
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
    for retry in range(3):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
           
