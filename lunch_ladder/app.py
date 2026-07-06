import streamlit as st
import streamlit.components.v1 as components
import json
import base64

# 1. 페이지 기본 설정 (이름 변경)
st.set_page_config(page_title="점심 사다리타기", page_icon="🪜", layout="centered")

st.title("🪜 점심 사다리타기")
st.write("식당 이름과 아이콘을 자유롭게 설정하고, 출발선 번호를 눌러 사다리를 타보세요!")

# 2. 기본 제공 이모지 목록
EMOJI_LIST = ["🍔", "🍣", "🍜", "🍕", "🥩", "🥗", "🌮", "🍱", "🍛", "🍝", "🥪", "🥘", "🍚", "🍲"]

# 3. 데이터 저장 공간 설정 (초기 기본값 설정)
if 'restaurants' not in st.session_state:
    st.session_state.restaurants = [
        {"name": "버거킹", "type": "emoji", "content": "🍔"},
        {"name": "마라탕", "type": "emoji", "content": "🍜"},
        {"name": "초밥", "type": "emoji", "content": "🍣"}
    ]

# 식당 삭제 함수
def remove_restaurant(index):
    st.session_state.restaurants.pop(index)

# 4. 사용자 인터페이스 (식당 추가 및 삭제)
with st.expander("🛠️ 식당 후보 관리 (여기를 눌러 열고 닫으세요)", expanded=True):
    new_name = st.text_input("식당 이름 (예: 김밥천국)")
    
    # 이모지 선택 또는 이미지 업로드 방식 선택 토글
    icon_type = st.radio("아이콘 추가 방식", ["기본 이모지 선택", "나만의 이미지 업로드"], horizontal=True)
    
    icon_content = None
    item_type = "emoji"
    
    if icon_type == "기본 이모지 선택":
        icon_content = st.selectbox("어울리는 이모지", EMOJI_LIST)
        item_type = "emoji"
    else:
        uploaded_file = st.file_uploader("식당 이미지 파일 선택 (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            # 업로드된 이미지를 웹 브라우저가 읽을 수 있도록 Base64 코드로 변환
            bytes_data = uploaded_file.read()
            b64_str = base64.b64encode(bytes_data).decode()
            icon_content = f"data:image/{uploaded_file.type.split('/')[-1]};base64,{b64_str}"
            item_type = "image"
            
    if st.button("➕ 식당 추가하기", use_container_width=True):
        if new_name:
            if item_type == "image" and icon_content is None:
                st.error("이미지 파일을 업로드해주세요!")
            else:
                st.session_state.restaurants.append({"name": new_name, "type": item_type, "content": icon_content})
                st.rerun()
        else:
            st.error("식당 이름을 입력해주세요!")
        
    st.divider()
    
    # 현재 목록 보여주고 삭제하기
    st.write("📝 **현재 후보 목록** (최대 8~10개 권장)")
    for i, rest in enumerate(st.session_state.restaurants):
        col_info, col_btn = st.columns([4, 1])
        with col_info:
            # 이모지인지 업로드된 이미지인지에 따라 다르게 표시
            if rest["type"] == "emoji":
                st.write(f"{i+1}. {rest['content']} {rest['name']}")
            else:
                st.write(f"{i+1}. 🖼️ {rest['name']} (직접 업로드됨)")
        with col_btn:
            if st.button("❌", key=f"del_{i}"):
                remove_restaurant(i)
                st.rerun()

st.divider()

# 5. 사다리 애니메이션 및 시각화 구현
if len(st.session_state.restaurants) >= 2:
    
    # 파이썬 데이터를 자바스크립트용 JSON으로 변경
    rest_json = json.dumps(st.session_state.restaurants)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ text-align: center; font-family: 'Malgun Gothic', sans-serif; }}
        h3 {{ color: #FF4B4B; margin-bottom: 5px; }}
        .question-mark {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 150px;
            color: rgba(0, 0, 0, 0.05);
            font-weight: bold;
            pointer-events: none;
            z-index: 0;
        }}
        .canvas-container {{ position: relative; display: inline-block; width: 100%; max-width: 800px; }}
        canvas {{ 
            width: 100%; height: auto; 
            background-color: #f9f9f9; 
            border-radius: 15px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            cursor: pointer;
            touch-action: manipulation;
            position: relative;
            z-index: 1;
        }}
        /* 다시 타기 버튼 스타일 */
        .reset-button {{
            display: none; 
            margin-top: 20px; 
            padding: 12px 30px; 
            font-size: 16px; 
            font-weight: bold; 
            background-color: #007BFF; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: background-color 0.2s;
        }}
        .reset-button:hover {{
            background-color: #0056b3;
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
            const restaurants = {rest_json};
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
            
            // 유저가 직접 업로드한 이미지들을 미리 로딩해두는 로직
            restaurants.forEach((r, idx) => {{
                if (r.type === 'image') {{
                    const img = new Image();
                    img.src = r.content;
                    img.onload = () => {{
                        drawLadder(); // 이미지가 로드 완료되면 화면을 다시 그림
                    }};
                    customImages[idx] = img;
                }}
            }});
            
            // 사다리 가로줄 랜덤 생성 함수
            function generateRungs() {{
                rungs = [];
                for (let r = 1; r < gridRows; r++) {{
                    for (let c = 0; c < N - 1; c++) {{
                        if (Math.random() > 0.4) {{
                            let hasLeft = rungs.some(rung => rung.row === r && rung.col === c - 1);
                            if (!hasLeft) {{
                                rungs.push({{ row: r, col: c, y: topMargin + r * rowHeight }});
                            }}
                        }}
                    }}
                }}
            }}
            
            let isLadderRevealed = false;
            let isAnimating = false;
            
            generateRungs(); // 최초 선 생성
            
            function drawLadder() {{
                ctx.clearRect(0, 0, w, h);
                ctx.lineWidth = 4;
                
                // 1. 세로줄 및 버튼 그리기
                ctx.strokeStyle = '#cccccc';
                for (let i = 0; i < N; i++) {{
                    let x = padding + i * colWidth;
                    
                    ctx.beginPath();
                    ctx.moveTo(x, topMargin);
                    ctx.lineTo(x, h - bottomMargin);
                    ctx.stroke();
                    
                    // 출발 번호 버튼
                    ctx.fillStyle = '#007BFF';
                    ctx.beginPath();
                    ctx.arc(x, topMargin - 20, 18, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 18px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(i + 1, x, topMargin - 20);
                    
                    // 아래쪽 결과 아이콘 및 이름 그리기
                    ctx.fillStyle = '#333333';
                    ctx.textAlign = 'center';
                    
                    if (restaurants[i].type === 'emoji') {{
                        ctx.font = '30px Arial';
                        ctx.fillText(restaurants[i].content, x, h - bottomMargin + 40);
                    }} else if (customImages[i]) {{
                        // 업로드된 이미지를 40x40 크기로 사다리 밑에 중앙 정렬하여 그리기
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
                
                // 2. 가로줄 가려져 있다가 번호 누르면 보이게 처리
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
                        document.getElementById('resetBtn').style.display = 'none'; // 시작하면 초기화 버튼 숨김
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
                        document.getElementById('resetBtn').style.display = 'inline-block'; // 완료 후 초기화 버튼 노출
                    }}
                }}
                animate();
            }}
            
            // 새로고침(다시 타기) 버튼 클릭 시 작동하는 로직
            document.getElementById('resetBtn').addEventListener('click', () => {{
                if (isAnimating) return;
                isLadderRevealed = false;
                document.getElementById('secretMark').style.display = 'block';
                document.getElementById('statusText').innerText = "👆 출발선 번호를 클릭하세요!";
                document.getElementById('resetBtn').style.display = 'none';
                generateRungs(); // 가로줄을 무작위로 새로 만듦
                drawLadder(); // 화면 리셋
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=660)
    
else:
    st.warning("사다리를 타려면 식당 후보가 최소 2개 이상이어야 합니다. 식당을 추가해주세요!")
