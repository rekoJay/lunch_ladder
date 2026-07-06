import streamlit as st
import random
import time

# 1. 페이지 기본 설정 (앱 접근성 및 UI)
st.set_page_config(page_title="오늘의 점심 사다리", page_icon="🍱", layout="centered")

st.title("🍱 점심 사다리타기")
st.write("매일 점심 고르기 힘드시죠? 이모지 후보를 추가하고 사다리를 타보세요!")

# 2. 세션 상태를 이용한 유연한 식당(이모지) 데이터 관리
# 기본값으로 귀여운 이모지들을 미리 넣어둡니다.
if 'restaurants' not in st.session_state:
    st.session_state.restaurants = ['🍔', '🍣', '🍜', '🍕', '🥩', '🥗', '🌮']

# 3. 데이터 추가/삭제 함수
def add_emoji(emoji):
    # 빈 칸이 아니면서 중복되지 않을 때만 추가
    if emoji and emoji not in st.session_state.restaurants:
        st.session_state.restaurants.append(emoji)

def remove_emoji(emoji):
    if emoji in st.session_state.restaurants:
        st.session_state.restaurants.remove(emoji)

# 4. 사용자 인터페이스 (후보 늘리거나 줄이는 유연성 제공)
st.subheader("🛠️ 후보 관리")
col1, col2 = st.columns(2)

with col1:
    new_emoji = st.text_input("새로운 메뉴 이모지 (예: 🥪, 🥘)", max_chars=2)
    if st.button("추가하기"):
        add_emoji(new_emoji)
        st.rerun() # 화면 새로고침

with col2:
    target_emoji = st.selectbox("삭제할 이모지 선택", ['선택'] + st.session_state.restaurants)
    if st.button("삭제하기") and target_emoji != '선택':
        remove_emoji(target_emoji)
        st.rerun()

st.divider()

# 5. 현재 등록된 식당 시각화
st.subheader("👀 현재 점심 후보")
st.write("  ".join(st.session_state.restaurants))

st.divider()

# 6. 사다리타기(추첨) 로직 및 애니메이션 효과
if st.button("🚀 사다리 타기 시작!", use_container_width=True):
    if not st.session_state.restaurants:
        st.error("후보가 없습니다! 메뉴를 먼저 추가해주세요.")
    else:
        # 긴장감을 주기 위한 프로그레스 바와 스피너
        progress_text = "사다리를 타고 내려가는 중... 🏃‍♂️💨"
        my_bar = st.progress(0, text=progress_text)
        
        for percent_complete in range(100):
            time.sleep(0.01)
            my_bar.progress(percent_complete + 1, text=progress_text)
            
        time.sleep(0.5) # 잠시 대기
        my_bar.empty() # 프로그레스 바 숨김
        
        # 결과 도출
        result = random.choice(st.session_state.restaurants)
        
        # 결과 화면 출력
        st.success("도착!")
        st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{result}</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>오늘의 점심 당첨! 🎉</h3>", unsafe_allow_html=True)
        st.balloons() # 축하 효과