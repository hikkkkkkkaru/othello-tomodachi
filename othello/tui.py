"""ターミナル表示: rich ダッシュボード。"""
from __future__ import annotations

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from othello.engine import BLACK, WHITE, count_stones, get_legal_moves

LINE = "#2f6b34"
DOT = "#4d8a52"
HINT = "#ffce73"
MUTED = "#8fae94"
GREEN = "#62f5b5"
CYAN = "#8ad8e9"


def _board_text(board, player: int | None, show_hints: bool) -> Text:
    legal = set(get_legal_moves(board, player)) if show_hints and player is not None else set()
    text = Text()
    text.append("    " + " ".join("abcdefgh") + " \n", style=MUTED)
    for r in range(8):
        text.append(f" {r + 1}  ", style=MUTED)
        for c in range(8):
            v = board[r][c]
            if v == BLACK:
                text.append("● ", style="bold white")
            elif v == WHITE:
                text.append("○ ", style="bold white")
            elif (r, c) in legal:
                text.append("· ", style=HINT)
            else:
                text.append("· ", style=DOT)
        text.append("\n")
    return text


def _bar(value: float, length: int = 24, color: str = GREEN) -> Text:
    filled = round(max(0.0, min(1.0, value)) * length)
    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * (length - filled), style=MUTED)
    return bar


def render(
    board,
    player: int | None,
    name_b: str,
    name_w: str,
    *,
    last_move: str | None = None,
    passed: str | None = None,
    result: str | None = None,
    show_hints: bool = False,
) -> Panel:
    b, w = count_stones(board, BLACK), count_stones(board, WHITE)
    total = max(b + w, 1)

    body = Group(
        _board_text(board, player, show_hints),
        Text(),
        Text.assemble(("● ", "bold white"), (f"{name_b}  {b:2d}", GREEN if player == BLACK else MUTED)),
        _bar(b / total, color=GREEN),
        Text.assemble(("○ ", "bold white"), (f"{name_w}  {w:2d}", CYAN if player == WHITE else MUTED)),
        _bar(w / total, color=CYAN),
        Text(),
        Text(result or passed or last_move or "", style="bold " + GREEN if result else MUTED),
    )

    if result:
        subtitle = result
    elif player == BLACK:
        subtitle = f"手番: ● {name_b}"
    elif player == WHITE:
        subtitle = f"手番: ○ {name_w}"
    else:
        subtitle = ""

    return Panel(body, title="[bold]OTHELLO[/bold]", subtitle=subtitle, border_style=LINE, padding=(1, 2))


class TUI:
    """`with TUI() as tui: tui.update(board, player, ...)` でライブ更新する。"""

    def __init__(self) -> None:
        self._live = Live(console=Console(), refresh_per_second=8, transient=False)

    def __enter__(self) -> "TUI":
        self._live.__enter__()
        return self

    def __exit__(self, *exc) -> None:
        self._live.__exit__(*exc)

    def update(self, *args, **kwargs) -> None:
        self._live.update(render(*args, **kwargs))
