import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="학습지원 SW 심의 완전정복", page_icon="🏫", layout="wide")

st.title("🏫 학습지원 SW 심의자료 자동 생성기")
st.markdown("""
2026학년도 학운위 심의를 위한 **[서식 1, 2, 3]** 내용을 생성합니다.
입력창에 **사이트 주소(URL)**를 넣거나, **내용을 직접 복사+붙여넣기** 하세요. 알아서 판단합니다!
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

def fetch_text_from_url(url):
    """URL에서 텍스트를 긁어오는 함수"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        if len(text) < 50:
            return "ERROR: 내용이 너무 짧습니다. 자바스크립트 차단 사이트일 수 있습니다."
        return text
    except Exception as e:
        return f"ERROR: 접속 실패 ({e})"

def get_content_from_input(user_input):
    """입력값이 URL인지 텍스트인지 판단하여 처리하는 함수"""
    if not user_input.strip():
        return "", "비어있음"
    
    # http로 시작하면 URL로 간주
    if user_input.strip().lower().startswith(("http://", "https://")):
        with st.spinner(f"🌐 URL 감지됨! 사이트 내용을 가져오는 중... ({user_input[:30]}...)"):
            scraped_text = fetch_text_from_url(user_input.strip())
            
            # 크롤링 실패 시 안내
            if scraped_text.startswith("ERROR"):
                return scraped_text, "URL 접속 실패"
            else:
                return scraped_text, f"URL 분석 ({user_input})"
    else:
        # http가 아니면 그냥 텍스트 붙여넣기로 간주
        return user_input, "사용자 직접 붙여넣기"

def analyze_with_gemini(main_text, privacy_text, info_source, api_key):
    """종합 분석 함수"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest') 
    
    prompt = f"""
    당신은 경상남도교육청의 '학습지원 소프트웨어 선정 심의'를 담당하는 행정 전문가 AI입니다.
    제공된 정보를 종합하여 보고서를 작성해주세요.

    [분석 소스 정보]
    - 출처 유형: {info_source}
    - 메인 정보(제품설명): {main_text[:30000]}
    - 개인정보처리방침 정보: {privacy_text[:50000]}

    ---
    ### 영역 1. 제품/서비스 개요 (서식 2 상단)
    *주로 [메인 정보]를 참고하여 작성하세요.*
    - 제품/서비스명: (서비스의 정확한 명칭)
    - 공급자(기업명): (운영 회사 이름)
    - 주요 내용 및 기능·특장점: (학습 도구로서의 핵심 기능을 3~4줄로 요약)

    ### 영역 2. 필수기준 세부 체크리스트 (서식 2 하단)
    *반드시 [개인정보처리방침 정보]를 근거로 판단하세요.*
    각 항목별로 '충족/미충족/확인불가'를 판단하고, 문서를 근거로 '증빙' 내용을 작성하세요.
    (내용이 부족해 판단이 어려우면 '확인불가'로 적으세요.)
    
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
      (해외 사이트라 13세 미만 제한(Children under 13)만 있다면 내용을 적고 '부분충족' 또는 '확인필요' 표시)
    
    **5. 책임자 및 위탁**
    - 5-1. 개인정보 보호책임자(CPO) 정보(이름/부서/연락처)가 있는가?
    - 5-2. 제3자 제공에 관한 정보가 있는가?
    - 5-3. 위·수탁 관계 정보가 있는가?

    ### 영역 3. 추천 의견서 초안 (서식 3)
    *[메인 정보]의 교육적 기능을 참고하여 작성하세요.*
    - 선정 이유: 이 소프트웨어를 수업에 활용했을 때 기대되는 교육적 효과 (2~3문장)

    ---
    [작성 원칙]
    - 한국어로 작성할 것.
    - 증빙 자료는 실제 텍스트 내용을 인용할 것.
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- 4. 메인 화면 구성 ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 제품 소개 (메인)")
    st.caption("URL을 넣거나, 사이트 내용을 복사해서 붙여넣으세요.")
    input_main = st.text_area("메인 정보 입력", height=200, placeholder="예: https://padlet.com 또는 제품 소개 텍스트 붙여넣기")

with col2:
    st.subheader("2️⃣ 개인정보처리방침 (필수)")
    st.caption("URL을 넣거나, 약관 전체를 복사해서 붙여넣으세요.")
    input_privacy = st.text_area("약관 정보 입력", height=200, placeholder="예: https://padlet.com/privacy 또는 약관 내용 통째로 붙여넣기")

st.write("") # 여백
analyze_btn = st.button("스마트 분석 시작 🚀", type="primary", use_container_width=True)

# --- 5. 분석 로직 실행 ---

if analyze_btn:
    if not api_key:
        st.error("👈 왼쪽 사이드바에 API Key를 먼저 입력해주세요!")
        st.stop()
        
    if not input_privacy:
        st.warning("⚠️ 심의를 위해 '개인정보처리방침' 정보는 필수입니다!")
    else:
        # 1. 입력값 처리 (URL이면 긁어오고, 텍스트면 그대로 씀)
        final_main_text, source_main = get_content_from_input(input_main)
        final_privacy_text, source_privacy = get_content_from_input(input_privacy)
        
        # 2. 에러 체크 (URL 접속 실패 시)
        error_msg = ""
        if "ERROR" in final_main_text: error_msg += f"❌ 메인 정보 URL 접속 실패: 직접 텍스트를 붙여넣어주세요.\n"
        if "ERROR" in final_privacy_text: error_msg += f"❌ 약관 URL 접속 실패: 직접 텍스트를 붙여넣어주세요.\n"
        
        if error_msg:
            st.error(error_msg)
            st.info("Tip: Gimkit, Padlet 등 일부 사이트는 보안 때문에 URL 분석이 안 됩니다. 내용을 복사(Ctrl+C)해서 입력창에 붙여넣기(Ctrl+V) 하세요.")
        else:
            # 3. AI 분석 요청
            try:
                with st.spinner("AI가 내용을 읽고 심의 기준을 분석 중입니다..."):
                    info_source = f"{source_main} + {source_privacy}"
                    result = analyze_with_gemini(final_main_text, final_privacy_text, info_source, api_key)
                    
                    st.success("🎉 분석 완료!")
                    
                    # 다운로드 & 결과 표시
                    st.download_button("📥 보고서 다운로드 (.txt)", result, "심의자료_완료.txt", use_container_width=True)
                    st.markdown(result)
                    
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")