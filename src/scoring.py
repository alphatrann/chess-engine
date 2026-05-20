import chess

from src.const import CHECKMATE_SCORE
from src.pst import (
    MG_VALUES,
    EG_VALUES,
    MG_TABLES,
    EG_TABLES,
    PHASE_WEIGHTS,
)

TOTAL_PHASE = 24

# =========================================================
# HELPERS
# =========================================================


def game_phase(board: chess.Board) -> int:

    phase = 0

    for piece_type, weight in PHASE_WEIGHTS.items():
        phase += (
            len(board.pieces(piece_type, chess.WHITE))
            + len(board.pieces(piece_type, chess.BLACK))
        ) * weight

    return min(phase, TOTAL_PHASE)


def pst_value(table, square, color):

    if color == chess.WHITE:
        return table[square]

    return table[chess.square_mirror(square)]


# =========================================================
# PAWN STRUCTURE
# =========================================================


def isolated_pawn(board, square, color):

    file = chess.square_file(square)

    for adjacent in [file - 1, file + 1]:
        if 0 <= adjacent <= 7:
            for pawn in board.pieces(chess.PAWN, color):
                if chess.square_file(pawn) == adjacent:
                    return False

    return True


def doubled_pawn(board, square, color):

    file = chess.square_file(square)

    count = 0

    for pawn in board.pieces(chess.PAWN, color):
        if chess.square_file(pawn) == file:
            count += 1

    return count > 1


def passed_pawn(board, square, color):

    enemy = not color

    file = chess.square_file(square)
    rank = chess.square_rank(square)

    for pawn in board.pieces(chess.PAWN, enemy):
        ef = chess.square_file(pawn)
        er = chess.square_rank(pawn)

        if abs(ef - file) > 1:
            continue

        if color == chess.WHITE:
            if er > rank:
                return False

        else:
            if er < rank:
                return False

    return True


# =========================================================
# MOBILITY
# =========================================================


def mobility(board, color):

    score = 0

    original_turn = board.turn
    board.turn = color

    for move in board.legal_moves:
        piece = board.piece_at(move.from_square)

        if piece is None:
            continue

        match piece.piece_type:
            case chess.KNIGHT:
                score += 4

            case chess.BISHOP:
                score += 5

            case chess.ROOK:
                score += 2

            case chess.QUEEN:
                score += 1

    board.turn = original_turn

    return score


# =========================================================
# KING SAFETY
# =========================================================


def king_safety(board, color, phase):

    score = 0

    king_sq = board.king(color)

    if king_sq is None:
        return 0

    king_file = chess.square_file(king_sq)
    king_rank = chess.square_rank(king_sq)

    pawns = board.pieces(chess.PAWN, color)

    # pawn shield
    shield = 0

    for pawn in pawns:
        pf = chess.square_file(pawn)
        pr = chess.square_rank(pawn)

        if abs(pf - king_file) <= 1:
            if color == chess.WHITE:
                if pr >= king_rank:
                    shield += 1

            else:
                if pr <= king_rank:
                    shield += 1

    score += shield * 12

    # punish exposed king in middlegame
    if phase > 16:
        center_distance = abs(king_file - 3.5) + abs(king_rank - 3.5)

        score += int(center_distance * 8)

    return score


# =========================================================
# DEVELOPMENT
# =========================================================


def development(board, color):

    score = 0

    back_rank = 0 if color == chess.WHITE else 7

    # knights
    for sq in board.pieces(chess.KNIGHT, color):
        if chess.square_rank(sq) != back_rank:
            score += 15

    # bishops
    for sq in board.pieces(chess.BISHOP, color):
        if chess.square_rank(sq) != back_rank:
            score += 15

    # castling
    king_sq = board.king(color)

    if king_sq in [chess.G1, chess.C1, chess.G8, chess.C8]:
        score += 40

    return score


# =========================================================
# ROOK ACTIVITY
# =========================================================


def rook_activity(board, color):

    score = 0

    enemy = not color

    for rook in board.pieces(chess.ROOK, color):
        file = chess.square_file(rook)

        friendly_pawn = False
        enemy_pawn = False

        for pawn in board.pieces(chess.PAWN, color):
            if chess.square_file(pawn) == file:
                friendly_pawn = True
                break

        for pawn in board.pieces(chess.PAWN, enemy):
            if chess.square_file(pawn) == file:
                enemy_pawn = True
                break

        # open file
        if not friendly_pawn and not enemy_pawn:
            score += 25

        # semi-open
        elif not friendly_pawn:
            score += 12

    return score


# =========================================================
# MAIN EVAL
# =========================================================


def evaluate(board: chess.Board) -> int:

    # =====================================================
    # TERMINAL
    # =====================================================

    if board.is_checkmate():
        return -CHECKMATE_SCORE

    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.is_repetition()
    ):
        return 0

    # =====================================================
    # INIT
    # =====================================================

    mg_score = 0
    eg_score = 0

    phase = game_phase(board)

    # =====================================================
    # PIECES
    # =====================================================

    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == chess.WHITE else -1

        # bishop pair
        if len(board.pieces(chess.BISHOP, color)) >= 2:
            mg_score += sign * 35
            eg_score += sign * 50

        for piece_type in chess.PIECE_TYPES:
            for square in board.pieces(piece_type, color):
                mg = MG_VALUES[piece_type]
                eg = EG_VALUES[piece_type]

                mg += pst_value(
                    MG_TABLES[piece_type],
                    square,
                    color,
                )

                eg += pst_value(
                    EG_TABLES[piece_type],
                    square,
                    color,
                )

                # =========================================
                # PAWNS
                # =========================================

                if piece_type == chess.PAWN:
                    if isolated_pawn(board, square, color):
                        mg -= 15
                        eg -= 10

                    if doubled_pawn(board, square, color):
                        mg -= 12
                        eg -= 10

                    if passed_pawn(board, square, color):
                        rank = chess.square_rank(square)

                        if color == chess.BLACK:
                            rank = 7 - rank

                        mg += rank * 12
                        eg += rank * 25

                mg_score += sign * mg
                eg_score += sign * eg

        # ================================================
        # MOBILITY
        # ================================================

        mg_score += sign * mobility(board, color)

        # ================================================
        # KING SAFETY
        # ================================================

        mg_score += sign * king_safety(
            board,
            color,
            phase,
        )

        # ================================================
        # DEVELOPMENT
        # ================================================

        if phase >= 16:
            mg_score += sign * development(
                board,
                color,
            )

        # ================================================
        # ROOKS
        # ================================================

        mg_score += sign * rook_activity(
            board,
            color,
        )

    # =====================================================
    # TEMPO BONUS
    # =====================================================

    mg_score += 10 if board.turn == chess.WHITE else -10

    # =====================================================
    # TAPERED
    # =====================================================

    score = (mg_score * phase + eg_score * (TOTAL_PHASE - phase)) // TOTAL_PHASE

    return score
