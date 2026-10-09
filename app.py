import streamlit as st
import time
from othello.engine import initial_board, get_legal_moves, apply_move, count_stones, is_game_over
from teams.my_agent import MyAgent, WEIGHT_MAP

st.set_page_config(page_title="オセロAI対戦", layout="centered")

# --- 🎯ここが新しいデザイン（CSS）の設定です🎯 ---
st.markdown("""
<style>
/* 1. マス目同士の隙間を消して盤面を密着させる */
[data-testid="column"] {
    padding: 0 !important;
    min-width: 0 !important;
}
[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}

/* 2. マス目（ボタン）を本物のフェルトマット風に */
div[data-testid="stButton"] > button {
    background-color: #0b5e2a !important; /* 深みのあるマットな緑 */
    border: 1px solid #000000 !important; /* マスの黒い枠線 */
    border-radius: 0px !important;        /* ボタンの丸みを完全に消して四角にする */
    height: 60px !important;              /* マスの高さを固定 */
    width: 100% !important;               /* 幅を最大に */
    padding: 0 !important;
    box-shadow: inset 0px 0px 10px rgba(0,0,0,0.5) !important; /* 内側に影を入れて質感を出す */
    transition: all 0.2s ease;
}

/* 3. マウスを乗せた時のハイライト（打てる場所が光る） */
div[data-testid="stButton"] > button:hover {
    background-color: #168c41 !important;
    border: 1px solid #ffeb3b !important; /* 枠を黄色く光らせる */
    z-index: 1;
}

/* 4. コマ（⚫⚪）に影をつけて立体的に見せる */
div[data-testid="stButton"] > button p {
    font-size: 42px !important;           /* コマをギリギリまで大きく */
    margin: 0 !important;
    text-shadow: 2px 4px 5px rgba(0,0,0,0.7); /* コマの下に影を落として浮かせる */
}
</style>
""", unsafe_allow_html=True)
# ------------------------------------------------

st.title("⚫ オセロ対戦 vs 自作AI ⚪")

level = st.selectbox("AIの強さを選んでください", [
    "初級 (ステップ1: マスの点数だけで選ぶ)",
    "中級 (ステップ2: ひっくり返した後の盤面を見る)",
    "上級 (ステップ3: 相手の反撃まで読む)",
    "超上級 (発展: α-β探索で4手先まで読む)"
])

if "board" not in st.session_state:
    st.session_state.board = initial_board()
    st.session_state.current_player = 1
    st.session_state.ai = MyAgent()

board = st.session_state.board
player = st.session_state.current_player

black_stones = count_stones(board, 1)
white_stones = count_stones(board, -1)
st.subheader(f"黒(あなた): {black_stones}  vs  白(AI): {white_stones}")

if is_game_over(board):
    st.success("ゲーム終了！")
    if black_stones > white_stones:
        st.balloons()
        st.write("🎉 あなたの勝ちです！")
    elif white_stones > black_stones:
        st.write("💀 AIの勝ちです！")
    else:
        st.write("引き分けです。")
        
    if st.button("もう一度遊ぶ"):
        st.session_state.clear()
        st.rerun()
    st.stop()

legal_moves = get_legal_moves(board, player)
if not legal_moves:
    st.warning("打てる場所がありません。パスします。")
    time.sleep(1.5)
    st.session_state.current_player *= -1
    st.rerun()

st.write("---")

# 盤面の描画
for r in range(8):
    cols = st.columns(8)
    for c in range(8):
        piece = board[r][c]
        with cols[c]:
            if piece == 1:
                st.button("⚫", key=f"B_{r}_{c}", disabled=True)
            elif piece == -1:
                st.button("⚪", key=f"W_{r}_{c}", disabled=True)
            elif player == 1 and (r, c) in legal_moves:
                # ➕マークだとダサいので、控えめな「・」に変更
                if st.button("・", key=f"btn_{r}_{c}"):
                    st.session_state.board = apply_move(board, 1, (r, c))
                    st.session_state.current_player = -1
                    st.rerun()
            else:
                # 何もないマス
                st.button(" ", key=f"E_{r}_{c}", disabled=True)

# --- AI（白番）のターン処理 ---
if player == -1:
    with st.spinner("AIが考え中..."):
        time.sleep(0.5)
        best_move = None
        
        if "初級" in level:
            best_score = -99999
            for move in legal_moves:
                if WEIGHT_MAP[move[0]][move[1]] > best_score:
                    best_score = WEIGHT_MAP[move[0]][move[1]]
                    best_move = move
                    
        elif "中級" in level:
            best_score = -99999
            for move in legal_moves:
                after = apply_move(board, -1, move)
                score = sum(WEIGHT_MAP[r][c] for r in range(8) for c in range(8) if after[r][c] == -1) - sum(WEIGHT_MAP[r][c] for r in range(8) for c in range(8) if after[r][c] == 1)
                if score > best_score:
                    best_score = score
                    best_move = move
                    
        elif "上級" in level:
            best_score = -99999
            for move in legal_moves:
                after1 = apply_move(board, -1, move)
                opp_legal = get_legal_moves(after1, 1)
                worst = 99999
                if not opp_legal:
                    worst = sum(WEIGHT_MAP[r][c] for r in range(8) for c in range(8) if after1[r][c] == -1) - sum(WEIGHT_MAP[r][c] for r in range(8) for c in range(8) if after1[r][c] == 1)
                else:
                    for opp_move in opp_legal:
                        after2 = apply_move(after1, 1, opp_move)
                        score = sum(WEIGHT_MAP[r][c] for r in range(8) for c in range(8) if after2[r][c] == -1) - sum(WEIGHT_MAP[r][c] for r in range(8) for c in range(8) if after2[r][c] == 1)
                        if score < worst: 
                            worst = score
                if worst > best_score:
                    best_score = worst
                    best_move = move
                    
        else:
            best_move = st.session_state.ai.choose(board, -1, legal_moves)

        st.session_state.board = apply_move(board, -1, best_move)
        st.session_state.current_player = 1
        st.rerun()
