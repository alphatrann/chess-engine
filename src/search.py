import time
import chess

from typing import Literal, TypedDict
from chess.polyglot import zobrist_hash

from src.pst import MG_VALUES
from src.scoring import evaluate
from src.config import EngineConfig

INF = 10**9
MATE = 100000

MAX_PLY = 128
MAX_TT_SIZE = 2 * 10**6

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


def score_to_tt(score: int, ply: int) -> int:

    if score > MATE - 1000:
        return score + ply

    if score < -MATE + 1000:
        return score - ply

    return score


def score_from_tt(score: int, ply: int) -> int:

    if score > MATE - 1000:
        return score - ply

    if score < -MATE + 1000:
        return score + ply

    return score


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
                + 10 * MG_VALUES[victim.piece_type]
                - MG_VALUES[attacker.piece_type]
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
def store_tt(tt, key, depth, score, flag, best_move, ply):
    existing = tt.get(key)

    if existing is None or depth >= existing["depth"]:
        tt[key] = {
            "depth": depth,
            "score": score_to_tt(score, ply),
            "flag": flag,
            "best_move": best_move,
        }


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

    tt_move = None
    key = zobrist_hash(board)

    if config.use_tt and key in tt:
        tt_move = tt[key]["best_move"]

    moves = list(board.legal_moves)

    moves.sort(key=lambda m: score_move(board, m, tt_move, 0, config), reverse=True)

    for i, move in enumerate(moves):
        board.push(move)

        if i == 0:
            score = -search(board, depth - 1, 1, -beta, -alpha, start_time, config)
        else:
            score = -search(board, depth - 1, 1, -alpha - 1, -alpha, start_time, config)

            if alpha < score < beta:
                score = -search(board, depth - 1, 1, -beta, -alpha, start_time, config)

        board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        if alpha >= beta:
            break

    return best_score, best_move


# =========================================================
# SEARCH
# =========================================================
def ordered_moves(board, tt_move, ply, config):

    wins, killers, quiets, bad = [], [], [], []

    for move in board.legal_moves:
        if move == tt_move:
            yield move
            continue

        if board.is_capture(move):
            if simple_see(board, move) >= 0:
                wins.append(move)
            else:
                bad.append(move)

        elif config.killer_moves and move in killer_moves[ply]:
            killers.append(move)

        else:
            quiets.append(move)

    yield from wins
    yield from killers
    yield from quiets
    yield from bad


def search(
    board: chess.Board,
    depth: int,
    ply: int,
    alpha: int,
    beta: int,
    start_time: float,
    config: EngineConfig,
    extension_count: int = 0,
):

    global nodes, TIMEOUT
    nodes += 1

    if out_of_time(start_time, config.max_time_ms):
        TIMEOUT = True
        return evaluate_position(board)

    key = zobrist_hash(board)

    tt_entry = tt.get(key) if config.use_tt else None
    tt_move = None

    if tt_entry:
        tt_move = tt_entry["best_move"]

        if tt_entry["depth"] >= depth:
            score = score_from_tt(tt_entry["score"], ply)

            if tt_entry["flag"] == "EXACT":
                return score

            elif tt_entry["flag"] == "LOWER":
                alpha = max(alpha, score)

            elif tt_entry["flag"] == "UPPER":
                beta = min(beta, score)

            if alpha >= beta:
                return score

    if board.is_checkmate():
        return -MATE + ply

    if board.is_stalemate():
        return 0

    if depth <= 0:
        return quiescence(board, alpha, beta, start_time, config)

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
            extension_count,
        )
        board.pop()
        if score >= beta:
            return beta

    static_eval = evaluate_position(board)

    if config.futility_pruning and depth == 1 and not in_check:
        if static_eval + config.futility_margin <= alpha:
            return static_eval

    best_score = -INF
    best_move = None
    original_alpha = alpha

    for i, move in enumerate(ordered_moves(board, tt_move, ply, config)):
        is_cap = board.is_capture(move)
        gives_check = board.gives_check(move)

        reduction = 0

        if (
            config.late_move_reduction
            and depth >= config.lmr_min_depth
            and i >= config.lmr_min_move
            and not is_cap
            and not gives_check
            and not in_check
        ):
            reduction = 1

        extension = (
            1
            if (
                config.check_extensions
                and gives_check
                and extension_count < config.max_extensions
            )
            else 0
        )

        board.push(move)

        new_depth = depth - 1 + extension

        if i == 0:
            score = -search(
                board,
                new_depth,
                ply + 1,
                -beta,
                -alpha,
                start_time,
                config,
                extension_count + extension,
            )
        else:
            score = -search(
                board,
                max(0, new_depth - reduction),
                ply + 1,
                -alpha - 1,
                -alpha,
                start_time,
                config,
                extension_count + extension,
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
                    extension_count + extension,
                )

        board.pop()

        if TIMEOUT:
            return alpha

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        if alpha >= beta:
            if not is_cap and config.killer_moves:
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

    store_tt(tt, key, depth, best_score, flag, best_move, ply)

    return best_score


def simple_see(board: chess.Board, move: chess.Move):

    if not board.is_capture(move):
        return 0

    victim = board.piece_at(move.to_square)
    attacker = board.piece_at(move.from_square)

    if not victim or not attacker:
        return 0

    return MG_VALUES[victim.piece_type] - MG_VALUES[attacker.piece_type]


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

    global TIMEOUT
    global nodes

    nodes += 1

    if out_of_time(start_time, config.max_time_ms):
        return alpha

    stand = evaluate_position(board)

    if config.delta_pruning and stand + config.delta_margin < alpha:
        return alpha

    if stand >= beta:
        return beta

    alpha = max(alpha, stand)

    moves = list(board.generate_legal_captures())

    for move in moves:
        if simple_see(board, move) < 0:
            continue

        board.push(move)
        score = -quiescence(board, -beta, -alpha, start_time, config)
        board.pop()

        if score >= beta:
            return beta

        alpha = max(alpha, score)

    return alpha
