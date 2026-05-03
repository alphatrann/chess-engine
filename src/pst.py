# =========================
# PIECE-SQUARE TABLES
# =========================

# fmt: off
import chess

from src.phase import get_game_phase


PAWN_TABLE = [
     0,   0,   0,   0,   0,   0,  0,  0,
    50,  50,  50,  50,  50,  50, 50, 50,
    10,  10,  20,  30,  30,  20, 10, 10,
     5,   5,  10,  25,  25,  10,  5,  5,
     0,   0,   0,  20,  20,   0,  0,  0,
     5,  -5, -10,   0,   0, -10, -5,  5,
     5,  10,  10, -20, -20,  10, 10,  5,
     0,   0,   0,   0,   0,   0,  0,  0,
]

KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,  10,  10,   0, -20, -40,
    -30,  10,  30,  40,  40,  30,  10, -30,
    -30,  20,  40,  50,  50,  40,  20, -30,
    -30,  20,  40,  50,  50,  40,  20, -30,
    -30,  10,  30,  40,  40,  30,  10, -30,
    -40, -20,   0,  10,  10,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,  10,   0,   0,   0,   0,  10, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_TABLE = [
     0,   0,   5,  10,  10,   5,   0,   0,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     5,  10,  10,  10,  10,  10,  10,   5,
     0,   0,   0,   0,   0,   0,   0,   0,
]


QUEEN_TABLE = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]

KING_TABLE_OPENING = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20,
]

KING_TABLE_ENDGAME = [
    -50, -30, -30, -30, -30, -30, -30, -50,
    -30, -10,   0,   0,   0,   0, -10, -30,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -30, -10,   0,   5,   5,   0, -10, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]
# fmt: on


def evaluate_pst(board: chess.Board) -> int:
    score = 0
    phase = get_game_phase(board)

    def interp(opening, endgame):
        return (opening * phase + endgame * (24 - phase)) // 24

    for square in board.pieces(chess.PAWN, chess.WHITE):
        score += PAWN_TABLE[square]
    for square in board.pieces(chess.PAWN, chess.BLACK):
        score -= PAWN_TABLE[chess.square_mirror(square)]

    for square in board.pieces(chess.KNIGHT, chess.WHITE):
        score += KNIGHT_TABLE[square]
    for square in board.pieces(chess.KNIGHT, chess.BLACK):
        score -= KNIGHT_TABLE[chess.square_mirror(square)]

    for square in board.pieces(chess.BISHOP, chess.WHITE):
        score += BISHOP_TABLE[square]
    for square in board.pieces(chess.BISHOP, chess.BLACK):
        score -= BISHOP_TABLE[chess.square_mirror(square)]

    for square in board.pieces(chess.ROOK, chess.WHITE):
        score += ROOK_TABLE[square]
    for square in board.pieces(chess.ROOK, chess.BLACK):
        score -= ROOK_TABLE[chess.square_mirror(square)]

    for square in board.pieces(chess.QUEEN, chess.WHITE):
        score += QUEEN_TABLE[square]
    for square in board.pieces(chess.QUEEN, chess.BLACK):
        score -= QUEEN_TABLE[chess.square_mirror(square)]

    # king (interpolated)
    for square in board.pieces(chess.KING, chess.WHITE):
        score += interp(KING_TABLE_OPENING[square], KING_TABLE_ENDGAME[square])

    for square in board.pieces(chess.KING, chess.BLACK):
        score -= interp(
            KING_TABLE_OPENING[chess.square_mirror(square)],
            KING_TABLE_ENDGAME[chess.square_mirror(square)],
        )

    return score
