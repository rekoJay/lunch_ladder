import streamlit as st
import streamlit.components.v1 as components
import json

# 1. 페이지 기본 설정
st.set_page_config(page_title="점심 리얼 사다리", page_icon="🪜", layout="centered")

st.title("🪜 리얼 점심 사다리타기")
st.write("식당 이름과 이모지를 추가하고, 출발선 번호를 눌러 사다리를 타보세요!")

# 2. 이모지 후보 리스트
EMOJI_LIST = ["🍔", "🍣", "🍜", "🍕", "🥩", "🥗", "🌮", "🍱", "🍛", "🍝", "🥪", "🥘", "🍚", "🍲"]

# 3. 데이터 저장 공간 설정
if 'restaurants' not in st.session_state:
    st.session_state.restaurants = [
        {"name": "버거킹", "emoji": "🍔"},
        {"name": "마라탕", "emoji": "🍜"},
        {"name": "초밥", "emoji": "🍣"}
    ]

# 식당 추가 함수
def add_restaurant(name, emoji):
    if name:
        st.session_state.restaurants.append({"name": name, "emoji": emoji})

# 식당 삭제 함수
def remove_restaurant(index):
    st.session_state.restaurants.pop(index)

# 4. 사용자 인터페이스 (식당 추가 및 삭제)
with st.expander("🛠️ 식당 후보 관리 (여기를 눌러 열고 닫으세요)", expanded=True):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_name = st.text_input("식당 이름 (예: 김밥천국)")
    with col2:
        new_emoji = st.selectbox("어울리는 이모지", EMOJI_LIST)
        
    if st.button("➕ 식당 추가하기", use_container_width=True):
        add_restaurant(new_name, new_emoji)
        st.rerun()
        
    st.divider()
    
    st.write("📝 **현재 후보 목록** (최대 8~10개 권장)")
    for i, rest in enumerate(st.session_state.restaurants):
        col_name, col_btn = st.columns([4, 1])
        with col_name:
            st.write(f"{i+1}. {rest['emoji']} {rest['name']}")
        with col_btn:
            if st.button("❌", key=f"del_{i}"):
                remove_restaurant(i)
                st.rerun()

st.divider()

# 5. 사다리 애니메이션 구현
if len(st.session_state.restaurants) >= 2:
    
    rest_json = json.dumps(st.session_state.restaurants)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ text-align: center; font-family: 'Malgun Gothic', sans-serif; }}
        h3 {{ color: #FF4B4B; margin-bottom: 5px; }}
        /* 중앙의 물음표(블라인드) 효과를 위한 CSS 추가 */
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
    </style>
    </head>
    <body>
        <h3 id="statusText">👆 출발선 번호를 클릭하세요!</h3>
        
        <div class="canvas-container">
            <div id="secretMark" class="question-mark">?</div>
            <canvas id="ladderCanvas" width="800" height="500"></canvas>
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
            
            // [수정] 가로줄(사다리 다리) 촘촘하게 만들기
            let rungs = [];
            const gridRows = 20; // 10개에서 20개로 두 배 증가 (복잡도 상승)
            const rowHeight = (h - topMargin - bottomMargin) / gridRows;
            
            for (let r = 1; r < gridRows; r++) {{
                for (let c = 0; c < N - 1; c++) {{
                    // [수정] 60% 확률로 가로줄 생성 (기존보다 선이 그어질 확률 상승)
                    if (Math.random() > 0.4) {{
                        let hasLeft = rungs.some(rung => rung.row === r && rung.col === c - 1);
                        if (!hasLeft) {{
                            rungs.push({{ row: r, col: c, y: topMargin + r * rowHeight }});
                        }}
                    }}
                }}
            }}
            
            // [수정] 사다리 가리기 상태 변수 추가
            let isLadderRevealed = false;
            
            function drawLadder() {{
                ctx.clearRect(0, 0, w, h);
                ctx.lineWidth = 4;
                
                // 1. 세로줄 및 위아래 버튼/텍스트 그리기 (항상 보임)
                ctx.strokeStyle = '#cccccc';
                for (let i = 0; i < N; i++) {{
                    let x = padding + i * colWidth;
                    
                    ctx.beginPath();
                    ctx.moveTo(x, topMargin);
                    ctx.lineTo(x, h - bottomMargin);
                    ctx.stroke();
                    
                    // 출발 버튼
                    ctx.fillStyle = '#007BFF';
                    ctx.beginPath();
                    ctx.arc(x, topMargin - 20, 18, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.fillStyle = 'white';
                    ctx.font = 'bold 18px Arial';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(i + 1, x, topMargin - 20);
                    
                    // 아래쪽 식당 결과
                    ctx.fillStyle = '#333333';
                    ctx.font = '30px Arial';
                    ctx.fillText(restaurants[i].emoji, x, h - bottomMargin + 40);
                    ctx.font = 'bold 16px Arial';
                    ctx.fillText(restaurants[i].name, x, h - bottomMargin + 70);
                }}
                
                // 2. [수정] 사다리 가로줄은 버튼을 눌렀을 때(isLadderRevealed가 true일 때)만 그리기
                if (isLadderRevealed) {{
                    ctx.strokeStyle = '#999999'; // 가로줄은 조금 더 진하게
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
            
            let isAnimating = false;
            
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
                        // [수정] 번호를 누르면 숨겨둔 가로줄을 나타나게 하고 배경의 큰 물음표를 숨김
                        isLadderRevealed = true;
                        document.getElementById('secretMark').style.display = 'none';
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
                        let resultEmoji = restaurants[endIndex].emoji;
                        
                        document.getElementById('statusText').innerHTML = `🎉 당첨: <b>${{resultName}}</b> ${{resultEmoji}} 🎉`;
                        
                        ctx.fillStyle = 'rgba(255, 75, 75, 0.2)';
                        let finalX = padding + endIndex * colWidth;
                        ctx.fillRect(finalX - 40, h - bottomMargin + 10, 80, 80);
                        
                        isAnimating = false;
                    }}
                }}
                animate();
            }}
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=650)
    
else:
    st.warning("사다리를 타려면 식당 후보가 최소 2개 이상이어야 합니다. 식당을 추가해주세요!")
