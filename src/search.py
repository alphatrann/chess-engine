from typing import Literal, TypedDict

import chess

from src.eval import evaluate
from src.scoring import score_move
from src.zobrist import init_zobrist, zobrist_hash

CHECKMATE_SCORE = 100000
INF = 10**9
MAX_Q_DEPTH = 6


class TranspositionTableItem(TypedDict):
    depth: int
    score: int
    flag: Literal["EXACT", "LOWER", "UPPER"]


zobrist_tables = init_zobrist()
tt: dict[int, TranspositionTableItem] = dict()
cache_hits = 0


def find_best_move(board: chess.Board, depth: int):
    global cache_hits
    cache_hits = 0
    tt.clear()
    best_move = None
    best_score = -INF

    for d in range(1, depth + 1):
        best_score, best_move = __search_root(board, d, best_move)

    print("⚡ Cache hits:", cache_hits)

    return best_score, best_move


def __search_root(board: chess.Board, depth, prev_best_move=None):
    moves = list(board.generate_legal_moves())
    sorted_moves = sorted(moves, key=lambda move: score_move(board, move), reverse=True)

    if prev_best_move in sorted_moves:
        sorted_moves.remove(prev_best_move)
        sorted_moves = [prev_best_move] + sorted_moves

    alpha = -INF
    beta = INF

    best_score = -INF
    best_move = None

    for move in sorted_moves:
        board.push(move)
        score = -__search(board, depth - 1, 1, -beta, -alpha)
        board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

    return best_score, best_move


def __search(board: chess.Board, depth, ply, alpha=-INF, beta=INF):
    global cache_hits
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

    if board.is_checkmate():
        return -CHECKMATE_SCORE + ply  # prefers faster checkmate

    if (
        board.is_stalemate()
        or board.is_repetition()
        or board.is_insufficient_material()
    ):
        return 0

    if depth == 0:
        return __quiescence(board, alpha, beta, ply)

    best_score = -INF

    moves = list(board.generate_legal_moves())
    sorted_moves = sorted(moves, key=lambda move: score_move(board, move), reverse=True)
    original_alpha = alpha

    for move in sorted_moves:
        board.push(move)
        score = -__search(board, depth - 1, ply + 1, -beta, -alpha)
        board.pop()

        best_score = max(best_score, score)
        alpha = max(alpha, score)

        if alpha >= beta:
            break
    if best_score <= original_alpha:
        flag = "UPPER"
    elif best_score >= beta:
        flag = "LOWER"
    else:
        flag = "EXACT"

    tt[h] = {
        "score": best_score,
        "depth": depth,
        "flag": flag,
    }
    return best_score


def __quiescence(board: chess.Board, alpha=-INF, beta=INF, ply=0):
    if ply >= MAX_Q_DEPTH:
        return evaluate(board)
    stand_pat = evaluate(board)

    if stand_pat >= beta:
        return beta

    alpha = max(alpha, stand_pat)
    all_captures = list(board.generate_legal_captures())

    for move in all_captures:
        board.push(move)
        score = -__quiescence(board, -beta, -alpha, ply + 1)
        board.pop()

        if score >= beta:
            return beta

        alpha = max(alpha, score)

    return alpha
