from typing import Literal, TypedDict

import chess

from src.eval import evaluate
from src.phase import get_game_phase
from src.scoring import score_move
from src.zobrist import init_zobrist, zobrist_hash

# =========================
# CONSTANTS
# =========================
CHECKMATE_SCORE = 100000
INF = 10**9

MAX_DEPTH = 64
MAX_Q_DEPTH = 6


# =========================
# TRANSPOSITION TABLE
# =========================
class TranspositionTableItem(TypedDict):
    depth: int
    score: int
    flag: Literal["EXACT", "LOWER", "UPPER"]
    best_move: chess.Move | None


# =========================
# GLOBALS
# =========================
zobrist_tables = init_zobrist()

tt: dict[int, TranspositionTableItem] = {}

killer_moves: list[list[chess.Move | None]] = [[None, None] for _ in range(MAX_DEPTH)]

history = [[0 for _ in range(64)] for _ in range(64)]

cache_hits = 0


# =========================
# ENTRYPOINT
# =========================
def find_best_move(board: chess.Board, depth: int):
    global cache_hits, killer_moves, history

    cache_hits = 0
    tt.clear()

    killer_moves = [[None, None] for _ in range(MAX_DEPTH)]
    history = [[0 for _ in range(64)] for _ in range(64)]

    best_move = None
    best_score = -INF

    # iterative deepening
    for d in range(1, depth + 1):
        best_score, best_move = __search_root(
            board,
            d,
            best_move,
        )

    print("⚡ Cache hits:", cache_hits)

    return best_score, best_move


# =========================
# ROOT SEARCH
# =========================
def __search_root(
    board: chess.Board,
    depth: int,
    prev_best_move: chess.Move | None = None,
):
    alpha = -INF
    beta = INF

    best_score = -INF
    best_move = None

    moves = list(board.legal_moves)

    sorted_moves = sorted(
        moves,
        key=lambda move: score_move(
            board,
            killer_moves,
            history,
            move,
            0,
        ),
        reverse=True,
    )

    # iterative deepening PV move first
    if prev_best_move in sorted_moves:
        sorted_moves.remove(prev_best_move)
        sorted_moves.insert(0, prev_best_move)

    for move_index, move in enumerate(sorted_moves):

        board.push(move)

        # PVS
        if move_index == 0:
            score = -__search(
                board,
                depth - 1,
                1,
                -beta,
                -alpha,
            )
        else:
            # null-window search
            score = -__search(
                board,
                depth - 1,
                1,
                -alpha - 1,
                -alpha,
            )

            # re-search if promising
            if alpha < score < beta:
                score = -__search(
                    board,
                    depth - 1,
                    1,
                    -beta,
                    -alpha,
                )

        board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

    return best_score, best_move


# =========================
# MAIN SEARCH
# =========================
def __search(
    board: chess.Board,
    depth: int,
    ply: int,
    alpha: int = -INF,
    beta: int = INF,
):
    global cache_hits

    original_alpha = alpha

    # =========================
    # TT LOOKUP
    # =========================
    h = zobrist_hash(board, zobrist_tables)

    if h in tt and tt[h]["depth"] >= depth:
        entry = tt[h]

        cache_hits += 1

        if entry["flag"] == "EXACT":
            return entry["score"]

        elif entry["flag"] == "LOWER":
            alpha = max(alpha, entry["score"])

        elif entry["flag"] == "UPPER":
            beta = min(beta, entry["score"])

        if alpha >= beta:
            return entry["score"]

    # =========================
    # TERMINAL STATES
    # =========================
    if board.is_checkmate():
        return -CHECKMATE_SCORE + ply

    if (
        board.is_stalemate()
        or board.is_repetition()
        or board.is_insufficient_material()
    ):
        return 0

    # =========================
    # QUIESCENCE
    # =========================
    if depth <= 0:
        return __quiescence(board, alpha, beta, ply)

    # =========================
    # NULL MOVE PRUNING
    # =========================
    phase = get_game_phase(board)

    has_non_pawn_material = (
        len(board.pieces(chess.QUEEN, board.turn)) > 0
        or len(board.pieces(chess.ROOK, board.turn)) > 0
        or len(board.pieces(chess.BISHOP, board.turn)) > 1
        or len(board.pieces(chess.KNIGHT, board.turn)) > 1
    )

    allow_null = (
        depth >= 3 and phase > 6 and has_non_pawn_material and not board.is_check()
    )

    if allow_null:

        R = 2 + (phase // 12)

        reduced_depth = max(0, depth - 1 - R)

        board.push(chess.Move.null())

        score = -__search(
            board,
            reduced_depth,
            ply + 1,
            -beta,
            -beta + 1,
        )

        board.pop()

        if score >= beta:
            return beta

    # =========================
    # MOVE ORDERING
    # =========================
    moves = list(board.legal_moves)

    tt_move = None

    if h in tt:
        tt_move = tt[h].get("best_move")

    sorted_moves = sorted(
        moves,
        key=lambda move: (
            move == tt_move,
            score_move(
                board,
                killer_moves,
                history,
                move,
                ply,
            ),
        ),
        reverse=True,
    )

    # =========================
    # SEARCH LOOP
    # =========================
    best_score = -INF
    best_move = None

    for move_index, move in enumerate(sorted_moves):

        is_capture = board.is_capture(move)
        gives_check = board.gives_check(move)

        is_quiet = not is_capture and not gives_check

        extension = 1 if gives_check else 0

        reduction = 0

        # LMR
        if depth >= 3 and move_index >= 4 and is_quiet:
            reduction = 1

        board.push(move)

        # =========================
        # PRINCIPAL VARIATION SEARCH
        # =========================

        new_depth = depth - 1 + extension

        if move_index == 0:

            score = -__search(
                board,
                new_depth,
                ply + 1,
                -beta,
                -alpha,
            )

        else:

            # reduced/null-window search first
            score = -__search(
                board,
                new_depth - reduction,
                ply + 1,
                -alpha - 1,
                -alpha,
            )

            # failed high -> full re-search
            if score > alpha:

                score = -__search(
                    board,
                    new_depth,
                    ply + 1,
                    -beta,
                    -alpha,
                )

        board.pop()

        # =========================
        # BEST MOVE UPDATE
        # =========================
        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        # =========================
        # BETA CUTOFF
        # =========================
        if alpha >= beta:

            # killer moves
            if is_quiet:

                if killer_moves[ply][0] != move:
                    killer_moves[ply][1] = killer_moves[ply][0]
                    killer_moves[ply][0] = move

                history[move.from_square][move.to_square] += depth * depth

            break

    # =========================
    # TT STORE
    # =========================
    if best_score <= original_alpha:
        flag: Literal["EXACT", "LOWER", "UPPER"] = "UPPER"

    elif best_score >= beta:
        flag = "LOWER"

    else:
        flag = "EXACT"

    tt[h] = {
        "score": best_score,
        "depth": depth,
        "flag": flag,
        "best_move": best_move,
    }

    return best_score


# =========================
# QUIESCENCE SEARCH
# =========================
def __quiescence(
    board: chess.Board,
    alpha: int = -INF,
    beta: int = INF,
    ply: int = 0,
):
    if ply >= MAX_Q_DEPTH:
        return evaluate(board)

    stand_pat = evaluate(board)

    if stand_pat >= beta:
        return beta

    alpha = max(alpha, stand_pat)

    captures = list(board.generate_legal_captures())

    captures = sorted(
        captures,
        key=lambda move: board.is_capture(move),
        reverse=True,
    )

    for move in captures:

        board.push(move)

        score = -__quiescence(
            board,
            -beta,
            -alpha,
            ply + 1,
        )

        board.pop()

        if score >= beta:
            return beta

        alpha = max(alpha, score)

    return alpha
