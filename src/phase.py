import chess


def get_game_phase(board: chess.Board) -> int:
    phase = 0

    phase += len(board.pieces(chess.QUEEN, chess.WHITE)) * 4
    phase += len(board.pieces(chess.QUEEN, chess.BLACK)) * 4
    phase += len(board.pieces(chess.ROOK, chess.WHITE)) * 2
    phase += len(board.pieces(chess.ROOK, chess.BLACK)) * 2
    phase += len(board.pieces(chess.BISHOP, chess.WHITE))
    phase += len(board.pieces(chess.BISHOP, chess.BLACK))
    phase += len(board.pieces(chess.KNIGHT, chess.WHITE))
    phase += len(board.pieces(chess.KNIGHT, chess.BLACK))

    return min(phase, 24)


def interp(opening, endgame, phase):
    return (opening * phase + endgame * (24 - phase)) // 24
