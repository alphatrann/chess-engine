import chess

CHECKMATE_SCORE = 1000
MATERIAL_SCORES: dict[chess.PieceType, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 350,
    chess.ROOK: 500,
    chess.QUEEN: 900,
}


def score_position(board: chess.Board) -> int:
    if board.is_checkmate():
        return CHECKMATE_SCORE

    if (
        board.is_stalemate()
        or board.is_repetition()
        or board.is_insufficient_material()
    ):
        return 0

    turn = board.turn
    material_score = 0
    other_turn = chess.BLACK if board.turn == chess.WHITE else chess.WHITE
    for material, score in MATERIAL_SCORES.items():
        pieces = board.pieces(material, turn)
        opponent_pieces = board.pieces(material, other_turn)
        material_score += (len(pieces) - len(opponent_pieces)) * score
    return material_score
