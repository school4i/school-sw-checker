import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="학습지원 SW 심의 도우미", page_icon="🏫")

st.title("🏫 학습지원 SW 필수기준 자동 분석기")
st.markdown("""
2026학년도 학운위 심의를 위한 **[서식 2] 필수기준 체크리스트** 초안을 만들어 드립니다.
분석하려는 사이트의 **'개인정보처리방침(Privacy Policy)'** URL을 입력해주세요.
""")

# --- 2. 사이드바: API 키 입력 및 안내 ---
with st.sidebar:
    st.header("설정")
    
    # Secrets에 키가 있으면 그걸 쓰고, 없으면 입력창을 보여줌
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ 공용 API 키가 적용되었습니다.")
    else:
        api_key = st.text_input("Google API Key를 입력하세요", type="password")
        
        # 🟢 요청하신 유튜브 링크 버튼 추가
        st.caption("키가 없으신가요? 아래 버튼을 눌러보세요!")
        st.link_button(
            label="📺 개인 API 키 발급 받는 방법 (영상)", 
            url="https://youtu.be/gCFqpFXY578?si=b7wa0DNXvzimrOTh"
        )
        st.info("발급받은 키는 저장되지 않고 휘발되니 안심하세요.")

# --- 3. 기능 함수 정의 ---

def get_website_text(url):
    """URL에서 텍스트만 긁어오는 함수"""
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

def analyze_with_gemini(text_content, api_key):
    """Gemini에게 분석을 요청하는 함수"""
    genai.configure(api_key=api_key)
    # 최신 모델 사용 (1.5 Flash)
    model = genai.GenerativeModel('gemini-flash-latest') 
    
    prompt = f"""
    당신은 대한민국 학교의 행정 업무를 돕는 AI입니다. 
    아래 제공된 [약관/개인정보처리방침 텍스트]를 분석하여, 
    '학습지원 소프트웨어 선정 필수기준' 5가지 항목의 충족 여부를 판단해주세요.

    [분석 기준 - 필수항목 5가지]
    1. 최소처리 원칙 준수: 수집항목, 목적, 보유기간이 명시되어 있는가?
    2. 개인정보 안전조치 의무: 암호화, 접근통제 등 안전성 확보 조치가 언급되어 있는가?
    3. 이용자 권리: 열람, 정정, 삭제, 처리정지 요구 절차가 있는가?
    4. 아동 보호: 만 14세 미만 아동(또는 Children)에 대한 보호 조치나 법정대리인 동의 절차가 있는가?
    5. 책임자 및 위탁: 개인정보 보호책임자(CPO) 정보나 연락처가 있는가?

    [출력 형식]
    각 항목별로 다음 형식에 맞춰 한국어로 작성해주세요.
    - 결과: (충족 / 미충족 / 확인불가 중 택 1)
    - 증빙: (약관에서 찾은 근거 문장을 짧게 발췌)
    - 설명: (판단 이유를 한 문장으로 요약)

    [분석할 텍스트]
    {text_content[:30000]} 
    (텍스트가 너무 길면 앞부분 30,000자만 분석합니다)
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- 4. 메인 화면 구성 ---

url = st.text_input("분석할 URL 입력 (개인정보처리방침 페이지 주소 권장)", placeholder="예: https://gimkit.com/privacy")

if st.button("분석 시작 🚀"):
    if not api_key:
        st.error("👈 왼쪽 사이드바에 API Key를 먼저 입력해주세요!")
        st.stop() # 키가 없으면 여기서 멈춤
        
    if not url:
        st.warning("URL을 입력해주세요!")
    else:
        with st.spinner("사이트를 읽고 분석 중입니다... 잠시만 기다려주세요 (약 10~20초)"):
            site_text = get_website_text(url)
            
            if "에러" in site_text:
                st.error(f"사이트 접속에 실패했습니다. 올바른 URL인지 확인해주세요.\n({site_text})")
            else:
                try:
                    result = analyze_with_gemini(site_text, api_key)
                    
                    st.success("분석이 완료되었습니다!")
                    st.subheader("📋 [서식 2] 작성 참고 자료")
                    st.warning("⚠️ 이 내용은 AI 분석 결과이므로, 반드시 원문과 대조하여 최종 확인하시기 바랍니다.")
                    
                    st.markdown(result)
                    
                    with st.expander("AI가 읽은 사이트 원문 보기"):
                        st.write(site_text)
                        
                except Exception as e:
                    st.error(f"AI 분석 중 오류가 발생했습니다: {e}")