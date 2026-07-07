import streamlit as st
import streamlit.components.v1 as components
import json
import base64
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="점심 사다리타기", page_icon="🪜", layout="centered")

st.markdown("<h1 style='word-break: keep-all;'>🪜 점심 사다리타기</h1>", unsafe_allow_html=True)

# 1. 구글 시트 DB 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 데이터 불러오기 (캐시 없이 항상 최신 데이터 읽기)
try:
    df = conn.read(worksheet="시트1", ttl=0)
    df = df.dropna(how="all") # 빈 줄 제거
except Exception as e:
    st.error("구글 시트 연결 오류! Secrets 설정이나 공유 권한을 확인해주세요.")
    df = pd.DataFrame(columns=["name", "type", "content"])

# 데이터프레임을 리스트형 딕셔너리로 변환
restaurants = df.to_dict('records')

EMOJI_LIST = ["🍔", "🍣", "🍜", "🍕", "🥩", "🥗", "🌮", "🍱", "🍛", "🍝", "🥪", "🥘", "🍚", "🍲"]

# 구글 시트 업데이트 함수
def update_sheet(new_df):
    conn.update(worksheet="시트1", data=new_df)

# 3. 사용자 인터페이스 (식당 추가 및 삭제)
with st.expander("🛠️ 식당 후보 관리 (자동 저장됨)", expanded=True):
    new_name = st.text_input("식당 이름 (예: 김밥천국)")
    icon_type = st.radio("아이콘 추가 방식", ["기본 이모지 선택", "나만의 이미지 업로드"], horizontal=True)
    
    icon_content = None
    item_type = "emoji"
    
    if icon_type == "기본 이모지 선택":
        icon_content = st.selectbox("어울리는 이모지", EMOJI_LIST)
        item_type = "emoji"
    else:
        uploaded_file = st.file_uploader("식당 이미지 파일 선택", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            bytes_data = uploaded_file.read()
            b64_str = base64.b64encode(bytes_data).decode()
            icon_content = f"data:image/{uploaded_file.type.split('/')[-1]};base64,{b64_str}"
            item_type = "image"
            
    if st.button("➕ 식당 추가하고 시트에 저장", use_container_width=True):
        if new_name:
            if item_type == "image" and icon_content is None:
                st.error("이미지 파일을 업로드해주세요!")
            else:
                # 새 데이터를 데이터프레임에 붙이고 시트에 덮어쓰기
                new_row = pd.DataFrame([{"name": new_name, "type": item_type, "content": icon_content}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                update_sheet(updated_df)
                st.success("구글 시트에 성공적으로 저장되었습니다!")
                st.rerun()
        else:
            st.error("식당 이름을 입력해주세요!")
        
    st.divider()
    
    st.write("📝 **현재 후보 목록** (구글 시트 연동 중)")
    for i, rest in enumerate(restaurants):
        col_info, col_btn = st.columns([4, 1])
        with col_info:
            if rest["type"] == "emoji":
                st.write(f"{i+1}. {rest['content']} {rest['name']}")
            else:
                st.write(f"{i+1}. 🖼️ {rest['name']} (직접 업로드됨)")
        with col_btn:
            if st.button("❌", key=f"del_{i}"):
                # 선택한 식당 데이터를 삭제하고 시트에 덮어쓰기
                updated_df = df.drop(index=i)
                update_sheet(updated_df)
                st.rerun()

st.divider()

# 4. 사다리 애니메이션 시각화 구현
if len(restaurants) >= 2:
    rest_json = json.dumps(restaurants)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ text-align: center; font-family: 'Malgun Gothic', sans-serif; }}
        h3 {{ color: #FF4B4B; margin-bottom: 5px; }}
        .question-mark {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            font-size: 150px; color: rgba(0, 0, 0, 0.05); font-weight: bold; pointer-events: none; z-index: 0;
        }}
        .canvas-container {{ position: relative; display: inline-block; width: 100%; max-width: 800px; }}
        canvas {{ 
            width: 100%; height: auto; background-color: #f9f9f9; 
            border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            cursor: pointer; touch-action: manipulation; position: relative; z-index: 1;
        }}
        .reset-button {{
            display: none; margin-top: 20px; padding: 12px 30px; font-size: 16px; 
            font-weight: bold; background-color: #007BFF; color: white; border: none; 
            border-radius: 8px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
    </style>
    </head>
    <body>
        <h3 id="statusText">👆 출발선 번호를 클릭하세요!</h3>
        <div class="canvas-container">
            <div id="secretMark" class="question-mark">?</div>
            <canvas id="ladderCanvas" width="800" height="500"></canvas>
        </div>
        <div>
            <button id="resetBtn" class="reset-button">🔄 다시 타기 (사다리 재구성)</button>
        </div>
        
        <script>
            // const에서 let으로 변경하여 배열을 덮어쓸 수 있게 만듭니다.
            let restaurants = {rest_json};
            const canvas = document.getElementById('ladderCanvas');
            const ctx = canvas.getContext('2d');
            
            const N = restaurants.length;
            const w = canvas.width;
            const h = canvas.height;
            const padding = 60;
            const topMargin = 80;
            const bottomMargin = 100;
            const colWidth = (w - 2 * padding) / (N - 1);
            const gridRows = 20; 
            const rowHeight = (h - topMargin - bottomMargin) / gridRows;
            
            let rungs = [];
            let customImages = [];
            
            // 💡 [새로 추가된 기능] 배열 안의 순서를 무작위로 뒤섞는 함수
            function shuffleArray(array) {{
                for (let i = array.length - 1; i > 0; i--) {{
                    const j = Math.floor(Math.random() * (i + 1));
                    [array[i], array[j]] = [array[j], array[i]];
                }}
            }}

            // 💡 [새로 추가된 기능] 식당 리스트를 섞고 이미지를 다시 불러오는 함수
            function setupRestaurants() {{
                shuffleArray(restaurants);
                customImages = [];
                restaurants.forEach((r, idx) => {{
                    if (r.type === 'image') {{
                        const img = new Image();
                        img.src = r.content;
                        img.onload = () => {{ drawLadder(); }};
                        customImages[idx] = img;
                    }}
                }});
            }}
            
            function generateRungs() {{
                rungs = [];
                for (let r = 1; r < gridRows; r++) {{
                    for (let c = 0; c < N - 1; c++) {{
                        if (Math.random() > 0.4) {{
                            let hasLeft = rungs.some(rung => rung.row === r && rung.col === c - 1);
                            if (!hasLeft) rungs.push({{ row: r, col: c, y: topMargin + r * rowHeight }});
                        }}
                    }}
                }}
            }}
            
            let isLadderRevealed = false;
            let isAnimating = false;
            
            // 처음 실행될 때 식당 순서를 무작위로 한 번 섞어줍니다.
            setupRestaurants(); 
            generateRungs(); 
            
            function drawLadder() {{
                ctx.clearRect(0, 0, w, h);
                ctx.lineWidth = 4;
                
                ctx.strokeStyle = '#cccccc';
                for (let i = 0; i < N; i++) {{
                    let x = padding + i * colWidth;
                    
                    ctx.beginPath();
                    ctx.moveTo(x, topMargin);
                    ctx.lineTo(x, h - bottomMargin);
                    ctx.stroke();
                    
                    ctx.fillStyle = '#007BFF';
                    ctx.beginPath();
                    ctx.arc(x, topMargin - 20, 18, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 18px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(i + 1, x, topMargin - 20);
                    
                    ctx.fillStyle = '#333333';
                    ctx.textAlign = 'center';
                    
                    if (restaurants[i].type === 'emoji') {{
                        ctx.font = '30px Arial';
                        ctx.fillText(restaurants[i].content, x, h - bottomMargin + 40);
                    }} else if (customImages[i]) {{
                        try {{
                            ctx.drawImage(customImages[i], x - 20, h - bottomMargin + 10, 40, 40);
                        }} catch (e) {{
                            ctx.font = '20px Arial';
                            ctx.fillText('🖼️', x, h - bottomMargin + 40);
                        }}
                    }}
                    
                    ctx.font = 'bold 16px Arial';
                    ctx.fillText(restaurants[i].name, x, h - bottomMargin + 75);
                }}
                
                if (isLadderRevealed) {{
                    ctx.strokeStyle = '#999999';
                    for (let rung of rungs) {{
                        let x1 = padding + rung.col * colWidth;
                        let x2 = padding + (rung.col + 1) * colWidth;
                        ctx.beginPath();
                        ctx.moveTo(x1, rung.y);
                        ctx.lineTo(x2, rung.y);
                        ctx.stroke();
                    }}
                }}
            }}
            
            // 이미지가 없는 이모지 모드일 때를 대비해 초기 그리기를 실행합니다.
            drawLadder(); 
            
            function tracePath(startIndex) {{
                let path = [];
                let currCol = startIndex;
                path.push({{x: padding + currCol * colWidth, y: topMargin}});
                
                rungs.sort((a,b) => a.row - b.row); 
                
                for (let rung of rungs) {{
                    if (rung.col === currCol) {{
                        path.push({{x: padding + currCol * colWidth, y: rung.y}});
                        currCol++;
                        path.push({{x: padding + currCol * colWidth, y: rung.y}});
                    }} else if (rung.col === currCol - 1) {{
                        path.push({{x: padding + currCol * colWidth, y: rung.y}});
                        currCol--;
                        path.push({{x: padding + currCol * colWidth, y: rung.y}});
                    }}
                }}
                path.push({{x: padding + currCol * colWidth, y: h - bottomMargin}});
                return {{ path, endIndex: currCol }};
            }}
            
            canvas.addEventListener('click', (e) => {{
                if (isAnimating) return;
                
                const rect = canvas.getBoundingClientRect();
                const scaleX = canvas.width / rect.width;
                const scaleY = canvas.height / rect.height;
                const clickX = (e.clientX - rect.left) * scaleX;
                const clickY = (e.clientY - rect.top) * scaleY;
                
                for (let i = 0; i < N; i++) {{
                    let nodeX = padding + i * colWidth;
                    let nodeY = topMargin - 20;
                    let dist = Math.sqrt((clickX - nodeX)**2 + (clickY - nodeY)**2);
                    
                    if (dist < 30) {{
                        isLadderRevealed = true;
                        document.getElementById('secretMark').style.display = 'none';
                        document.getElementById('resetBtn').style.display = 'none';
                        startAnimation(i);
                        break;
                    }}
                }}
            }});

            function startAnimation(startIndex) {{
                isAnimating = true;
                document.getElementById('statusText').innerText = "두근두근 사다리 타는 중... 🏃‍♂️💨";
                const {{ path, endIndex }} = tracePath(startIndex);
                
                let pIdx = 0;
                let progress = 0; 
                
                function animate() {{
                    drawLadder(); 
                    
                    ctx.lineWidth = 6;
                    ctx.strokeStyle = '#FF4B4B';
                    ctx.beginPath();
                    ctx.moveTo(path[0].x, path[0].y);
                    for(let i=1; i<=pIdx; i++) {{
                        ctx.lineTo(path[i].x, path[i].y);
                    }}
                    
                    if (pIdx < path.length - 1) {{
                        let startPoint = path[pIdx];
                        let endPoint = path[pIdx+1];
                        let currX = startPoint.x + (endPoint.x - startPoint.x) * progress;
                        let currY = startPoint.y + (endPoint.y - startPoint.y) * progress;
                        ctx.lineTo(currX, currY);
                        ctx.stroke();
                        
                        ctx.fillStyle = '#FF4B4B';
                        ctx.beginPath();
                        ctx.arc(currX, currY, 10, 0, Math.PI*2);
                        ctx.fill();
                        
                        progress += 0.08; 
                        if (progress >= 1) {{
                            progress = 0;
                            pIdx++;
                        }}
                        requestAnimationFrame(animate);
                    }} else {{
                        ctx.stroke(); 
                        let resultName = restaurants[endIndex].name;
                        document.getElementById('statusText').innerHTML = `🎉 당첨: <b>${{resultName}}</b> 🎉`;
                        
                        ctx.fillStyle = 'rgba(255, 75, 75, 0.2)';
                        let finalX = padding + endIndex * colWidth;
                        ctx.fillRect(finalX - 45, h - bottomMargin + 5, 90, 85);
                        
                        isAnimating = false;
                        document.getElementById('resetBtn').style.display = 'inline-block';
                    }}
                }}
                animate();
            }}
            
            document.getElementById('resetBtn').addEventListener('click', () => {{
                if (isAnimating) return;
                isLadderRevealed = false;
                document.getElementById('secretMark').style.display = 'block';
                document.getElementById('statusText').innerText = "👆 출발선 번호를 클릭하세요!";
                document.getElementById('resetBtn').style.display = 'none';
                
                // 💡 [새로 추가된 기능] 다시 타기 버튼을 누를 때마다 식당 순서를 새롭게 섞어줍니다!
                setupRestaurants(); 
                generateRungs();
                drawLadder();
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=660)
    
else:
    st.warning("사다리를 타려면 식당 후보가 최소 2개 이상이어야 합니다. 식당을 추가해주세요!")

st.divider()

# 5. 점심 기록(히스토리) 저장 기능
st.markdown("<h2 style='text-align: center; word-break: keep-all;'>📅 점심 기록 남기기</h2>", unsafe_allow_html=True)

# 기록용 시트 불러오기 (시트 이름: '기록')
try:
    history_df = conn.read(worksheet="기록", ttl=0)
    history_df = history_df.dropna(how="all")
except Exception:
    # 시트가 없거나 비어있을 경우를 대비해 빈 뼈대 만들기
    history_df = pd.DataFrame(columns=["날짜", "식당이름", "메뉴및메모"])

# 💡 [새로 추가된 부분] 데이터의 '행 번호'를 깔끔하게 0, 1, 2... 순으로 다시 정리합니다. (수정/삭제 시 엉뚱한 줄이 지워지는 것을 방지)
history_df = history_df.reset_index(drop=True)

with st.expander("📝 어떤 메뉴를 드셨는지 기록해 보세요!", expanded=False):
    with st.form("history_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # 날짜 선택 (기본값: 오늘 날짜)
            selected_date = st.date_input("날짜 선택")
            
            # 등록된 식당 목록을 가져와서 선택지에 추가
            restaurant_names = [r["name"] for r in restaurants] if restaurants else []
            selected_rest = st.selectbox("어디로 가셨나요?", ["직접 입력..."] + restaurant_names)
            
            # 만약 '직접 입력...'을 선택했다면 텍스트 입력창 띄우기
            if selected_rest == "직접 입력...":
                selected_rest = st.text_input("식당 이름 직접 입력")
        
        with col2:
            # 무엇을 먹었는지, 어땠는지 적는 칸
            memo = st.text_area("무엇을 드셨나요? (메뉴, 평가 등)", height=110)
        
        submit_btn = st.form_submit_button("💾 기록 저장하기", use_container_width=True)
        
        if submit_btn:
            if selected_rest:
                # 새로운 기록을 표(데이터프레임) 형태로 만들기
                new_history = pd.DataFrame([{
                    "날짜": str(selected_date), 
                    "식당이름": selected_rest, 
                    "메뉴및메모": memo
                }])
                # 기존 기록 아래에 새로운 기록 이어 붙이기
                updated_history = pd.concat([history_df, new_history], ignore_index=True)
                # 구글 시트에 덮어쓰기
                conn.update(worksheet="기록", data=updated_history)
                
                st.success("점심 기록이 성공적으로 저장되었습니다!")
                st.rerun() # 새로고침하여 기록 목록 업데이트
            else:
                st.error("식당 이름을 입력하거나 선택해주세요!")

# 💡 [새로 추가된 부분] 저장된 기록을 수정하거나 삭제하는 기능
with st.expander("🛠️ 기록 수정 및 삭제", expanded=False):
    if not history_df.empty:
        # 사용자가 선택하기 쉽도록 목록 만들기 (예: [0] 2026-07-07 - 김밥천국)
        history_list = []
        for i, row in history_df.iterrows():
            history_list.append(f"[{i}] {row['날짜']} - {row['식당이름']}")
        
        selected_history = st.selectbox("수정하거나 삭제할 기록을 선택하세요", history_list)
        
        if selected_history:
            # 선택한 항목에서 '[숫자]' 부분의 숫자(인덱스)만 쏙 뽑아냅니다.
            selected_idx = int(selected_history.split("]")[0][1:])
            selected_row = history_df.loc[selected_idx]
            
            # 기존 내용을 입력칸에 미리 채워 보여주고, 수정할 수 있게 합니다.
            edit_date = st.text_input("날짜 수정", value=selected_row['날짜'])
            edit_rest = st.text_input("식당 이름 수정", value=selected_row['식당이름'])
            # 메모가 비어있을 수 있으므로 안전하게 가져오기 (get 사용)
            edit_memo = st.text_area("메뉴 및 메모 수정", value=str(selected_row.get('메뉴및메모', '')))
            
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("💾 수정 내용 저장", use_container_width=True):
                    # 표(데이터프레임)에서 선택된 행의 데이터만 새로운 내용으로 교체
                    history_df.at[selected_idx, '날짜'] = edit_date
                    history_df.at[selected_idx, '식당이름'] = edit_rest
                    history_df.at[selected_idx, '메뉴및메모'] = edit_memo
                    
                    # 구글 시트 덮어쓰기
                    conn.update(worksheet="기록", data=history_df)
                    st.success("기록이 성공적으로 수정되었습니다!")
                    st.rerun()
            with col_del:
                if st.button("🗑️ 이 기록 삭제", use_container_width=True):
                    # 선택된 행을 표에서 아예 지워버리고 행 번호를 다시 정렬
                    updated_history = history_df.drop(index=selected_idx).reset_index(drop=True)
                    
                    # 구글 시트 덮어쓰기
                    conn.update(worksheet="기록", data=updated_history)
                    st.success("기록이 삭제되었습니다!")
                    st.rerun()
    else:
        st.info("수정하거나 삭제할 기록이 아직 없습니다.")
        
st.divider()

st.write("📖 **이전 점심 기록 모아보기**")
if not history_df.empty:
    # 최신 기록이 위로 오도록 날짜 기준 내림차순 정렬
    sorted_history = history_df.sort_values(by="날짜", ascending=False)
    st.dataframe(sorted_history, use_container_width=True, hide_index=True)
else:
    st.info("아직 저장된 식사 기록이 없습니다. 오늘의 첫 식사를 기록해 보세요!")
