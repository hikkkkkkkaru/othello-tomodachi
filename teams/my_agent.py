import random

from othello.engine import get_legal_moves, apply_move, count_stones, is_game_over

# マスの価値マップ: チームの考えで自由に変えてよい
# 正の値 = 有利なマス、負の値 = 危険なマス
WEIGHT_MAP = [
    [ 50,-30, 30, 20, 20, 30,-30, 50],
    [-30,-50,-20,-20,-20,-20,-50,-30],
    [ 30,-20, 20, 10, 10, 20,-20, 30],
    [ 20,-20, 10, 10, 10, 10,-20, 20],
    [ 20,-20, 10, 10, 10, 10,-20, 20],
    [ 30,-20, 20, 10, 10, 20,-20, 30],
    [-30,-50,-20,-20,-20,-20,-50,-30],
    [ 50,-30, 30, 20, 20, 30,-30, 50],
]


class MyAgent:
    def select_action(self, board: list[list[int]], player: int) -> tuple[int, int]:
        """
        board : 8×8の二重リスト（0=空, 1=黒, -1=白）
        player: 1（黒）または -1（白）
        return: (row, col) — 行・列とも0〜7の座標タプル
        パスはエンジンが処理するため、合法手があるときだけ呼ばれる。
        """
        legal = get_legal_moves(board, player)
        return self.choose(board, player, legal)

    def choose(self, board, player, legal):
        best_score = -999999
        best_move = None
        alpha = -999999
        beta = 999999
        
        # 先読みする手数（4手先まで読みます。もし5秒の制限時間を超える場合は3に減らしてください）
        depth = 4 

        for move in legal:
            after = apply_move(board, player, move)
            # 次は相手のターンなので -player を渡して再帰探索を開始
            score = self.alphabeta(after, -player, depth - 1, alpha, beta, player)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)

        return best_move

    # --- 新しく追加する再帰関数（chooseの下に同じ字下げで配置） ---
    def alphabeta(self, board, current_player, depth, alpha, beta, my_color):
        # 1. 終局判定（勝敗が確定している場合は、石の差を最優先して大きな点数をつける）
        if is_game_over(board):
            my_stones = count_stones(board, my_color)
            opp_stones = count_stones(board, -my_color)
            if my_stones > opp_stones:
                return 10000 + my_stones  # 勝ち確
            elif my_stones < opp_stones:
                return -10000 - opp_stones # 負け確
            else:
                return 0

        # 2. 指定した深さ(depth)まで読んだら、その時点での盤面を評価して返す
        if depth == 0:
            score = 0
            for r in range(8):
                for c in range(8):
                    if board[r][c] == my_color:
                        score += WEIGHT_MAP[r][c]
                    elif board[r][c] == -my_color:
                        score -= WEIGHT_MAP[r][c]
            return score

        legal_moves = get_legal_moves(board, current_player)
        
        # 3. パスの場合（手番を変えて深さはそのままで探索を続ける）
        if not legal_moves:
            return self.alphabeta(board, -current_player, depth, alpha, beta, my_color)

        # 4. ミニマックス探索 ＋ α-β枝刈り
        if current_player == my_color:
            # 【自分のターン】スコアを最大化（一番良い手）を選びたい
            max_eval = -999999
            for move in legal_moves:
                after = apply_move(board, current_player, move)
                eval = self.alphabeta(after, -current_player, depth - 1, alpha, beta, my_color)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break # βカット（これ以上調べても相手に防がれるのでスキップ）
            return max_eval
        else:
            # 【相手のターン】自分にとって最悪（スコア最小）の手を選んでくると想定
            min_eval = 999999
            for move in legal_moves:
                after = apply_move(board, current_player, move)
                eval = self.alphabeta(after, -current_player, depth - 1, alpha, beta, my_color)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break # αカット（これ以上調べても無駄なのでスキップ）
            return min_eval