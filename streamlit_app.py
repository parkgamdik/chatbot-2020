import streamlit as st
from openai import OpenAI

# -----------------------------
# 앱 기본 정보
# -----------------------------
st.title("💬 박감독의 첫번째 수다봇 – 감정 공감 모드")
st.write(
    "영화감독 박감독의 감성 채팅방입니다.\n"
    "이 앱은 OpenAI API 키가 필요합니다. [발급 링크](https://platform.openai.com/account/api-keys)\n"
    "먼저 **현재 감정 상태**를 선택(또는 직접 입력)해 주세요. 그 감정에 맞춰 공감과 위로를 드립니다."
)

# -----------------------------
# API 키 입력
# -----------------------------
openai_api_key = st.text_input("OpenAI API Key", type="password")

# -----------------------------
# 감정 상태 입력 UI
# -----------------------------
st.subheader("🧠 현재 감정 상태")
preset = [
    "기쁨", "평온", "설렘", "감사",
    "슬픔", "불안", "우울", "외로움",
    "분노", "지침/번아웃", "혼란", "무기력", "스트레스", "걱정"
]
col1, col2 = st.columns(2)
with col1:
    emotion_select = st.selectbox("감정 선택", ["선택 안 함"] + preset, index=0)
with col2:
    custom_emotion = st.text_input("직접 입력 (선택 대신 자유롭게)")

# 감정 최종값 결정
emotion = custom_emotion.strip() if custom_emotion.strip() else (emotion_select if emotion_select != "선택 안 함" else "")

# 감정 상태 유지
if "emotion" not in st.session_state:
    st.session_state.emotion = ""
if emotion:
    st.session_state.emotion = emotion

# -----------------------------
# 세션 메시지 초기화
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# 안내/검증
# -----------------------------
if not openai_api_key:
    st.info("계속하려면 OpenAI API 키를 입력해 주세요.", icon="🗝️")
elif not st.session_state.emotion:
    st.info("먼저 상단에서 **현재 감정 상태**를 선택하거나 직접 입력해 주세요.", icon="💬")
else:
    # -----------------------------
    # 모델/창의성 옵션(선택)
    # -----------------------------
    with st.expander("⚙️ 고급 설정", expanded=False):
        model = st.selectbox(
            "모델 선택",
            ["gpt-4o-mini", "gpt-4.1-mini", "gpt-3.5-turbo"],
            index=0
        )
        temperature = st.slider("창의성(temperature)", 0.0, 1.2, 0.8, 0.1)

    # -----------------------------
    # 시스템 프롬프트(감성 규칙)
    # -----------------------------
    system_prompt = f"""
당신은 공감형 감성 대화 파트너입니다.
사용자가 제공한 현재 감정 상태: "{st.session_state.emotion}"

대화 규칙:
1) 먼저 사용자의 감정을 1문장으로 '부드럽게 재진술'합니다. (예: "지금은 ○○한 마음이시군요.")
2) 이어서 2~3문장 안에서 따뜻한 위로/공감을 전합니다.
3) 마지막에 1문장으로 '실제로 해볼 수 있는 아주 작은 제안'을 덧붙입니다. (예: 호흡, 산책, 한 줄 일기 등)
톤과 스타일:
- 존댓말, 시적이고 문학적인 어조, 다정하지만 과장되지 않게
- 실천 가능한 한 가지 행동을 꼭 제시 (과제는 작고 구체적으로)
- 너무 길지 않게: 문장 3~5개 내외, 각 문장은 간결하게
- 유머는 상황이 가볍거나 안전할 때만 아주 은은하게 사용
- 비의학적 조언만; 위기/전문 상담이 필요한 경우 도움을 권유
"""

    # -----------------------------
    # 사용자 입력
    # -----------------------------
    prompt = st.chat_input("무슨 일이 있었는지 편하게 적어주세요. (감정에 얽힌 상황, 오늘 있었던 일 등)")

    if prompt:
        # 메시지 저장/표시 (user)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # OpenAI 클라이언트
        client = OpenAI(api_key=openai_api_key)

        # 메시지 구성: 시스템 프롬프트 + (감정 태그) + 기존 대화
        # 감정을 모델이 분명히 인식하도록, 첫 메시지에 감정 태그를 덧붙입니다.
        messages = [{"role": "system", "content": system_prompt}]
        messages += [{"role": "user", "content": f"[현재 감정: {st.session_state.emotion}]"}]
        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        # 응답 스트리밍
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )

        # 스트림 출력 및 저장
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # 작게 후속 팁
        st.caption("💡 팁: 감정이 바뀌면 상단의 감정 선택값을 바꿔보세요. 응답 톤이 함께 달라집니다.")
