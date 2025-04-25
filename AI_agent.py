import os
import streamlit as st
import requests
import re
import google.generativeai as genai

# — API キー設定 —
genai.configure(api_key=st.secrets["general"]["api_key"])

# — 定数定義 —
MODEL_NAME = "gemini-2.5-pro-exp-03-25"
PERSONAS   = ["ゆかり", "しんや", "みのる"]

# — CSS／JS 埋め込み（省略） —
st.markdown("""
<style>
  /* 省略: チャットバブル & 固定入力欄のスタイル */
</style>
<script>
  /* 省略: 自動スクロール */
</script>
""", unsafe_allow_html=True)

# — セッション初期化 —
if "discussion" not in st.session_state:
    st.session_state.discussion = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""

# — パラメータ調整関数（省略） —  
def adjust_params(q: str) -> dict:
    # ...（省略）...
    return {}

# — Gemini 呼び出し関数 —  
def call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel(model_name=MODEL_NAME)
    resp = model.generate_content(prompt)
    return resp.text.strip()

# — 会話・まとめ生成 —  
def gen_discussion(q: str) -> str:
    params = adjust_params(q)
    p = f"【ユーザーの質問】\n{q}\n\n"
    # ...パーソナ設定をプロンプトに追加...
    return call_gemini(p)

def gen_summary(disc: str) -> str:
    p = f"以下は3人の会話です：\n{disc}\n\nまとめを作成してください。"
    return call_gemini(p)

# — バブル描画（省略） —  
def render_bubbles(text: str):
    # ...（省略）...
    pass

# — アプリ本体 —  
st.title("ぼくのともだち")

# チャット表示エリア
st.markdown('<div id="chat-container">', unsafe_allow_html=True)
if st.session_state.discussion:
    render_bubbles(st.session_state.discussion)
if st.session_state.summary:
    st.markdown(f'**まとめ:** {st.session_state.summary}')
st.markdown('</div>', unsafe_allow_html=True)

# 入力エリア（固定）
st.markdown('<div id="input-area">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True, enter_to_submit=True):
    user_q = st.text_area(
        label="質問",
        placeholder="質問を入力…",
        key="input_q",
        height=150,
        label_visibility="collapsed"
    )
    send        = st.form_submit_button("送信")
    summary_btn = st.form_submit_button("まとめ表示")
st.markdown('</div>', unsafe_allow_html=True)

# 送信処理
if send and user_q.strip():
    st.session_state.discussion = gen_discussion(user_q)
    st.session_state.summary    = ""
    st.experimental_rerun()

if summary_btn and st.session_state.discussion:
    st.session_state.summary = gen_summary(st.session_state.discussion)
    st.experimental_rerun()
