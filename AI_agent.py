import streamlit as st
import requests
import re
import random

# ========================
#    定数／設定
# ========================
API_KEY = st.secrets["general"]["api_key"]
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"
NAMES = ["ゆかり", "しんや", "みのる"]

# ========================
#    CSS／JS 埋め込み
# ========================
st.markdown("""
<style>
#chat-container {
    padding-bottom: 80px;  /* 入力エリアと重ならない余白 */
}
#input-area {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #ffffff;
    padding: 10px 20px;
    box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
}
.chat-bubble {
    max-width: 70%;
    margin: 5px;
    padding: 8px 12px;
    border-radius: 16px;
    position: relative;
    word-wrap: break-word;
}
.bubble-yukari {
    background-color: #DCF8C6;
    align-self: flex-start;
}
.bubble-shinya {
    background-color: #E0F7FA;
    align-self: flex-end;
}
.bubble-minoru {
    background-color: #FCE4EC;
    align-self: flex-start;
}
</style>
<script>
const scrollToBottom = () => {
    const el = document.getElementById("chat-container");
    if (el) el.scrollTop = el.scrollHeight;
};
window.onload = scrollToBottom;
</script>
""", unsafe_allow_html=True)

# ========================
#    関数定義
# ========================
def analyze_question(question: str) -> int:
    score = 0
    for word in ["困った", "悩み", "苦しい", "辛い"]:
        if re.search(word, question):
            score += 1
    for word in ["理由", "原因", "仕組み", "方法"]:
        if re.search(word, question):
            score -= 1
    return score

def adjust_parameters(question: str) -> dict:
    score = analyze_question(question)
    if score > 0:
        return {
            "ゆかり": {"style": "情熱的", "detail": "感情に寄り添う回答"},
            "しんや": {"style": "共感的", "detail": "心情を重視した解説"},
            "みのる": {"style": "柔軟", "detail": "状況に合わせた多面的な視点"}
        }
    else:
        return {
            "ゆかり": {"style": "論理的", "detail": "具体的な解説を重視"},
            "しんや": {"style": "分析的", "detail": "データや事実を踏まえた説明"},
            "みのる": {"style": "客観的", "detail": "中立的な視点からの考察"}
        }

def remove_json_artifacts(text: str) -> str:
    if not isinstance(text, str):
        text = str(text) if text else ""
    pattern = r"'parts': \[\{'text':.*?\}\], 'role': 'model'"
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL)
    return cleaned.strip()

def call_gemini_api(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
    except Exception as e:
        return f"エラー: リクエスト送信時に例外が発生 -> {e}"
    if response.status_code != 200:
        return f"エラー: ステータスコード {response.status_code} -> {response.text}"
    try:
        rjson = response.json()
        candidates = rjson.get("candidates", [])
        if not candidates:
            return "回答が見つかりませんでした。(candidatesが空)"
        content = candidates[0].get("content", "")
        if isinstance(content, dict):
            parts = content.get("parts", [])
            text = " ".join([p.get("text", "") for p in parts]).strip()
        else:
            text = str(content).strip()
        return remove_json_artifacts(text) or "回答を取得できませんでした。"
    except Exception as e:
        return f"エラー: レスポンス解析に失敗 -> {e}"

def generate_discussion(question: str, persona: dict) -> str:
    prompt = f"【ユーザーの質問】\n{question}\n\n"
    for name, p in persona.items():
        prompt += f"{name}はで、{p['detail']}。\n"
    prompt += (
        "\n上記を踏まえて3人が友達同士のように自然な会話をしてください。\n"
        "出力は「ゆかり: …」「しんや: …」「みのる: …」の形式で。"
    )
    return call_gemini_api(prompt)

def generate_summary(discussion: str) -> str:
    prompt = f"以下は3人の会話です。\n{discussion}\n\nこの内容を踏まえ、質問に対するまとめ回答を自然な日本語で作成してください。"
    return call_gemini_api(prompt)

def display_bubbles(text: str):
    for line in text.split("\n"):
        m = re.match(r"^(ゆかり|しんや|みのる):\s*(.*)$", line)
        if m:
            name, msg = m.groups()
            cls = {"ゆかり":"bubble-yukari","しんや":"bubble-shinya","みのる":"bubble-minoru"}[name]
            st.markdown(f'<div class="chat-bubble {cls}">{msg}</div>', unsafe_allow_html=True)

# ========================
#    アプリ本体
# ========================
st.title("ぼくのともだち")

if "discussion" not in st.session_state:
    st.session_state.discussion = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""

with st.container():
    st.markdown('<div id="chat-container" style="display:flex;flex-direction:column;">', unsafe_allow_html=True)
    if st.session_state.discussion:
        display_bubbles(st.session_state.discussion)
    if st.session_state.summary:
        st.markdown(f'**まとめ:** {st.session_state.summary}')
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div id="input-area">', unsafe_allow_html=True)
# ラベルに空文字を渡さず label_visibility で隠す
question = st.text_area(
    label="質問",
    placeholder="質問を入力してください…",
    key="input_text",
    height=50,
    label_visibility="collapsed"
)
col1, col2 = st.columns([1,1])
with col1:
    if st.button("会話を開始"):
        if question.strip():
            params = adjust_parameters(question)
            st.session_state.discussion = generate_discussion(question, params)
            st.experimental_rerun()
with col2:
    if st.button("まとめを表示"):
        if st.session_state.discussion:
            st.session_state.summary = generate_summary(st.session_state.discussion)
            st.experimental_rerun()
st.markdown('</div>', unsafe_allow_html=True)
