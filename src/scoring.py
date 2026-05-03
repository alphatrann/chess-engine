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
    return (
        evaluate_material(board)
        + evaluate_pst(board)
        + evaluate_pawn_structure(board)
        + evaluate_king_safety(board)
    )


def evaluate_material(board: chess.Board) -> int:

    material_score = 0
    for material, score in MATERIAL_SCORES.items():
        pieces = board.pieces(material, chess.WHITE)
        opponent_pieces = board.pieces(material, chess.BLACK)
        material_score += (len(pieces) - len(opponent_pieces)) * score
    return material_score


def evaluate_pawn_structure(board: chess.Board) -> int:
    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)

        files = [chess.square_file(sq) for sq in pawns]

        for sq in pawns:
            file = chess.square_file(sq)

            penalty = 0

            # doubled pawn
            if files.count(file) > 1:
                penalty -= 20

            # isolated pawn
            if not any(f in files for f in [file - 1, file + 1]):
                penalty -= 20

            if color == chess.WHITE:
                score += penalty
            else:
                score -= penalty

    return score


def evaluate_king_safety(board: chess.Board) -> int:
    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if king_sq is None:
            continue

        penalty = 0

        king_file = chess.square_file(king_sq)

        # check surrounding squares for pawn cover
        directions = [-1, 0, 1]

        for df in directions:
            f = king_file + df
            if 0 <= f <= 7:
                pawn_found = False

                for sq in board.pieces(chess.PAWN, color):
                    if chess.square_file(sq) == f:
                        pawn_found = True
                        break

                if not pawn_found:
                    penalty -= 10

        if color == chess.WHITE:
            score += penalty
        else:
            score -= penalty

    return score
