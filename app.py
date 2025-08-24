# app.py — 청년 맞춤형 정책 추천 (Streamlit / near-miss + 코치봇)
import os
import re
import streamlit as st
import pandas as pd

# ─────────────────────────────────────────────────────────
# 페이지 설정
st.set_page_config(page_title="청년 맞춤형 정책 추천 PoC", layout="wide")
st.title("청년 맞춤형 정책 추천 — PoC (near-miss 포함 + 코치봇)")
st.caption("조건 입력 → 완전 적합/거의 적합을 구분해 보여주고, 코치봇이 신청 팁을 안내합니다.")

# ─────────────────────────────────────────────────────────
# 샘플 데이터 (원하면 행 추가/수정)
DATA = [
    {"name":"청년도약계좌","category":"금융상품","min_age":19,"max_age":34,
     "max_income":7500,"needs_non_homeowner":False,"employment_required":False,
     "benefit":"5년간 최대 5천만원 목돈 + 정부 기여금","popularity":5,"difficulty":3,
     "why_fit":"자산형성 시작 사회초년생 적합","apply_url":"https://www.fss.or.kr"},
    {"name":"청년 전월세보증금 대출","category":"금융상품","min_age":19,"max_age":34,
     "max_income":5000,"needs_non_homeowner":True,"employment_required":False,
     "benefit":"수도권 최대 1.2억원, 금리 2~3%","popularity":4,"difficulty":3,
     "why_fit":"무주택 청년 주거안정","apply_url":"https://www.hf.go.kr"},
    {"name":"내일배움카드","category":"지원제도","min_age":19,"max_age":34,
     "max_income":6000,"needs_non_homeowner":False,"employment_required":False,
     "benefit":"최대 500만원 직업훈련비 지원","popularity":5,"difficulty":2,
     "why_fit":"역량 강화/이직 준비","apply_url":"https://www.hrd.go.kr"},
    {"name":"국민취업지원제도","category":"지원제도","min_age":19,"max_age":34,
     "max_income":4000,"needs_non_homeowner":False,"employment_required":False,
     "benefit":"구직활동 지원금 + 취업알선","popularity":4,"difficulty":3,
     "why_fit":"청년 구직자 소득지원","apply_url":"https://www.kua.go.kr"},
    {"name":"청년월세지원","category":"생활지원","min_age":19,"max_age":34,
     "max_income":3900,"needs_non_homeowner":True,"employment_required":False,
     "benefit":"월 최대 20만원, 12개월 지원(지자체별 상이)","popularity":5,"difficulty":2,
     "why_fit":"월세 거주 청년 주거비 경감","apply_url":"https://www.bokjiro.go.kr"},
]
df = pd.DataFrame(DATA)

# ─────────────────────────────────────────────────────────
# 사이드바 입력
st.sidebar.header("내 프로필")
age = st.sidebar.slider("나이", 18, 45, 27, 1)
income = st.sidebar.slider("연소득(만원)", 0, 10000, 2800, 50)
home = st.sidebar.selectbox("주거상태", ["무주택","주택보유"])
emp = st.sidebar.selectbox("재직형태", ["취업","미취업/구직","자영업/프리랜서"])
sort_by = st.sidebar.selectbox("정렬기준", ["인기도","혜택 크기(설명 길이)","난이도(쉬운 순)"])
show_near = st.sidebar.checkbox("거의 적합(near miss)도 보기", True)

# ─────────────────────────────────────────────────────────
# 적합도 계산
def score_and_reason(row, age, income, home, emp):
    score = 0; ok = []; miss = []
    # 연령
    if row["min_age"] <= age <= row["max_age"]:
        score += 1; ok.append("연령 적합")
    else:
        miss.append(f"연령 {row['min_age']}~{row['max_age']}세")
    # 소득
    if income <= row["max_income"]:
        score += 1; ok.append("소득 적합")
    else:
        miss.append(f"소득 상한 {row['max_income']}만원")
    # 무주택 요건
    if row["needs_non_homeowner"]:
        if home == "무주택":
            score += 1; ok.append("무주택 요건")
        else:
            miss.append("무주택 필수")
    else:
        score += 1; ok.append("주거 무관")
    # 재직 요건
    if row["employment_required"]:
        if emp == "취업":
            score += 1; ok.append("재직 필수 충족")
        else:
            miss.append("재직 필수")
    else:
        score += 1; ok.append("재직 무관")
    return score, "; ".join(ok), "; ".join(miss)

rows = []
for _, r in df.iterrows():
    s, ok, miss = score_and_reason(r, age, income, home, emp)
    rows.append({**r.to_dict(), "eligibility_score": s, "ok_reasons": ok, "miss_reasons": miss})
res = pd.DataFrame(rows)

def sort_df(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty: return d
    if sort_by == "인기도":
        return d.sort_values(by=["popularity","name"], ascending=[False, True])
    if sort_by == "혜택 크기(설명 길이)":
        d = d.copy(); d["benefit_len"] = d["benefit"].astype(str).str.len()
        return d.sort_values(by=["benefit_len","popularity"], ascending=[False, False])
    return d.sort_values(by=["difficulty","popularity"], ascending=[True, False])  # 난이도(쉬운 순)

perfect = sort_df(res[res["eligibility_score"] == 4].copy())
near = sort_df(res[res["eligibility_score"] == 3].copy())

col1, col2 = st.columns(2)
with col1:
    st.subheader(f"✅ 완전 적합 ({len(perfect)}건)")
    if perfect.empty:
        st.info("완전 적합 항목이 없습니다.")
    else:
        st.dataframe(
            perfect[["name","category","benefit","why_fit","popularity","difficulty","apply_url","ok_reasons"]]
            .reset_index(drop=True), use_container_width=True
        )
with col2:
    if show_near:
        st.subheader(f"🟡 거의 적합 ({len(near)}건)")
        if near.empty:
            st.info("거의 적합 항목이 없습니다.")
        else:
            st.dataframe(
                near[["name","category","benefit","why_fit","popularity","difficulty","apply_url","miss_reasons"]]
                .reset_index(drop=True), use_container_width=True
            )

st.caption(f"입력: 나이 {age}세 / 연소득 {income}만원 / {home} / {emp} · 정렬: {sort_by}")
st.divider()

# ─────────────────────────────────────────────────────────
# 코치봇 (두 모드: 규칙 기반 / LLM)
st.header("AI 금융 코치")

# 세션 대화 메모리
if "chat" not in st.session_state:
    st.session_state.chat = []

# 모드 선택
use_llm = st.checkbox("LLM 모드 사용 (OpenAI API 키 필요)", value=False, help="환경변수 OPENAI_API_KEY 설정 시 사용 가능")
api_key_present = bool(os.getenv("OPENAI_API_KEY"))

if use_llm and not api_key_present:
    st.warning("OPENAI_API_KEY 환경변수가 없어 LLM 모드를 사용할 수 없습니다. 규칙 기반으로 동작합니다.")
    use_llm = False

# 규칙 기반 빠른 답변 (키워드 룰)
def rule_based_answer(q: str) -> str:
    q = (q or "").lower().strip()

    # 현재 프로필 요약
    header = f"**내 프로필**: 나이 {age}세 · 연소득 {income}만원 · {home} · {emp}\n"

    # 1) 키워드로 특정 제도/상품 직접 조회
    for _, r in df.iterrows():
        key = r["name"].lower().replace(" ", "")
        if key in q or r["name"].lower() in q:
            return (
                header +
                f"\n### {r['name']} ({r['category']})\n"
                f"- 혜택: {r['benefit']}\n"
                f"- 적합 사유: {r['why_fit']}\n"
                f"- 신청/안내: {r['apply_url']}\n"
                "\n※ 실제 요건은 공식 안내에서 최종 확인하세요."
            )

    # 2) 프로필과 매칭된 결과 기반 추천(완전 적합 → 거의 적합 순)
    def fmt_rows(tbl, title):
        if tbl.empty:
            return f"**{title}**: 해당 없음\n"
        lines = [f"**{title} ({len(tbl)}건)**"]
        for r in tbl[["name","category","benefit","apply_url"]].itertuples(index=False):
            lines.append(f"- **{r.name}** ({r.category}) — {r.benefit}  \n  ▶ {r.apply_url}")
        return "\n".join(lines) + "\n"

    # 질문에 주거/무주택 뉘앙스가 있으면 주거 관련 먼저 보여주기
    wants_housing = any(k in q for k in ["무주택","전세","월세","주거","보증금","청약","집"])
    pf = perfect.copy()
    nr = near.copy()
    if wants_housing:
        pf = pf.sort_values(by=pf["name"].str.contains("전월세|월세|주거|청약"), ascending=False)
        nr = nr.sort_values(by=nr["name"].str.contains("전월세|월세|주거|청약"), ascending=False)

    body = fmt_rows(pf, "✅ 완전 적합") + "\n" + fmt_rows(nr, "🟡 거의 적합")

    # 3) 아무 매칭도 없으면 힌트
    if pf.empty and nr.empty:
        hint = (
            "\n적합 항목이 없어요. 아래를 확인해 보세요.\n"
            "- 연소득(만원)을 실제보다 높게 넣진 않았는지\n"
            "- ‘주거상태’가 무주택/보유 중 어디에 해당하는지\n"
            "- 정렬/필터를 바꿔보기\n"
        )
    else:
        hint = "\n각 항목의 링크로 이동하여 최신 요건·서류를 확인하세요."

    return header + "\n" + body + hint


# LLM 호출 (선택)
def llm_answer(q: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def topn(tbl, n=6):
        if tbl.empty: return "없음"
        rows = []
        for r in tbl[["name","category","benefit","apply_url"]].head(n).itertuples(index=False):
            rows.append(f"- {r.name} ({r.category}) — {r.benefit} (링크: {r.apply_url})")
        return "\n".join(rows)

    context = (
        f"[사용자 프로필] 나이={age}, 소득(만원)={income}, 주거={home}, 재직={emp}\n"
        f"[완전 적합]\n{topn(perfect)}\n"
        f"[거의 적합]\n{topn(near)}\n"
        "규칙: 사실만 답하고, 모르면 공식 링크 확인하도록 안내. 과장/추정/단정 금지. 간결하고 한국어로."
    )

    messages = [
        {"role":"system","content":"너는 청년 정책·금융 가이드를 한국어로 간결하게 제공하는 코치봇이다. 허위 정보 금지."},
        {"role":"user","content": f"{context}\n\n질문: {q}"}
    ]
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2,
        max_tokens=600,
    )
    return resp.choices[0].message.content.strip()


# 채팅 UI
for role, content in st.session_state.chat:
    with st.chat_message(role):
        st.markdown(content)

user_msg = st.chat_input("질문을 입력하세요. 예) 무주택인데 받을 수 있는 지원은?")
if user_msg:
    st.session_state.chat.append(("user", user_msg))
    with st.chat_message("user"):
        st.markdown(user_msg)

    if use_llm:
        try:
            answer = llm_answer(user_msg)
        except Exception as e:
            answer = f"LLM 호출 실패로 규칙 기반으로 답합니다.\n\n{rule_based_answer(user_msg)}\n\n(error: {e})"
    else:
        answer = rule_based_answer(user_msg)

    st.session_state.chat.append(("assistant", answer))
    with st.chat_message("assistant"):
        st.markdown(answer)

