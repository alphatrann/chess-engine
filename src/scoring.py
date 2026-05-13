import chess

from src.phase import get_game_phase
from src.pst import evaluate_pst

CENTER = (chess.D4, chess.E4, chess.D5, chess.E5)


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
        return 200

    # killer moves (quiet but important)
    if move == killer_moves[ply][0]:
        return 100
    if move == killer_moves[ply][1]:
        return 90

    return history[move.from_square][move.to_square]


def score_position(board: chess.Board) -> int:
    return (
        evaluate_pst(board)
        + evaluate_pawn_structure(board)
        + evaluate_mobility(board)
        + evaluate_bishop_pair(board)
        + evaluate_rook_activity(board)
        + evaluate_king_safety(board)
        + evaluate_development(board)
        + evaluate_center_control(board)
        + evaluate_space(board)
        + evaluate_tempo(board)
    )


def evaluate_space(board: chess.Board) -> int:
    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == chess.WHITE else -1

        for sq in chess.SQUARES:
            rank = chess.square_rank(sq)

            if color == chess.WHITE and rank >= 4:
                attackers = len(board.attackers(color, sq))
                score += sign * attackers

            elif color == chess.BLACK and rank <= 3:
                attackers = len(board.attackers(color, sq))
                score += sign * attackers

    return score


def evaluate_tempo(board: chess.Board) -> int:
    return 10 if board.turn == chess.WHITE else -10


def evaluate_development(board: chess.Board) -> int:
    score = 0

    if get_game_phase(board) < 10:
        return 0

    STARTING_SQUARES = {
        chess.WHITE: {
            chess.KNIGHT: [chess.B1, chess.G1],
            chess.BISHOP: [chess.C1, chess.F1],
        },
        chess.BLACK: {
            chess.KNIGHT: [chess.B8, chess.G8],
            chess.BISHOP: [chess.C8, chess.F8],
        },
    }

    for color in [chess.WHITE, chess.BLACK]:
        sign = 1 if color == chess.WHITE else -1

        for piece_type, squares in STARTING_SQUARES[color].items():
            for sq in squares:
                piece = board.piece_at(sq)

                if piece == chess.Piece(piece_type, color):
                    score -= sign * 20

    return score


def evaluate_mobility(board: chess.Board) -> int:
    score = 0

    original_turn = board.turn

    for color in [chess.WHITE, chess.BLACK]:
        board.turn = color
        mobility = board.legal_moves.count()

        if color == chess.WHITE:
            score += mobility * 4
        else:
            score -= mobility * 4

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


def evaluate_center_control(board: chess.Board) -> int:
    score = 0

    for sq in CENTER:

        piece = board.piece_at(sq)

        if piece == chess.Piece(chess.PAWN, chess.WHITE):
            score += 25

        elif piece == chess.Piece(chess.PAWN, chess.BLACK):
            score -= 25

        white_attackers = len(board.attackers(chess.WHITE, sq))
        black_attackers = len(board.attackers(chess.BLACK, sq))

        score += (white_attackers - black_attackers) * 15

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


def evaluate_pawn_structure(board: chess.Board) -> int:
    score = 0

    for color in [chess.WHITE, chess.BLACK]:

        pawns = board.pieces(chess.PAWN, color)
        enemy_pawns = board.pieces(chess.PAWN, not color)

        files = [chess.square_file(sq) for sq in pawns]

        for sq in pawns:

            file = chess.square_file(sq)
            rank = chess.square_rank(sq)

            penalty = 0
            bonus = 0

            # =========================
            # DOUBLED PAWNS
            # =========================
            if files.count(file) > 1:
                penalty -= 20

            # =========================
            # ISOLATED PAWNS
            # =========================
            if not any(f in files for f in [file - 1, file + 1]):
                penalty -= 20

            # =========================
            # BACKWARD PAWNS
            # =========================
            backward = True

            for adj_file in [file - 1, file + 1]:

                if not (0 <= adj_file <= 7):
                    continue

                for friendly_sq in pawns:

                    if chess.square_file(friendly_sq) != adj_file:
                        continue

                    friendly_rank = chess.square_rank(friendly_sq)

                    # white pawn support
                    if color == chess.WHITE and friendly_rank >= rank:
                        backward = False

                    # black pawn support
                    if color == chess.BLACK and friendly_rank <= rank:
                        backward = False

            if backward:

                # square in front
                if color == chess.WHITE:

                    if rank < 7:
                        front_sq = chess.square(file, rank + 1)

                        if board.attackers(chess.BLACK, front_sq):
                            penalty -= 15

                else:

                    if rank > 0:
                        front_sq = chess.square(file, rank - 1)

                        if board.attackers(chess.WHITE, front_sq):
                            penalty -= 15

            # =========================
            # PASSED PAWNS
            # =========================
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

                advance = rank if color == chess.WHITE else (7 - rank)

                bonus += 20 + advance * 10

            # =========================
            # APPLY SCORE
            # =========================
            total = penalty + bonus

            if color == chess.WHITE:
                score += total
            else:
                score -= total

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
