import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="학습지원 SW 심의 완전정복", page_icon="🏫", layout="wide")

st.title("🏫 학습지원 SW 심의자료 자동 생성기")
st.markdown("""
2026학년도 학운위 심의를 위한 **[서식 1, 2, 3]** 내용을 생성합니다.
**Gimkit, Padlet** 등 일부 사이트는 URL 분석이 안 될 수 있습니다. 그럴 땐 **텍스트를 직접 붙여넣어 주세요.**
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

def analyze_with_gemini(main_text, privacy_text, info_source, api_key):
    """종합 분석 함수"""
    genai.configure(api_key=api_key)
    # 최신 모델 이름 (오타 수정됨)
    model = genai.GenerativeModel('gemini-flash-latest') 
    
    prompt = f"""
    당신은 경상남도교육청의 '학습지원 소프트웨어 선정 심의'를 담당하는 행정 전문가 AI입니다.
    제공된 정보를 종합하여 보고서를 작성해주세요.

    [분석 소스 정보]
    - 출처: {info_source}
    - 메인 페이지 텍스트(제품정보용): {main_text[:30000]}
    - 개인정보처리방침 텍스트(심의기준용): {privacy_text[:50000]}

    ---
    ### 영역 1. 제품/서비스 개요 (서식 2 상단)
    *주로 [메인 페이지 텍스트]를 참고하여 작성하세요.*
    - 제품/서비스명: (서비스의 정확한 명칭)
    - 공급자(기업명): (운영 회사 이름)
    - 주요 내용 및 기능·특장점: (학습 도구로서의 핵심 기능을 3~4줄로 요약)

    ### 영역 2. 필수기준 세부 체크리스트 (서식 2 하단)
    *반드시 [개인정보처리방침 텍스트]를 근거로 판단하세요.*
    각 항목별로 '충족/미충족/확인불가'를 판단하고, 약관 내 문장을 찾아 '증빙'에 적으세요.
    (만약 텍스트가 부족하여 판단이 어려우면 솔직하게 '확인불가'로 적으세요.)
    
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

st.info("💡 **Gimkit, Padlet** 같은 사이트는 URL 분석 시 내용이 안 보일 수 있습니다. 그럴 땐 아래 **[직접 붙여넣기]** 탭을 이용하세요.")

tab_url, tab_paste = st.tabs(["🌐 URL로 분석하기", "📝 텍스트 직접 붙여넣기 (확실함)"])

# [탭 1] 기존 URL 방식
with tab_url:
    col1, col2 = st.columns(2)
    with col1:
        main_url = st.text_input("메인 사이트 URL", placeholder="https://www.gimkit.com")
    with col2:
        privacy_url = st.text_input("개인정보처리방침 URL", placeholder="https://www.gimkit.com/privacy")
    
    btn_url = st.button("URL로 분석 시작 🚀", type="primary")

# [탭 2] 텍스트 붙여넣기 방식
with tab_paste:
    st.caption("사이트에 접속해서 `Ctrl+A`(전체선택), `Ctrl+C`(복사) 후 여기에 붙여넣으세요.")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        paste_main = st.text_area("1️⃣ 메인 페이지 내용 붙여넣기", height=200, placeholder="제품 소개가 있는 메인 화면의 글자를 복사해 넣으세요.")
    with col_p2:
        paste_privacy = st.text_area("2️⃣ 개인정보처리방침 내용 붙여넣기", height=200, placeholder="약관(Privacy Policy) 페이지의 글자를 통째로 복사해 넣으세요.")
    
    btn_paste = st.button("텍스트로 분석 시작 📝", type="primary")

# --- 5. 분석 로직 실행 ---

final_main_text = ""
final_privacy_text = ""
source_info = ""
do_analysis = False

if btn_url:
    if not api_key:
        st.error("👈 왼쪽 사이드바에 API Key를 먼저 입력해주세요!")
    elif not privacy_url:
        st.warning("약관 URL은 필수입니다.")
    else:
        with st.spinner("URL에서 텍스트를 가져오는 중..."):
            final_main_text = get_website_text(main_url)
            final_privacy_text = get_website_text(privacy_url)
            
            # 자바스크립트 차단 확인
            if "enable JavaScript" in final_privacy_text or len(final_privacy_text) < 100:
                st.error("⛔ 이 사이트는 URL 분석을 막아놨습니다! (JavaScript 필수)")
                st.warning("👉 위의 **[📝 텍스트 직접 붙여넣기]** 탭을 클릭해서 직접 복사+붙여넣기 해주세요.")
            else:
                source_info = f"URL 분석 ({main_url})"
                do_analysis = True

if btn_paste:
    if not api_key:
        st.error("👈 왼쪽 사이드바에 API Key를 먼저 입력해주세요!")
    elif not paste_privacy:
        st.warning("개인정보처리방침 내용은 필수입니다.")
    else:
        final_main_text = paste_main
        final_privacy_text = paste_privacy
        source_info = "사용자 직접 붙여넣기"
        do_analysis = True

# 실제 AI 분석 요청
if do_analysis:
    with st.spinner("AI가 법적 기준을 꼼꼼히 분석 중입니다... (약 20초)"):
        try:
            result = analyze_with_gemini(final_main_text, final_privacy_text, source_info, api_key)
            
            st.success("🎉 분석 완료!")
            st.download_button("📥 보고서 다운로드 (.txt)", result, "심의자료_완료.txt")
            st.markdown(result)
            
        except Exception as e:
            st.error(f"오류 발생: {e}")