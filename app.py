import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="학습지원 SW 심의 완전정복", page_icon="🏫", layout="wide")

st.title("🏫 학습지원 SW 심의자료 자동 생성기")
st.markdown("""
2026학년도 학운위 심의를 위한 **[서식 1, 2, 3]** 내용을 한 번에 생성합니다.
정확한 분석을 위해 **두 가지 URL**을 모두 입력해 주시는 것이 좋습니다.
""")

# --- 2. 사이드바: 설정 ---
with st.sidebar:
    st.header("설정")
    
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ 공용 API 키가 적용되었습니다.")
    else:
        api_key = st.text_input("Google API Key를 입력하세요", type="password")
        
        st.caption("키가 없으신가요? 아래 버튼을 눌러보세요!")
        st.link_button(
            label="📺 개인 API 키 발급 받는 방법 (영상)", 
            url="https://youtu.be/gCFqpFXY578?si=b7wa0DNXvzimrOTh"
        )
        st.info("발급받은 키는 저장되지 않고 휘발되니 안심하세요.")

# --- 3. 기능 함수 정의 ---

def get_website_text(url):
    """URL에서 텍스트만 긁어오는 함수"""
    if not url: return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        return f"에러: {e}"

def analyze_with_gemini(main_text, privacy_text, main_url, api_key):
    """두 개의 텍스트 소스를 모두 활용해 분석하는 함수"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-lastest') 
    
    prompt = f"""
    당신은 경상남도교육청의 '학습지원 소프트웨어 선정 심의'를 담당하는 행정 전문가 AI입니다.
    제공된 [메인 홈페이지 정보]와 [개인정보처리방침 정보]를 종합하여 보고서를 작성해주세요.

    [분석 소스]
    1. 메인 사이트 URL: {main_url}
    2. 메인 페이지 텍스트(제품정보용): {main_text[:20000]}
    3. 개인정보처리방침 텍스트(심의기준용): {privacy_text[:30000]}

    ---
    ### 영역 1. 제품/서비스 개요 (서식 2 상단)
    *주로 [메인 페이지 텍스트]를 참고하여 작성하세요.*
    - 제품/서비스명: (서비스의 정확한 명칭)
    - 공급자(기업명): (운영 회사 이름, 하단 카피라이트 등 참조)
    - 주요 내용 및 기능·특장점: (학습 도구로서의 핵심 기능을 3~4줄로 요약)

    ### 영역 2. 필수기준 세부 체크리스트 (서식 2 하단)
    *반드시 [개인정보처리방침 텍스트]를 근거로 판단하세요.*
    각 항목별로 '충족/미충족/확인불가'를 판단하고, 약관 내 문장을 찾아 '증빙'에 적으세요.
    
    **1. 최소처리 원칙 준수**
    - 1-1. 개인정보가 최소한으로 수집되는가?
    - 1-2. 개인정보 수집·이용 목적이 기재되어 있는가?
    - 1-3. 수집항목, 보유기간 등이 기재되어 있는가?
    
    **2. 개인정보 안전조치 의무**
    - 2-1. 안전성 확보 조치(암호화, 보안 등) 사항이 기재되어 있는가?
    
    **3. 이용자 권리**
    - 3-1. 열람·정정·삭제·처리정지 요구 절차가 안내되어 있는가?
    
    **4. 아동 보호**
    - 4-1. 만 14세 미만 아동(Children)의 법정대리인 동의 절차가 있는가?
      (해외 사이트의 경우 '13세 미만 이용 제한' 등으로 되어 있다면 그 내용을 적고 '부분충족' 또는 '확인필요'로 표시)
    
    **5. 책임자 및 위탁**
    - 5-1. 개인정보 보호책임자(CPO) 정보(이름/부서/연락처)가 있는가?
    - 5-2. 제3자 제공에 관한 정보가 있는가?
    - 5-3. 위·수탁 관계 정보가 있는가?

    ### 영역 3. 추천 의견서 초안 (서식 3)
    *[메인 페이지 텍스트]의 교육적 기능을 참고하여 작성하세요.*
    - 선정 이유: 이 소프트웨어를 수업에 활용했을 때 기대되는 교육적 효과 (2~3문장)

    ---
    [작성 원칙]
    - 한국어로 작성할 것.
    - 증빙 자료는 실제 약관 문구를 인용할 것.
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- 4. 메인 화면 구성 ---

col1, col2 = st.columns(2)
with col1:
    st.subheader("1️⃣ 메인 사이트 URL")
    st.caption("제품명, 주요 기능 파악용 (예: padlet.com)")
    main_url = st.text_input("메인 URL", label_visibility="collapsed", placeholder="https://padlet.com")

with col2:
    st.subheader("2️⃣ 개인정보처리방침 URL")
    st.caption("필수 기준 충족 여부 확인용 (예: padlet.com/privacy)")
    privacy_url = st.text_input("약관 URL", label_visibility="collapsed", placeholder="https://padlet.com/about/privacy")

st.write("")
analyze_btn = st.button("종합 분석 시작 🚀", type="primary", use_container_width=True)

if analyze_btn:
    if not api_key:
        st.error("👈 왼쪽 사이드바에 API Key를 먼저 입력해주세요!")
        st.stop()
        
    if not privacy_url:
        st.warning("⚠️ 최소한 '개인정보처리방침 URL'은 입력해야 심의가 가능합니다.")
    else:
        with st.spinner("두 개의 사이트를 모두 읽고 분석 중입니다... (약 30초)"):
            # 1. 텍스트 수집
            main_text = get_website_text(main_url) if main_url else "메인 URL이 입력되지 않음."
            privacy_text = get_website_text(privacy_url)
            
            error_msg = ""
            if "에러" in main_text: error_msg += f"[메인URL 오류] {main_text}\n"
            if "에러" in privacy_text: error_msg += f"[약관URL 오류] {privacy_text}\n"
            
            if error_msg and not privacy_text: # 약관도 못 읽었으면 중단
                st.error(f"사이트 접속 실패:\n{error_msg}")
            else:
                try:
                    # 2. AI 분석
                    result = analyze_with_gemini(main_text, privacy_text, main_url, api_key)
                    
                    st.success("🎉 분석 완료! 제품 정보와 법적 기준을 모두 확인했습니다.")
                    
                    tab1, tab2 = st.tabs(["📄 종합 보고서", "🔍 원문 데이터"])
                    
                    with tab1:
                        st.markdown(result)
                        st.download_button("📥 보고서 다운로드 (.txt)", result, "심의자료_완료.txt")

                    with tab2:
                        st.write("### 🔹 메인 페이지 텍스트")
                        st.text_area("Main", main_text, height=150)
                        st.write("### 🔸 개인정보처리방침 텍스트")
                        st.text_area("Privacy", privacy_text, height=150)
                        
                except Exception as e:
                    st.error(f"오류 발생: {e}")