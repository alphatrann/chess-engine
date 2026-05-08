import chess

from src.pst import evaluate_pst

MATERIAL_SCORES: dict[chess.PieceType, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 350,
    chess.ROOK: 500,
    chess.QUEEN: 900,
}


def score_move(
    board: chess.Board,
    killer_moves: list[list[chess.Move | None]],
    history: list[list[int]],
    move: chess.Move,
    ply: int,
):
    # captures (still highest)
    if board.is_capture(move):
        return 1000

    # promotions
    if move.promotion:
        return 900

    # checks
    if board.gives_check(move):
        return 800

    # killer moves (quiet but important)
    if move == killer_moves[ply][0]:
        return 700
    if move == killer_moves[ply][1]:
        return 600

    return history[move.from_square][move.to_square]


def score_position(board: chess.Board) -> int:
    return (
        evaluate_material(board)
        + evaluate_pst(board)
        + evaluate_pawn_structure(board)
        + evaluate_mobility(board)
        + evaluate_bishop_pair(board)
        + evaluate_rook_activity(board)
        + evaluate_king_safety(board)
    )


def evaluate_mobility(board: chess.Board) -> int:
    score = 0

    original_turn = board.turn

    for color in [chess.WHITE, chess.BLACK]:
        board.turn = color
        mobility = board.legal_moves.count()

        if color == chess.WHITE:
            score += mobility * 2
        else:
            score -= mobility * 2

    board.turn = original_turn
    return score


def evaluate_passed_pawns(board: chess.Board) -> int:
    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)
        enemy_pawns = board.pieces(chess.PAWN, not color)

        for sq in pawns:
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)

            passed = True

            for ep in enemy_pawns:
                ep_file = chess.square_file(ep)
                ep_rank = chess.square_rank(ep)

                if abs(ep_file - file) <= 1:
                    if color == chess.WHITE and ep_rank > rank:
                        passed = False
                    if color == chess.BLACK and ep_rank < rank:
                        passed = False

            if passed:
                bonus = 20 + rank * 10

                if color == chess.WHITE:
                    score += bonus
                else:
                    score -= bonus

    return score


def evaluate_bishop_pair(board: chess.Board) -> int:
    score = 0

    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += 30

    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= 30

    return score


def evaluate_rook_activity(board: chess.Board) -> int:
    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        rooks = board.pieces(chess.ROOK, color)
        pawns = board.pieces(chess.PAWN, color)

        for rook_sq in rooks:
            file = chess.square_file(rook_sq)

            open_file = True

            for pawn_sq in pawns:
                if chess.square_file(pawn_sq) == file:
                    open_file = False
                    break

            bonus = 0

            if open_file:
                bonus += 20

            rank = chess.square_rank(rook_sq)

            if color == chess.WHITE and rank == 6:
                bonus += 20

            if color == chess.BLACK and rank == 1:
                bonus += 20

            if color == chess.WHITE:
                score += bonus
            else:
                score -= bonus

    return score


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
