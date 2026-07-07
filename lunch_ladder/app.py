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
