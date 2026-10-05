import streamlit as st
import time
from othello.engine import initial_board, get_legal_moves, apply_move, count_stones, is_game_over
from teams.my_agent import MyAgent, WEIGHT_MAP

st.set_page_config(page_title="オセロAI対戦", layout="centered")

# --- 画面の見栄えを良くする設定 ---
st.markdown("""
<style>
div[data-testid="stButton"] > button {
    background-color: #008000 !important;
    border: 1px solid #005000 !important;
    color: white !important;
    font-size: 28px !important;
    height: 60px !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

st.title("⚫ オセロ対戦 vs 自作AI ⚪")

# 4つのレベルを選択可能にする
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
                if st.button("➕", key=f"btn_{r}_{c}"):
                    st.session_state.board = apply_move(board, 1, (r, c))
                    st.session_state.current_player = -1
                    st.rerun()
            else:
                st.button(" ", key=f"E_{r}_{c}", disabled=True)

# --- AI（白番）のターン処理と全レベル分岐 ---
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
                # 簡略化したスコア計算
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
            # 超上級：提出用の my_agent.py（α-β探索）を呼び出す
            best_move = st.session_state.ai.choose(board, -1, legal_moves)

        st.session_state.board = apply_move(board, -1, best_move)
        st.session_state.current_player = 1
        st.rerun()
