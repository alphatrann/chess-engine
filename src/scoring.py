import chess

from src.pst import evaluate_pst

MATERIAL_SCORES: dict[chess.PieceType, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 350,
    chess.ROOK: 500,
    chess.QUEEN: 900,
}


# prioritize captures, promotions and checks
def score_move(board: chess.Board, move: chess.Move):
    if board.is_capture(move):
        return 1000
    if move.promotion:
        return 900
    if board.gives_check(move):
        return 800
    return 0


def score_position(board: chess.Board) -> int:
    return evaluate_material(board) + evaluate_pst(board)


# =========================
# 1. MATERIAL
# =========================
def evaluate_material(board: chess.Board) -> int:

    material_score = 0
    for material, score in MATERIAL_SCORES.items():
        pieces = board.pieces(material, chess.WHITE)
        opponent_pieces = board.pieces(material, chess.BLACK)
        material_score += (len(pieces) - len(opponent_pieces)) * score
    return material_score
