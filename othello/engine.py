
EMPTY, BLACK, WHITE = 0, 1, -1
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
MOVE_TIMEOUT = 5.0  # select_action のタイムアウト（秒）


def initial_board() -> list[list[int]]:
    board = [[EMPTY] * 8 for _ in range(8)]
    board[3][3] = board[4][4] = WHITE
    board[3][4] = board[4][3] = BLACK
    return board


def get_flips(board: list[list[int]], player: int, row: int, col: int) -> list[tuple[int, int]]:
    if board[row][col] != EMPTY:
        return []
    opponent = -player
    flips = []
    for dr, dc in DIRECTIONS:
        r, c = row + dr, col + dc
        line = []
        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent:
            line.append((r, c))
            r += dr
            c += dc
        if line and 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player:
            flips.extend(line)
    return flips


def get_legal_moves(board: list[list[int]], player: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(8) for c in range(8) if get_flips(board, player, r, c)]


def apply_move(board: list[list[int]], player: int, move: tuple[int, int]) -> list[list[int]]:
    r, c = move
    flips = get_flips(board, player, r, c)
    new_board = [row[:] for row in board]
    new_board[r][c] = player
    for fr, fc in flips:
        new_board[fr][fc] = player
    return new_board


def count_stones(board: list[list[int]], player: int) -> int:
    return sum(board[r][c] == player for r in range(8) for c in range(8))


def is_game_over(board: list[list[int]]) -> bool:
    return not get_legal_moves(board, BLACK) and not get_legal_moves(board, WHITE)


def _safe_move(agent, board: list[list[int]], player: int, legal: list) -> tuple[int, int]:
    """実装ミスは例外で通知する。時間制限は ProcessAgent が担当する。"""
    move = agent.select_action(board, player)
    if (not isinstance(move, tuple) or len(move) != 2
            or any(type(value) is not int for value in move) or move not in legal):
        raise ValueError(f"{type(agent).__name__}: 不正な手 {move!r}。合法手: {legal}")
    return move


def play_game(agent_black, agent_white) -> int:
    """1試合実行。戻り値: 1=黒勝ち, -1=白勝ち, 0=引き分け"""
    board = initial_board()
    player = BLACK
    agents = {BLACK: agent_black, WHITE: agent_white}

    while True:
        legal = get_legal_moves(board, player)
        if not legal:
            player = -player
            if not get_legal_moves(board, player):
                break
            continue

        move = _safe_move(agents[player], [row[:] for row in board], player, legal)
        board = apply_move(board, player, move)
        player = -player

    b, w = count_stones(board, BLACK), count_stones(board, WHITE)
    return BLACK if b > w else WHITE if w > b else 0


def print_board(board: list[list[int]]) -> None:
    sym = {EMPTY: ".", BLACK: "●", WHITE: "○"}
    print("  a b c d e f g h")
    for r in range(8):
        print(f"{r + 1} " + " ".join(sym[board[r][c]] for c in range(8)))
    print(f"● {count_stones(board, BLACK)}  ○ {count_stones(board, WHITE)}")
