def test():
    import chess
    from .search import search

    fen1 = "r2qr1k1/1p3ppp/1p1p3b/2nP4/1R2P3/4P3/P1B1Q1PP/5RK1 b - - 0 25"  # white is down a knight
    fen2 = "r1bqk2r/pppp1ppp/5n2/4n3/1b1QP3/2N5/PPP2PPP/R1B1KBNR w KQkq - 0 6"  # Qxe5+
    board = chess.Board(fen2)
    best_score, best_move = search(board, depth=6)
    print("Best score:", best_score)
    print("Best move:", best_move.uci())


if __name__ == "__main__":
    test()
