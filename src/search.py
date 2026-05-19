import time
import chess

from typing import Literal, TypedDict
from src.zobrist import init_zobrist, zobrist_hash

from src.scoring import evaluate
from src.config import EngineConfig

INF = 10**9
MATE = 100000

MAX_PLY = 128

nodes = 0

killer_moves = [[None, None] for _ in range(MAX_PLY)]
history = [[0 for _ in range(64)] for _ in range(64)]


# =========================================================
# TT
# =========================================================


class TTEntry(TypedDict):
    depth: int
    score: int
    flag: Literal["EXACT", "LOWER", "UPPER"]
    best_move: chess.Move | None


tt: dict[int, TTEntry] = {}
zobrist = init_zobrist()

# =========================================================
# TIME
# =========================================================

TIMEOUT = False


def out_of_time(start_time: float, max_time_ms: int) -> bool:
    elapsed = (time.perf_counter() - start_time) * 1000
    return elapsed >= max_time_ms


# =========================================================
# EVAL
# =========================================================


def evaluate_position(board: chess.Board) -> int:
    score = evaluate(board)
    return score if board.turn == chess.WHITE else -score


# =========================================================
# MOVE ORDERING
# =========================================================

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}


def score_move(
    board: chess.Board,
    move: chess.Move,
    tt_move: chess.Move | None,
    ply: int,
    config: EngineConfig,
):

    if move == tt_move:
        return 10_000_000

    if move.promotion:
        return 9_000_000

    if board.is_capture(move):

        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)

        if victim and attacker:
            return (
                5_000_000
                + 10 * PIECE_VALUES[victim.piece_type]
                - PIECE_VALUES[attacker.piece_type]
            )

    if config.killer_moves:

        if move == killer_moves[ply][0]:
            return 4_000_000

        if move == killer_moves[ply][1]:
            return 3_999_999

    if config.history_heuristic:
        return history[move.from_square][move.to_square]

    return 0


# =========================================================
# ROOT
# =========================================================


def find_best_move(
    board: chess.Board,
    config: EngineConfig,
):

    global TIMEOUT
    global nodes

    TIMEOUT = False
    nodes = 0

    start_time = time.perf_counter()

    best_move = None
    best_score = 0

    alpha = -INF
    beta = INF

    for depth in range(1, config.max_depth + 1):

        if out_of_time(start_time, config.max_time_ms):
            break

        if depth > 1:
            alpha = best_score - config.aspiration_window
            beta = best_score + config.aspiration_window

        while True:

            score, move = search_root(
                board=board,
                depth=depth,
                alpha=alpha,
                beta=beta,
                start_time=start_time,
                config=config,
            )

            if TIMEOUT:
                break

            if score <= alpha:
                alpha -= config.aspiration_window * 2
                continue

            if score >= beta:
                beta += config.aspiration_window * 2
                continue

            best_score = score
            best_move = move

            break

        if TIMEOUT:
            break

    return best_score, best_move


# =========================================================
# ROOT SEARCH
# =========================================================


def search_root(
    board: chess.Board,
    depth: int,
    alpha: int,
    beta: int,
    start_time: float,
    config: EngineConfig,
):

    best_move = None
    best_score = -INF

    moves = list(board.legal_moves)

    moves.sort(
        key=lambda move: score_move(
            board,
            move,
            None,
            0,
            config,
        ),
        reverse=True,
    )

    for move_index, move in enumerate(moves):

        if out_of_time(start_time, config.max_time_ms):
            global TIMEOUT
            TIMEOUT = True
            break

        board.push(move)

        if move_index == 0:

            score = -search(
                board,
                depth - 1,
                1,
                -beta,
                -alpha,
                start_time,
                config,
            )

        else:

            score = -search(
                board,
                depth - 1,
                1,
                -alpha - 1,
                -alpha,
                start_time,
                config,
            )

            if alpha < score < beta:

                score = -search(
                    board,
                    depth - 1,
                    1,
                    -beta,
                    -alpha,
                    start_time,
                    config,
                )

        board.pop()

        if TIMEOUT:
            break

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

    return best_score, best_move


# =========================================================
# SEARCH
# =========================================================


def search(
    board: chess.Board,
    depth: int,
    ply: int,
    alpha: int,
    beta: int,
    start_time: float,
    config: EngineConfig,
):

    global nodes
    nodes += 1

    key = zobrist_hash(board, zobrist)

    tt_entry = tt.get(key)

    if tt_entry and tt_entry["depth"] >= depth:

        tt_score = tt_entry["score"]

        if tt_entry["flag"] == "EXACT":
            return tt_score

        elif tt_entry["flag"] == "LOWER":
            alpha = max(alpha, tt_score)

        elif tt_entry["flag"] == "UPPER":
            beta = min(beta, tt_score)

        if alpha >= beta:
            return tt_score

    if out_of_time(start_time, config.max_time_ms):
        global TIMEOUT
        TIMEOUT = True
        return evaluate_position(board)

    if board.is_checkmate():
        return -MATE + ply

    if board.is_stalemate():
        return 0

    if depth <= 0:
        return quiescence(
            board,
            alpha,
            beta,
            start_time,
            config,
        )

    in_check = board.is_check()

    # NULL MOVE
    if config.null_move and depth >= 3 and not in_check:

        board.push(chess.Move.null())

        score = -search(
            board,
            depth - 1 - config.null_move_reduction,
            ply + 1,
            -beta,
            -beta + 1,
            start_time,
            config,
        )

        board.pop()

        if score >= beta:
            return beta

    best_score = -INF

    moves = list(board.legal_moves)
    tt_move = tt_entry["best_move"] if tt_entry else None

    moves.sort(
        key=lambda move: score_move(
            board,
            move,
            tt_move,
            ply,
            config,
        ),
        reverse=True,
    )
    original_alpha = alpha
    best_move = None

    for move_index, move in enumerate(moves):

        is_capture = board.is_capture(move)
        gives_check = board.gives_check(move)

        reduction = 0

        if (
            config.late_move_reduction
            and depth >= 4
            and move_index >= 4
            and not is_capture
            and not gives_check
            and not in_check
        ):
            reduction = 1

        extension = 0

        if config.check_extensions and gives_check:
            extension = 1

        board.push(move)

        new_depth = depth - 1 + extension

        if move_index == 0:

            score = -search(
                board,
                new_depth,
                ply + 1,
                -beta,
                -alpha,
                start_time,
                config,
            )

        else:

            score = -search(
                board,
                new_depth - reduction,
                ply + 1,
                -alpha - 1,
                -alpha,
                start_time,
                config,
            )

            if alpha < score < beta:

                score = -search(
                    board,
                    new_depth,
                    ply + 1,
                    -beta,
                    -alpha,
                    start_time,
                    config,
                )

        board.pop()

        if TIMEOUT:
            return alpha

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        if alpha >= beta:

            if not is_capture:

                if config.killer_moves:

                    if killer_moves[ply][0] != move:
                        killer_moves[ply][1] = killer_moves[ply][0]
                        killer_moves[ply][0] = move

                if config.history_heuristic:
                    history[move.from_square][move.to_square] += depth * depth

            break
    flag = "EXACT"

    if best_score <= original_alpha:
        flag = "UPPER"

    elif best_score >= beta:
        flag = "LOWER"

    tt[key] = {
        "depth": depth,
        "score": best_score,
        "flag": flag,
        "best_move": best_move,
    }
    return best_score


# =========================================================
# QUIESCENCE
# =========================================================


def quiescence(
    board: chess.Board,
    alpha: int,
    beta: int,
    start_time: float,
    config: EngineConfig,
):

    stand_pat = evaluate_position(board)

    if stand_pat >= beta:
        return beta

    alpha = max(alpha, stand_pat)

    moves = list(board.generate_legal_captures())

    moves.sort(
        key=lambda move: score_move(
            board,
            move,
            None,
            0,
            config,
        ),
        reverse=True,
    )

    for move in moves:

        if out_of_time(start_time, config.max_time_ms):
            global TIMEOUT
            TIMEOUT = True
            return alpha

        board.push(move)

        score = -quiescence(
            board,
            -beta,
            -alpha,
            start_time,
            config,
        )

        board.pop()

        if score >= beta:
            return beta

        alpha = max(alpha, score)

    return alpha
