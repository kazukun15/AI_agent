import os
import streamlit as st
import requests
import re
from openai import OpenAI

# ========================
#    APIクライアント設定
# ========================
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# ========================
#    定数／設定
# ========================
API_KEY    = st.secrets["general"]["api_key"]
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"
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
    padding-bottom: 100px;  /* 下部入力エリアと重ならない余白 */
    overflow-y: auto;
    height: calc(100vh - 120px);
  }
  .chat-bubble {
    max-width: 70%;
    margin: 5px;
    padding: 10px 14px;
    border-radius: 16px;
    word-wrap: break-word;
    box-shadow: 0 1px 1px rgba(0,0,0,0.1);
  }
  .bubble-yukari { background-color: #DCF8C6; align-self: flex-start;  }
  .bubble-shinya { background-color: #E0F7FA; align-self: flex-end;    }
  .bubble-minoru { background-color: #FCE4EC; align-self: flex-start;  }

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
  window.onload = () => {
    const el = document.getElementById("chat-container");
    if (el) el.scrollTop = el.scrollHeight;
  };
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
#    ChatGPT レスポンス取得
# ========================
def response_chatgpt(prompt: str) -> str:
    """OpenAI のストリーミング ChatCompletion で逐次応答を取得"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    text = ""
    for chunk in response:
        delta = chunk.choices[0].delta.get("content", "")
        text += delta
    return text.strip()

# ========================
#    会話生成・表示ヘルパー
# ========================
def gen_discussion(q: str) -> str:
    params = adjust_params(q)
    prompt = f"【ユーザーの質問】\n{q}\n\n"
    for name, cfg in params.items():
        prompt += f"{name}は【{cfg['style']}】で、{cfg['detail']}。\n"
    prompt += "\n以上の設定で3人が友達同士のように自然に会話してください。"
    return response_chatgpt(prompt)

def gen_summary(disc: str) -> str:
    prompt = f"以下は3人の会話です：\n{disc}\n\nこの内容を踏まえたまとめを自然な日本語で作成してください。"
    return response_chatgpt(prompt)

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
    send        = st.form_submit_button("送信")
    summary_btn = st.form_submit_button("まとめ表示")
st.markdown('</div>', unsafe_allow_html=True)

# — 送信処理 —
if send and user_q.strip():
    st.session_state.discussion = gen_discussion(user_q)
    st.session_state.summary    = ""
    st.experimental_rerun()

if summary_btn and st.session_state.discussion:
    st.session_state.summary = gen_summary(st.session_state.discussion)
    st.experimental_rerun()
