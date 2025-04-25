import streamlit as st
import requests
import re

# ========================
#    定数／設定
# ========================
API_KEY = st.secrets["general"]["api_key"]
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"

# 各キャラクタのスタイル設定
PERSONAS = {
    "ゆかり": {"bg": "#DCF8C6", "align": "right"},
    "しんや": {"bg": "#FFFFFF", "align": "left"},
    "みのる": {"bg": "#FCE4EC", "align": "left"}
}

# ========================
#    ヘルパー関数
# ========================

def analyze_question(question: str) -> int:
    """質問文から感情スコアを算出（肯定的な感情が多ければ+、論理的なキーワードが多ければ-）。"""
    score = 0
    for w in ["困った", "悩み", "苦しい", "辛い"]:
        if w in question:
            score += 1
    for w in ["理由", "原因", "仕組み", "方法"]:
        if w in question:
            score -= 1
    return score


def adjust_parameters(question: str) -> dict:
    """質問のスコアに応じて、各キャラの回答スタイルを決定。"""
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


def clean_response(text: str) -> str:
    """JSONアーティファクトを除去してテキストを整形。"""
    if not text:
        return ""
    text = re.sub(r"\{'text':\s*'(.*?)'\}", r"\1", text)
    return text.strip()


def call_gemini_api(prompt: str) -> str:
    """Gemini API を呼び出し、テキストを返す。"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code != 200:
        return f"エラー: ステータス {res.status_code} - {res.text}"
    data = res.json()
    parts = []
    try:
        candidates = data.get("candidates", [])
        for c in candidates:
            content = c.get("content", {})
            for p in content.get("parts", []):
                parts.append(p.get("text", ""))
    except Exception:
        return "エラー: レスポンス解析失敗"
    return clean_response("".join(parts))


def generate_discussion(question: str, params: dict) -> str:
    prompt = f"【ユーザーの質問】\n{question}\n\n"
    for name, info in params.items():
        prompt += f"{name}は【{info['style']}な視点】で、{info['detail']}。\n"
    prompt += (
        "\n上記情報を元に、3人が友達同士のように自然な会話をしてください。"
        "出力形式は以下の通りです。\n"
        "ゆかり: 発言内容\n"
        "しんや: 発言内容\n"
        "みのる: 発言内容\n"
        "余計なJSON形式は入れず、自然な日本語の会話のみを出力してください。"
    )
    return call_gemini_api(prompt)


def generate_summary(discussion: str) -> str:
    prompt = (
        "以下は3人の会話内容です。\n"
        f"{discussion}\n\n"
        "この会話を踏まえて、質問に対するまとめ回答を生成してください。"
        "自然な日本語文で出力し、余計なJSON形式は不要です。"
    )
    return call_gemini_api(prompt)


def display_line_style(discussion: str):
    """LINE風のバブルチャットをHTMLでレンダリング。# chat-container で自動スクロール設定"""
    st.markdown(
        """
        <style>
        #chat-container { overflow-y: auto; height: calc(100vh - 120px); padding-bottom: 100px; }
        .bubble { position: relative; margin: 6px 0; padding: 8px 12px; border-radius: 16px; max-width: 70%; word-wrap: break-word; }
        .bubble::after { content: ''; position: absolute; width: 0; height: 0; border: 8px solid transparent; }
        .bubble-left::after { top: 0; left: -16px; border-right-color: inherit; border-left: 0; margin-top: 4px; }
        .bubble-right::after { top: 0; right: -16px; border-left-color: inherit; border-right: 0; margin-top: 4px; }
        #input-area { position: fixed; bottom: 0; left: 0; width: 100%; background: #fff; padding: 10px; box-shadow: 0 -2px 5px rgba(0,0,0,0.1); }
        </style>
        <script>
        function scrollChat() {
          const chat = document.getElementById('chat-container');
          if (chat) { chat.scrollTop = chat.scrollHeight; }
        }
        setTimeout(scrollChat, 100);
        </script>
        <div id="chat-container"></div>
        """, unsafe_allow_html=True
    )
    for line in discussion.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^(.*?):\s*(.*)$", line)
        if m:
            name, msg = m.group(1), m.group(2)
        else:
            name, msg = "", line
        persona = PERSONAS.get(name, {"bg": "#F0F0F0", "align": "left"})
        align = persona['align']
        css_class = "bubble-right" if align == 'right' else "bubble-left"
        html = f"""
        <div class="bubble {css_class}" style="background:{persona['bg']}; margin-{'left' if align=='left' else 'right'}: auto;">
            <strong>{name}</strong><br>{msg}
        </div>
        """
        st.markdown(
            f"<script>document.getElementById('chat-container').insertAdjacentHTML('beforeend', `{html}`)</script>",
            unsafe_allow_html=True
        )

# ========================
#    Streamlit アプリ本体
# ========================

st.set_page_config(page_title="ぼくのともだち", layout="wide")

st.title("💬 ぼくのともだち")

# セッションステート初期化
if "discussion" not in st.session_state:
    st.session_state.discussion = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""

# --- 質問入力と操作 ---
# input-area を固定表示
st.markdown("<div id='input-area'>", unsafe_allow_html=True)
with st.form("input_form"):
    question = st.text_area("", placeholder="質問を入力してください…", key="input_text", height=50)
    submitted = st.form_submit_button("送信")
st.markdown("</div>", unsafe_allow_html=True)

# 送信後に自動的に会話を更新し表示
if "input_text" in st.session_state and st.session_state.input_text:
    question = st.session_state.input_text
    params = adjust_parameters(question)
    discussion = generate_discussion(question, params)
    st.session_state.discussion = discussion
    display_line_style(st.session_state.discussion)
