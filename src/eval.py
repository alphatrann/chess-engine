import chess

from src.scoring import score_position


def evaluate(board: chess.Board) -> int:
    score = score_position(board)
    if board.turn == chess.WHITE:
        return score
    else:
        return -score
