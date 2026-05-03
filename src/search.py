from math import inf

import chess

from src.eval import evaluate
from src.moves import generate_moves


def search(
    board: chess.Board, depth: int, alpha: int | float = -inf, beta: int | float = inf
) -> tuple[int | float, chess.Move | None]:
    if depth == 0:
        return evaluate(board), None

    moves = generate_moves(board)

    best_score = -inf
    best_move = None
    for move in moves:
        board.push(move)
        score, _ = search(board, depth - 1, -beta, -alpha)
        score = -score
        board.pop()

        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

        if beta <= alpha:
            break

    return best_score, best_move
