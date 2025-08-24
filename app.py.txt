# app.py — 청년 맞춤형 정책 추천 (Streamlit / 링크 배포용)
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="청년 맞춤형 정책 추천 PoC", layout="wide")
st.title("청년 맞춤형 정책 추천 — PoC (near-miss 포함 + 코치봇)")
st.caption("조건 입력 → 완전 적합/거의 적합을 구분해 보여줍니다.")

# 0) 샘플 데이터 (원하면 여기 행을 추가/수정하세요)
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
     "benefit":"월 최대 20만원, 12개월 지원","popularity":5,"difficulty":2,
     "why_fit":"월세 거주 청년 주거비 경감","apply_url":"https://www.bokjiro.go.kr"},
]

df = pd.DataFrame(DATA)

# 1) 입력(사이드바)
st.sidebar.header("내 프로필")
age = st.sidebar.slider("나이", 18, 45, 27, 1)
income = st.sidebar.slider("연소득(만원)", 0, 10000, 2800, 50)
home = st.sidebar.selectbox("주거상태", ["무주택","주택보유"])
emp = st.sidebar.selectbox("재직형태", ["취업","미취업/구직","자영업/프리랜서"])
sort_by = st.sidebar.selectbox("정렬기준", ["인기도","혜택 크기(설명 길이)","난이도(쉬운 순)"])
show_near = st.sidebar.checkbox("거의 적합(near miss)도 보기", True)

# 2) 적합도 평가
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

# 3) 계산
rows = []
for _, r in df.iterrows():
    s, ok, miss = score_and_reason(r, age, income, home, emp)
    rows.append({**r.to_dict(), "eligibility_score": s, "ok_reasons": ok, "miss_reasons": miss})
res = pd.DataFrame(rows)

# 4) 정렬
def sort_df(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty: return d
    if sort_by == "인기도":
        return d.sort_values(by=["popularity","name"], ascending=[False, True])
    if sort_by == "혜택 크기(설명 길이)":
        d = d.copy(); d["benefit_len"] = d["benefit"].astype(str).str.len()
        return d.sort_values(by=["benefit_len","popularity"], ascending=[False, False])
    return d.sort_values(by=["difficulty","popularity"], ascending=[True, False])  # 난이도(쉬운 순)

# 5) 완전 적합/거의 적합
perfect = sort_df(res[res["eligibility_score"] == 4].copy())
near = sort_df(res[res["eligibility_score"] == 3].copy())

# 6) 출력
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

# ====== 규칙 기반 AI 코치봇 (간단) ======
st.header("AI 금융 코치 (간단 PoC)")
user_q = st.text_input("무엇이 궁금하신가요? 예: 무주택인데 가능한 혜택 알려줘")

def coachbot_answer(q: str) -> str:
    q = (q or "").lower().strip()
    if not q:
        return "예) '무주택인데 가능한 혜택 알려줘', '내일배움카드 신청서류 알려줘'"

    if ("무주택" in q) or ("전세" in q) or ("월세" in q) or ("주거" in q):
        return ("무주택/주거 관련:\n"
                "- 청년 전월세보증금 대출: 소득·연령 요건 충족 시 저금리 보증금 대출\n"
                "- 청년월세지원: 지자체별 월세 지원(예: 월 최대 20만원, 12개월)\n"
                "▶ 상단 ‘완전 적합/거의 적합’ 표를 확인하고 ‘apply_url’ 링크로 이동하세요.")
    if ("교육" in q) or ("자격" in q) or ("훈련" in q):
        return ("교육/자격 관련:\n"
                "- 내일배움카드: 최대 500만원 훈련비(분야별 상이)\n"
                "- 국민취업지원제도: 구직활동 지원금 + 취업알선\n"
                "▶ 상단 추천 결과에서 세부 조건을 확인하세요.")
    if ("소득" in q) or ("연봉" in q):
        return ("소득 입력 팁:\n"
                "- ‘연소득(만원)’ 슬라이더를 실제 연소득에 맞춰 조정하면\n"
                "  상단 표에서 ‘완전 적합/거의 적합’이 자동 반영됩니다.")
    if ("신청" in q) or ("서류" in q) or ("방법" in q):
        return ("신청 가이드:\n"
                "- 각 항목의 ‘apply_url’를 클릭해 공식 안내를 확인하세요.\n"
                "- 공통 준비서류: 신분증, 소득/재직 증빙, 임대차계약서(주거), 훈련계획(교육) 등.")
    return ("상단 입력(나이/소득/주거/재직)을 조절하면 추천이 갱신됩니다.\n"
            "특정 제도를 묻고 싶다면: 예) '내일배움카드 신청서류 알려줘'")

st.text_area("코치봇 답변", value=coachbot_answer(user_q), height=160)
