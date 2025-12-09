import os
import io
import re
from typing import Dict, Any, Optional

import streamlit as st
from PIL import Image

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
import docx

# ======================================================
# ページ設定
# ======================================================
st.set_page_config(
    page_title="MAGI風マルチAI分析システム（テキスト簡易版＋SWOTオプション）",
    page_icon="🧬",
    layout="wide",
)

# ------------------------------------------------------
# MAGI風 カスタムCSS（スマホ対応＋SWOT可視化）
# ------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top, #222b40 0, #050710 45%, #02030a 100%);
        color: #e0e4ff;
        font-family: "Roboto Mono", "SF Mono", "Consolas", "Noto Sans JP", monospace;
    }
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: #3e4a6e;
        border-radius: 3px;
    }
    .magi-header {
        border: 1px solid #4d5cff;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 16px;
        background: linear-gradient(135deg, rgba(35,50,95,0.95), rgba(10,15,35,0.95));
        box-shadow: 0 0 20px rgba(80,120,255,0.35);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .magi-header-left { display: flex; flex-direction: column; }
    .magi-header-title {
        font-size: 20px;
        letter-spacing: 0.18em;
        color: #e8ecff;
        text-transform: uppercase;
    }
    .magi-header-sub {
        font-size: 11px;
        color: #9fa8ff;
        margin-top: 4px;
    }
    .magi-status {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        color: #b6ffcc;
    }
    .magi-status-light {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: radial-gradient(circle, #9fffcb 0, #00ff66 40%, #008833 100%);
        box-shadow: 0 0 8px #00ff99;
        animation: magi-pulse 1.5s infinite ease-in-out;
    }
    @keyframes magi-pulse {
        0% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(1.3); opacity: 1; }
        100% { transform: scale(1); opacity: 0.8; }
    }
    .magi-info-card {
        border-radius: 10px;
        border: 1px solid rgba(130,140,200,0.6);
        background: linear-gradient(135deg, rgba(16,22,48,0.95), rgba(6,10,26,0.95));
        padding: 10px 14px;
        font-size: 13px;
        color: #cfd6ff;
        margin-bottom: 8px;
    }
    .magi-info-card b { color: #ffffff; }

    .magi-panel {
        border-radius: 10px;
        padding: 10px 14px;
        margin-top: 6px;
        margin-bottom: 6px;
        font-size: 13px;
        line-height: 1.6;
        border: 1px solid rgba(140,160,255,0.4);
        background: radial-gradient(circle at top, rgba(18,26,60,0.98), rgba(5,8,22,0.98));
        box-shadow: 0 0 15px rgba(90,110,200,0.35);
        overflow-wrap: break-word;
    }
    .magi-panel-logic {
        border-color: #497bff;
        box-shadow: 0 0 16px rgba(74,123,255,0.4);
    }
    .magi-panel-human {
        border-color: #ffb349;
        box-shadow: 0 0 16px rgba(255,179,73,0.4);
    }
    .magi-panel-reality {
        border-color: #3fd684;
        box-shadow: 0 0 16px rgba(63,214,132,0.4);
    }
    .magi-panel-media {
        border-color: #c36bff;
        box-shadow: 0 0 16px rgba(195,107,255,0.4);
    }
    .magi-panel-summary {
        margin-top: 4px;
        font-size: 13px;
        line-height: 1.6;
        color: #e3e7ff;
    }

    .magi-vote {
        display: inline-flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: center;
        padding: 4px 8px;
        border-radius: 6px;
        margin-bottom: 4px;
        font-size: 11px;
    }
    .magi-vote-label-en {
        font-size: 10px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        opacity: 0.9;
    }
    .magi-vote-label-jp {
        font-size: 12px;
        font-weight: 600;
        margin-top: 2px;
    }
    .magi-vote-approve {
        background: linear-gradient(135deg, #0b5428, #21b35a);
        border: 1px solid #39ff9c;
        box-shadow: 0 0 12px rgba(50,255,170,0.7);
        color: #e8fff4;
    }
    .magi-vote-reject {
        background: linear-gradient(135deg, #5b1111, #d63232);
        border: 1px solid #ff7b7b;
        box-shadow: 0 0 12px rgba(255,100,100,0.7);
        color: #ffecec;
    }
    .magi-vote-hold {
        background: linear-gradient(135deg, #6a5212, #d7a52b);
        border: 1px solid #ffd966;
        box-shadow: 0 0 12px rgba(255,220,120,0.7);
        color: #fff8e1;
    }

    .magi-aggregator {
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 10px;
        border: 1px solid #6f8dff;
        background: radial-gradient(circle at top, rgba(31,42,90,0.98), rgba(6,8,20,0.98));
        box-shadow: 0 0 22px rgba(110,140,255,0.5);
        font-size: 14px;
        color: #ecf0ff;
        line-height: 1.7;
        overflow-wrap: break-word;
    }

    .magi-section-title {
        font-size: 15px;
        font-weight: 600;
        color: #e3e7ff;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 16px;
        margin-bottom: 6px;
    }
    .magi-divider {
        height: 1px;
        border: none;
        background: linear-gradient(to right, #4b5cff, transparent);
        margin-bottom: 10px;
    }

    /* SWOT 可視化用 */
    .magi-panel-swot {
        border-radius: 10px;
        padding: 10px 14px;
        margin-top: 6px;
        margin-bottom: 6px;
        font-size: 12px;
        line-height: 1.6;
        border: 1px solid rgba(255,127,209,0.7);
        background: radial-gradient(circle at top, rgba(40,20,50,0.96), rgba(10,4,16,0.96));
        box-shadow: 0 0 18px rgba(255,127,209,0.5);
        overflow-wrap: break-word;
    }
    .swot-chip {
        display: inline-block;
        padding: 3px 8px;
        margin: 2px;
        border-radius: 999px;
        font-size: 11px;
        line-height: 1.4;
        white-space: normal;
        word-break: break-word;
    }
    .swot-chip-s {
        background: rgba(76, 175, 80, 0.18);
        border: 1px solid rgba(129, 199, 132, 0.9);
        color: #dcedc8;
    }
    .swot-chip-w {
        background: rgba(244, 67, 54, 0.18);
        border: 1px solid rgba(229, 115, 115, 0.9);
        color: #ffcdd2;
    }
    .swot-chip-o {
        background: rgba(33, 150, 243, 0.18);
        border: 1px solid rgba(144, 202, 249, 0.9);
        color: #bbdefb;
    }
    .swot-chip-t {
        background: rgba(255, 193, 7, 0.18);
        border: 1px solid rgba(255, 224, 130, 0.9);
        color: #ffecb3;
    }
    .swot-count-label {
        font-size: 11px;
        opacity: 0.8;
        margin-bottom: 4px;
    }

    @media (max-width: 768px) {
        .magi-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
        }
        .magi-header-title {
            font-size: 16px;
        }
        .magi-panel {
            font-size: 12px;
            padding: 8px 10px;
        }
        .magi-aggregator {
            font-size: 13px;
            padding: 12px 14px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# MAGI ヘッダー
st.markdown(
    """
    <div class="magi-header">
        <div class="magi-header-left">
            <div class="magi-header-title">MAGI MULTI-AGENT INTELLIGENCE</div>
            <div class="magi-header-sub">
                GEMINI MULTI-MODEL · TEXT-ONLY LIGHTWEIGHT ANALYSIS
            </div>
        </div>
        <div class="magi-status">
            <div class="magi-status-light"></div>
            <span>SYSTEM STATUS: ONLINE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="magi-info-card">
    <b>概要：</b> テキスト・画像・音声などを入力すると、<b>Magi-Logic / Magi-Human / Magi-Reality / Magi-Media</b> が
    それぞれ短いコメントと判定を出し、最後に統合MAGIが結論をまとめます。<br>
    出力はプレーンテキスト形式のみとし、JSON解析を行わないことで安定性を優先した簡易版です。<br>
    さらにオプションで SWOT 分析（強み・弱み・機会・脅威）も実行できます。
    </div>
    """,
    unsafe_allow_html=True,
)

# ======================================================
# Gemini API 初期化
# ======================================================
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if not api_key:
    st.error(
        "Gemini の API キーが設定されていません。\n\n"
        "【Streamlit Cloud】Settings → Secrets で：\n"
        'GEMINI_API_KEY = "あなたのGemini APIキー"\n\n'
        "【ローカル】.streamlit/secrets.toml または環境変数 GEMINI_API_KEY に設定してください。"
    )
    st.stop()

genai.configure(api_key=api_key)

# ======================================================
# モデル選択（デフォルトは gemini-2.0-flash）
# ======================================================
MODEL_CHOICES = {
    "Gemini 2.0 Flash（デフォルト）": "gemini-2.0-flash",
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 2.5 Pro": "gemini-2.5-pro",
    "Gemini 2.5 Flash Lite": "gemini-2.5-flash-lite",
}

if "gemini_model_name" not in st.session_state:
    st.session_state["gemini_model_name"] = "gemini-2.0-flash"

st.sidebar.markdown("### モデル選択")
labels = list(MODEL_CHOICES.keys())
current_model = st.session_state.get("gemini_model_name", "gemini-2.0-flash")
current_label = next(
    (lbl for lbl, mid in MODEL_CHOICES.items() if mid == current_model),
    "Gemini 2.0 Flash（デフォルト）",
)
default_index = labels.index(current_label) if current_label in labels else 0

selected_label = st.sidebar.selectbox(
    "使用するGeminiモデル",
    labels,
    index=default_index,
    help=(
        "デフォルトは gemini-2.0-flash です。\n"
        "他のモデルも、まったく同じ聞き方（同じプロンプト構成）で呼び出します。"
    ),
)
st.session_state["gemini_model_name"] = MODEL_CHOICES[selected_label]


def get_gemini_model():
    """
    どのモデルに対しても「同じ聞き方」を維持するため、
    呼び出し方は変えず、内部でモデル名だけを切り替える。
    """
    model_name = st.session_state.get("gemini_model_name", "gemini-2.0-flash")
    return genai.GenerativeModel(model_name)


# ======================================================
# ユーティリティ
# ======================================================
def clean_text_for_display(text: str) -> str:
    if not text:
        return ""
    return text.replace("*", "・")


def trim_text(s: str, max_chars: int = 600) -> str:
    if not s:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n…（長文のためここで省略）"


def classify_resource_exhausted(e: ResourceExhausted) -> str:
    """
    ResourceExhausted のメッセージから、
    - レートリミット（短時間の叩きすぎ）
    - 日次／総量クォータ
    - free tier が 0
    - その他
    を日本語で推定。
    """
    msg = str(e)
    low = msg.lower()

    if "limit: 0" in msg:
        return (
            "カテゴリ推定：free tier クォータが 0\n"
            "・このプロジェクトの free_tier が 0 に設定されているか、既に使い切っています。\n"
            "・AI Studio / Cloud Console の Quotas 画面で、対象モデルの free_tier が 0 かどうか確認してください。\n"
            "・継続利用する場合は、課金の有効化または別プロジェクト／別APIキーの利用を検討してください。"
        )

    is_per_minute = ("PerMinute" in msg) or ("per minute" in low)
    is_per_day = ("PerDay" in msg) or ("per day" in low)

    if "rate limit" in low or "too many requests" in low or (is_per_minute and not is_per_day):
        return (
            "カテゴリ推定：レートリミット（短時間の叩きすぎ）\n"
            "・短時間に大量のリクエストを送信している可能性があります。\n"
            "・ボタンの連打を避け、実行間隔をあけてください。\n"
            "・1回の実行での呼び出し回数や入力サイズを減らすことも有効です。"
        )

    if is_per_day:
        return (
            "カテゴリ推定：日次／総量クォータ上限\n"
            "・1日あたり、またはプロジェクト全体の利用上限（無料枠・課金枠）に達している可能性があります。\n"
            "・AI Studio / Cloud Console の Usage / Quota 画面で、対象モデルの PerDay / PerProject の値を確認してください。"
        )

    if "exhausted" in low or "resources exhausted" in low:
        return (
            "カテゴリ推定：リソース逼迫（モデル側の一時的混雑など）\n"
            "・アクセス集中などで一時的にリソースが不足している可能性があります。\n"
            "・しばらく待ってから再実行してみてください。"
        )

    return (
        "カテゴリ推定：その他の ResourceExhausted\n"
        "・詳細は下記の『生メッセージ』を参照してください。"
    )


# ======================================================
# 媒体のテキスト化（画像・音声）
# ======================================================
def describe_image_with_gemini(img: Image.Image) -> str:
    model = get_gemini_model()
    prompt = (
        "この画像に何が写っているか、日本語で簡潔に2〜3文で説明してください。\n"
        "心理的な印象も1文で添えてください。"
    )
    try:
        resp = model.generate_content([prompt, img])
        return clean_text_for_display((resp.text or "").strip())
    except ResourceExhausted as e:
        detail = classify_resource_exhausted(e)
        return (
            "【エラー】画像解析中に Gemini のリソース上限エラーが発生しました。\n"
            f"生メッセージ：{str(e)}\n\n{detail}"
        )
    except Exception as e:
        return f"【エラー】画像解析に失敗しました: {str(e)}"


def transcribe_audio_with_gemini(uploaded_file) -> str:
    model = get_gemini_model()
    audio_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type or "audio/wav"

    prompt = (
        "この音声の内容を日本語でできるだけ正確に文字起こししてください。\n"
        "出力は通常の日本語文のみで書いてください。"
    )
    try:
        resp = model.generate_content(
            [prompt, {"mime_type": mime_type, "data": audio_bytes}]
        )
        return clean_text_for_display((resp.text or "").strip())
    except ResourceExhausted as e:
        detail = classify_resource_exhausted(e)
        return (
            "【エラー】音声解析中に Gemini のリソース上限エラーが発生しました。\n"
            f"生メッセージ：{str(e)}\n\n{detail}"
        )
    except Exception as e:
        return f"【エラー】音声解析に失敗しました: {str(e)}"


# ======================================================
# MAGI テキスト生成（SWOT ON/OFF・リミット診断付き）
# ======================================================
def call_magi_plain(context: Dict[str, Any], enable_swot: bool) -> str | None:
    """
    1回の generate_content で、Magi-Logic/Human/Reality/Media と統合出力を返す。
    enable_swot=True のときだけ SWOT 分析指示を追加し、
    リソース上限や MAX_TOKENS などを詳細にエラーハンドリング。
    """
    model = get_gemini_model()

    trimmed_context = {
        "user_question": trim_text(context.get("user_question", "")),
        "text_input": trim_text(context.get("text_input", "")),
        "audio_transcript": trim_text(context.get("audio_transcript", "")),
        "image_description": trim_text(context.get("image_description", "")),
    }

    # --- SWOTあり版プロンプト ---
    sys_prompt_swot = """
あなたは NERV の MAGI システム全体を模した統合AIです。
Magi-Logic / Magi-Human / Magi-Reality / Magi-Media の4視点と、統合MAGIとしての結論、
さらに意思決定に役立つSWOT分析を、以下のフォーマットだけを使って日本語で出力してください。

[重要：出力フォーマット（この通りに出力すること）]

【Magi-Logic】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内

【Magi-Human】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内

【Magi-Reality】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内

【Magi-Media】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内

【MAGI-統合サマリー】
全体としての結論を150文字以内でまとめる

【MAGI-統合詳細】
統合的な視点から、2〜4段落・合計500文字以内で詳細なコメントと推奨アクションを書く

【SWOT分析】
Strengths: 強みを5〜7個、日本語で列挙し、読点「、」で区切って1行で書く（合計300文字以内）
Weaknesses: 弱みを5〜7個、日本語で列挙し、読点「、」で区切って1行で書く（合計300文字以内）
Opportunities: 機会を5〜7個、日本語で列挙し、読点「、」で区切って1行で書く（合計300文字以内）
Threats: 脅威を5〜7個、日本語で列挙し、読点「、」で区切って1行で書く（合計300文字以内）

[制約]
- 箇条書き（・や番号付きリスト）は使わない。
- 上記の見出し・ラベル以外の文言や飾りは追加しない。
- 「Strengths:」「Weaknesses:」「Opportunities:」「Threats:」は英語ラベルをそのまま使う。
- 暴力・自傷・違法行為などの過激な表現は避け、穏当で一般的な表現に言い換える。
- 出力は必ずこのフォーマットに沿ったプレーンテキストのみとする。
"""

    # --- SWOTなし（軽量版）プロンプト ---
    sys_prompt_basic = """
あなたは NERV の MAGI システム全体を模した統合AIです。
Magi-Logic / Magi-Human / Magi-Reality / Magi-Media の4視点と、統合MAGIとしての結論を、
以下のフォーマットだけを使って日本語で出力してください。

[重要：出力フォーマット（この通りに出力すること）]

【Magi-Logic】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内

【Magi-Human】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内

【Magi-Reality】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内

【Magi-Media】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内

【MAGI-統合サマリー】
全体としての結論を150文字以内でまとめる

【MAGI-統合詳細】
統合的な視点から、2〜3段落・合計400文字以内で詳細なコメントと推奨アクションを書く

[制約]
- 箇条書き（・や番号付きリスト）は使わない。
- 上記の見出し・ラベル以外の文言や飾りは追加しない。
- 出力は必ずこのフォーマットに沿ったプレーンテキストのみとする。
"""

    ctx_text = (
        "【ユーザーからの情報】\n"
        + f"質問: {trimmed_context['user_question']}\n"
        + (
            f"テキスト入力: {trimmed_context['text_input']}\n"
            if trimmed_context["text_input"]
            else ""
        )
        + (
            f"音声文字起こし: {trimmed_context['audio_transcript']}\n"
            if trimmed_context["audio_transcript"]
            else ""
        )
        + (
            f"画像説明: {trimmed_context['image_description']}\n"
            if trimmed_context["image_description"]
            else ""
        )
    )

    def _call_internal(use_swot: bool, attempt: int) -> str | None:
        sys_prompt = sys_prompt_swot if use_swot else sys_prompt_basic
        max_tokens = 640 if use_swot else 480

        try:
            resp = model.generate_content(
                [sys_prompt, ctx_text],
                generation_config={"max_output_tokens": max_tokens},
            )

            if not getattr(resp, "candidates", None):
                if attempt == 1 and use_swot:
                    # SWOTありで失敗した場合は、1回だけSWOTなし軽量モードで再試行
                    return _call_internal(False, 2)
                return None

            first = resp.candidates[0]
            content = getattr(first, "content", None)
            parts = getattr(content, "parts", None)

            if not content or not parts:
                # finish_reason から原因を推定
                reason = getattr(first, "finish_reason", None)
                reason_str = str(reason).upper() if reason is not None else ""

                if attempt == 1 and use_swot:
                    # まずはSWOTなしに落として再チャレンジ
                    return _call_internal(False, 2)

                if "SAFETY" in reason_str:
                    return (
                        "【エラー】Gemini の安全ポリシーにより回答がブロックされました。\n"
                        "・特定の個人攻撃、自傷行為、違法行為などに関する内容が含まれていないか確認してください。\n"
                        "・表現をもっと一般的で穏やかなものに言い換えて再実行してみてください。"
                    )
                if "MAX_TOKENS" in reason_str or "TOKENS" in reason_str:
                    return (
                        "【エラー】Gemini の出力トークン上限に達し、回答を最後まで生成できませんでした。\n"
                        "・質問や補足テキストをさらに短くしてください。\n"
                        "・必要なポイントだけに絞って問い直してみてください。"
                    )

                return (
                    "【エラー】Gemini が有効なテキストを返しませんでした。\n"
                    "・入力内容が長すぎるか、安全ポリシーに抵触した可能性があります。\n"
                    "・質問を短くし、刺激的な表現を避けて再実行してみてください。"
                )

            text = (getattr(resp, "text", "") or "").strip()
            if not text:
                if attempt == 1 and use_swot:
                    # 空テキスト → SWOTなしで再試行
                    return _call_internal(False, 2)
                return (
                    "【エラー】Gemini が統合MAGIのテキストを返しませんでした。\n"
                    "内容が長すぎるか、一部が安全フィルタにかかった可能性があります。"
                )

            return text

        except ResourceExhausted as e:
            if attempt == 1 and use_swot:
                # まずはSWOTなしで軽く投げ直し
                return _call_internal(False, 2)

            detail = classify_resource_exhausted(e)
            return (
                "【エラー】Gemini で ResourceExhausted が発生しました。\n\n"
                f"生メッセージ：{str(e)}\n\n"
                f"{detail}"
            )
        except GoogleAPIError as e:
            return f"【エラー】Gemini API で問題が発生しました: {str(e)}"
        except Exception as e:
            return f"【エラー】MAGI複合分析中に想定外のエラーが発生しました: {str(e)}"

    return _call_internal(enable_swot, 1)


# ======================================================
# テキスト → 擬似エージェント構造＋SWOTへのパース
# ======================================================
def parse_magi_text(text: str) -> tuple[Dict[str, Any], Dict[str, str], Dict[str, str]]:
    agents: Dict[str, Any] = {}
    aggregated: Dict[str, str] = {"summary": "", "details": ""}
    swot: Dict[str, str] = {
        "strengths": "",
        "weaknesses": "",
        "opportunities": "",
        "threats": "",
    }

    pattern = r"^【(Magi-Logic|Magi-Human|Magi-Reality|Magi-Media|MAGI-統合サマリー|MAGI-統合詳細|SWOT分析)】"
    parts = re.split(pattern, text, flags=re.MULTILINE)

    it = iter(parts[1:])  # 最初の要素は前置き

    for name, body in zip(it, it):
        body = body.strip()
        if name == "Magi-Logic":
            agents["logic"] = parse_agent_block("Magi-Logic（論理・構造担当）", body)
        elif name == "Magi-Human":
            agents["human"] = parse_agent_block("Magi-Human（感情・人間面担当）", body)
        elif name == "Magi-Reality":
            agents["reality"] = parse_agent_block("Magi-Reality（現実運用・リスク担当）", body)
        elif name == "Magi-Media":
            agents["media"] = parse_agent_block("Magi-Media（表現・印象担当）", body)
        elif name == "MAGI-統合サマリー":
            aggregated["summary"] = body.replace("\n", " ").strip()
        elif name == "MAGI-統合詳細":
            aggregated["details"] = body.strip()
        elif name == "SWOT分析":
            swot = parse_swot_block(body)

    return agents, aggregated, swot


def parse_agent_block(name_jp: str, body: str) -> Dict[str, Any]:
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    decision_jp = "保留"
    summary = ""

    for line in lines:
        if line.startswith("判定"):
            if "可決" in line:
                decision_jp = "可決"
            elif "否決" in line:
                decision_jp = "否決"
            elif "保留" in line:
                decision_jp = "保留"
        elif line.startswith("要約"):
            summary = line.replace("要約", "").replace(":", "").replace("：", "").strip()
        else:
            if summary:
                summary += " " + line

    decision_code = {
        "可決": "Go",
        "否決": "No-Go",
        "保留": "Hold",
    }.get(decision_jp, "Hold")

    return {
        "name_jp": name_jp,
        "summary": summary,
        "decision_jp": decision_jp,
        "decision_code": decision_code,
    }


def parse_swot_block(body: str) -> Dict[str, str]:
    swot = {
        "strengths": "",
        "weaknesses": "",
        "opportunities": "",
        "threats": "",
    }
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    for line in lines:
        if line.startswith("Strengths"):
            swot["strengths"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Weaknesses"):
            swot["weaknesses"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Opportunities"):
            swot["opportunities"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Threats"):
            swot["threats"] = line.split(":", 1)[-1].strip()
    return swot


def decision_to_css(decision_code: str) -> Dict[str, str]:
    code = (decision_code or "Hold").strip()
    if code == "Go":
        return {"css": "approve", "en": "APPROVE", "jp": "可決"}
    if code == "No-Go":
        return {"css": "reject", "en": "REJECT", "jp": "否決"}
    return {"css": "hold", "en": "HOLD", "jp": "保留"}


def swot_text_to_chips(text: str, chip_class: str) -> str:
    if not text:
        return ""
    items = [x.strip() for x in text.replace("。", "、").split("、") if x.strip()]
    html_items = "".join(
        f'<span class="swot-chip {chip_class}">{clean_text_for_display(item)}</span>'
        for item in items
    )
    count_label = f'<div class="swot-count-label">項目数: {len(items)}</div>'
    return count_label + html_items


# ======================================================
# Word レポート生成（SWOT ON のときだけ第4章を追加）
# ======================================================
def build_word_report(
    context: Dict[str, Any],
    agents: Dict[str, Any],
    aggregated: Dict[str, Any],
    magi_raw_text: str,
    image: Optional[Image.Image] = None,
    swot: Optional[Dict[str, str]] = None,
    enable_swot: bool = False,
) -> bytes:
    doc = docx.Document()
    title = "MAGI風マルチAI分析レポート（テキスト簡易版"
    if enable_swot:
        title += "＋SWOT"
    title += "）"
    doc.add_heading(title, level=1)

    # 第1章 入力情報
    doc.add_heading("第1章 入力情報", level=2)
    doc.add_paragraph(f"■ ユーザー質問：{context.get('user_question', '')}")
    if context.get("text_input"):
        doc.add_paragraph("■ テキスト入力：")
        doc.add_paragraph(context["text_input"])
    if context.get("audio_transcript"):
        doc.add_paragraph("■ 音声文字起こし：")
        doc.add_paragraph(context["audio_transcript"])
    if context.get("image_description"):
        doc.add_paragraph("■ 画像の説明：")
        doc.add_paragraph(context["image_description"])

    if image is not None:
        img_stream = io.BytesIO()
        image.save(img_stream, format="PNG")
        img_stream.seek(0)
        doc.add_picture(img_stream, width=docx.shared.Inches(3))

    # 第2章 各MAGIエージェントの要約
    doc.add_heading("第2章 各MAGIエージェントの要約と判定", level=2)
    if agents:
        for key in ["logic", "human", "reality", "media"]:
            if key not in agents:
                continue
            a = agents[key]
            name = a.get("name_jp", key)
            doc.add_heading(name, level=3)
            doc.add_paragraph(f"判定：{a.get('decision_jp', '')}")
            doc.add_paragraph(f"要約：{clean_text_for_display(a.get('summary', ''))}")
    else:
        doc.add_paragraph("今回の実行では、MAGIエージェントの詳細出力は取得できませんでした。")

    # 第3章 MAGI統合AIの結論
    doc.add_heading("第3章 MAGI統合AIの結論・アクションプラン", level=2)
    agg_summary = clean_text_for_display(aggregated.get("summary", ""))
    agg_details = clean_text_for_display(aggregated.get("details", ""))
    if agg_summary:
        doc.add_paragraph("【サマリー】")
        doc.add_paragraph(agg_summary)
    if agg_details:
        doc.add_paragraph("【詳細】")
        for line in agg_details.splitlines():
            doc.add_paragraph(line)

    # 第4章 SWOT分析（ON のときだけ）
    if enable_swot and swot:
        if any(swot.values()):
            doc.add_heading("第4章 SWOT分析", level=2)
            doc.add_paragraph(f"Strengths（強み）：{swot.get('strengths', '')}")
            doc.add_paragraph(f"Weaknesses（弱み）：{swot.get('weaknesses', '')}")
            doc.add_paragraph(f"Opportunities（機会）：{swot.get('opportunities', '')}")
            doc.add_paragraph(f"Threats（脅威）：{swot.get('threats', '')}")
        else:
            doc.add_heading("第4章 SWOT分析", level=2)
            doc.add_paragraph("今回の実行では、SWOT分析は生成されませんでした。")

    # 付録：生テキスト
    doc.add_heading("付録：MAGI生テキスト", level=2)
    for line in magi_raw_text.splitlines():
        doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ======================================================
# サイドバー：媒体入力
# ======================================================
st.sidebar.markdown("### 媒体入力（任意）")

input_mode = st.sidebar.radio(
    "画像・音声の入力方法",
    ["ファイル／写真ライブラリから選択", "カメラで撮影", "使用しない"],
    index=2,
)

uploaded_file: Optional[Any] = None
image_for_report: Optional[Image.Image] = None

if input_mode == "ファイル／写真ライブラリから選択":
    file = st.sidebar.file_uploader(
        "画像 / 音声 / テキストファイル",
        accept_multiple_files=False,
    )
    if file:
        uploaded_file = file
elif input_mode == "カメラで撮影":
    cam = st.sidebar.camera_input("カメラで撮影（対応端末のみ）")
    if cam:
        uploaded_file = cam
else:
    st.sidebar.info("媒体入力を使用しない場合は、このままで構いません。")


# ======================================================
# メイン：質問と補足テキスト＋SWOTオプション
# ======================================================
st.markdown(
    '<div class="magi-section-title">INPUT · QUERY</div><hr class="magi-divider">',
    unsafe_allow_html=True,
)

user_question = st.text_area(
    "MAGI に投げたい「問い」",
    placeholder=(
        "例：この企画の方向性と改善点をMAGIに評価してほしい。\n"
        "例：この写真や音声から受ける印象と、次に取るべき行動を知りたい。"
    ),
    height=120,
)

text_input = st.text_area(
    "補足テキスト（任意）",
    height=100,
    placeholder="貼り付けたいメモや補足情報があれば入力してください。",
)

enable_swot = st.checkbox(
    "SWOT分析を有効にする（Strengths / Weaknesses / Opportunities / Threats を複数列挙）",
    value=False,
)

if not user_question and not uploaded_file and not text_input:
    st.info("質問か、媒体（画像・音声など）、または補足テキストのいずれかを入力してください。")
    st.stop()

# ======================================================
# 媒体の前処理（テキスト化）
# ======================================================
context: Dict[str, Any] = {
    "user_question": user_question,
    "text_input": text_input,
    "audio_transcript": "",
    "image_description": "",
}

if uploaded_file is not None:
    if uploaded_file.type and uploaded_file.type.startswith("image/"):
        try:
            image = Image.open(uploaded_file).convert("RGB")
        except Exception:
            st.error("この画像形式には対応していません。JPEG または PNG 形式の画像を使用してください。")
            image = None

        if image is not None:
            image_for_report = image
            st.image(image, caption="入力画像", use_column_width=True)

            with st.spinner("画像内容を解析中（Gemini）..."):
                img_desc = describe_image_with_gemini(image)
            context["image_description"] = img_desc

    elif uploaded_file.type and uploaded_file.type.startswith("audio/"):
        st.audio(uploaded_file)
        with st.spinner("音声を文字起こし中（Gemini）..."):
            transcript = transcribe_audio_with_gemini(uploaded_file)
        context["audio_transcript"] = transcript

    else:
        if (uploaded_file.type == "text/plain") or (
            isinstance(uploaded_file.name, str)
            and uploaded_file.name.lower().endswith(".txt")
        ):
            text_bytes = uploaded_file.read()
            context["text_input"] += "\n\n[ファイル内容]\n" + text_bytes.decode(
                "utf-8", errors="ignore"
            )
        else:
            st.warning("対応していないファイル形式です。画像・音声・テキストファイルを使用してください。")

# ======================================================
# MAGI 分析実行（コメントを問の近くに表示）
# ======================================================
run_analysis = st.button("🔎 MAGI による分析を実行", type="primary")

if run_analysis:
    if not user_question and not text_input and not any(
        [context["audio_transcript"], context["image_description"]]
    ):
        st.warning("最低でも質問・テキスト・媒体のいずれかが必要です。")
        st.stop()

    with st.spinner("MAGI 分析を実行中..."):
        magi_text = call_magi_plain(context, enable_swot=enable_swot)

    if magi_text is None:
        # 本当にテキストが返らなかった場合だけ、共通の案内を出す
        st.error(
            "【エラー】Gemini が有効なテキストを返しませんでした。\n"
            "・内容が極端に長い\n・安全フィルタにかかる表現が含まれている\nなどの可能性があります。\n\n"
            "一度、質問やテキストを短く・穏やかな表現にして再実行してみてください。"
        )
        st.stop()

    if isinstance(magi_text, str) and magi_text.startswith("【エラー】"):
        # ResourceExhausted / Safety / MAX_TOKENS など、詳細メッセージをそのまま表示
        st.error(magi_text)
        st.stop()

    agents, aggregated, swot = parse_magi_text(magi_text)

    st.success("MAGI の分析が完了しました。")

    # ▼ 質問のすぐ下にコメント欄を配置
    st.markdown(
        '<div class="magi-section-title">OUTPUT · MAGI COMMENTS</div><hr class="magi-divider">',
        unsafe_allow_html=True,
    )

    colL, colR = st.columns(2)

    # 左側：Logic / Reality
    with colL:
        if "logic" in agents:
            a = agents["logic"]
            dec = decision_to_css(a.get("decision_code", "Hold"))
            st.markdown("##### Magi-Logic")
            st.markdown(
                f'''
                <div class="magi-panel magi-panel-logic">
                  <div class="magi-vote magi-vote-{dec["css"]}">
                    <div class="magi-vote-label-en">{dec["en"]}</div>
                    <div class="magi-vote-label-jp">{dec["jp"]}</div>
                  </div>
                  <div class="magi-panel-summary">
                    {clean_text_for_display(a.get("summary", "")).replace("\\n", "<br>")}
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

        if "reality" in agents:
            a = agents["reality"]
            dec = decision_to_css(a.get("decision_code", "Hold"))
            st.markdown("##### Magi-Reality")
            st.markdown(
                f'''
                <div class="magi-panel magi-panel-reality">
                  <div class="magi-vote magi-vote-{dec["css"]}">
                    <div class="magi-vote-label-en">{dec["en"]}</div>
                    <div class="magi-vote-label-jp">{dec["jp"]}</div>
                  </div>
                  <div class="magi-panel-summary">
                    {clean_text_for_display(a.get("summary", "")).replace("\\n", "<br>")}
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

    # 右側：Human / Media
    with colR:
        if "human" in agents:
            a = agents["human"]
            dec = decision_to_css(a.get("decision_code", "Hold"))
            st.markdown("##### Magi-Human")
            st.markdown(
                f'''
                <div class="magi-panel magi-panel-human">
                  <div class="magi-vote magi-vote-{dec["css"]}">
                    <div class="magi-vote-label-en">{dec["en"]}</div>
                    <div class="magi-vote-label-jp">{dec["jp"]}</div>
                  </div>
                  <div class="magi-panel-summary">
                    {clean_text_for_display(a.get("summary", "")).replace("\\n", "<br>")}
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

        if "media" in agents:
            a = agents["media"]
            dec = decision_to_css(a.get("decision_code", "Hold"))
            st.markdown("##### Magi-Media")
            st.markdown(
                f'''
                <div class="magi-panel magi-panel-media">
                  <div class="magi-vote magi-vote-{dec["css"]}">
                    <div class="magi-vote-label-en">{dec["en"]}</div>
                    <div class="magi-vote-label-jp">{dec["jp"]}</div>
                  </div>
                  <div class="magi-panel-summary">
                    {clean_text_for_display(a.get("summary", "")).replace("\\n", "<br>")}
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

    # 統合コメント
    agg_html = clean_text_for_display(
        aggregated.get("details", "") or aggregated.get("summary", "")
    )
    st.markdown(
        '<div class="magi-section-title">OUTPUT · MAGI AGGREGATED DECISION</div><hr class="magi-divider">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="magi-aggregator">{agg_html.replace("\\n", "<br>")}</div>',
        unsafe_allow_html=True,
    )

    # ==================================================
    # SWOT 表示（SWOT ON のときだけ／生成されていれば）
    # ==================================================
    if enable_swot:
        st.markdown(
            '<div class="magi-section-title">SWOT · STRATEGIC VIEW</div><hr class="magi-divider">',
            unsafe_allow_html=True,
        )

        if any(swot.values()):
            col_s, col_w = st.columns(2)
            with col_s:
                s_html = swot_text_to_chips(swot.get("strengths", ""), "swot-chip-s")
                st.markdown(
                    f'''
                    <div class="magi-panel-swot">
                      <b>Strengths（強み）</b><br>
                      {s_html}
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
            with col_w:
                w_html = swot_text_to_chips(swot.get("weaknesses", ""), "swot-chip-w")
                st.markdown(
                    f'''
                    <div class="magi-panel-swot">
                      <b>Weaknesses（弱み）</b><br>
                      {w_html}
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

            col_o, col_t = st.columns(2)
            with col_o:
                o_html = swot_text_to_chips(swot.get("opportunities", ""), "swot-chip-o")
                st.markdown(
                    f'''
                    <div class="magi-panel-swot">
                      <b>Opportunities（機会）</b><br>
                      {o_html}
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
            with col_t:
                t_html = swot_text_to_chips(swot.get("threats", ""), "swot-chip-t")
                st.markdown(
                    f'''
                    <div class="magi-panel-swot">
                      <b>Threats（脅威）</b><br>
                      {t_html}
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
        else:
            st.info("今回の実行では、SWOT分析は生成されませんでした。入力内容をもう少し具体的にして再実行してみてください。")

    # レポート出力
    report_bytes = build_word_report(
        context=context,
        agents=agents,
        aggregated=aggregated,
        magi_raw_text=magi_text,
        image=image_for_report,
        swot=swot,
        enable_swot=enable_swot,
    )

    st.markdown(
        '<div class="magi-section-title">REPORT · EXPORT</div><hr class="magi-divider">',
        unsafe_allow_html=True,
    )

    file_name = "MAGI分析レポート_テキスト簡易版"
    if enable_swot:
        file_name += "+SWOT"
    file_name += ".docx"

    st.download_button(
        "MAGIレポート（Word）をダウンロード",
        data=report_bytes,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

else:
    st.info(
        "質問と必要なら補足テキストを入力し、右側のサイドバーで画像・音声・ファイルを指定してから、\n"
        "「MAGI による分析を実行」を押してください。"
    )
