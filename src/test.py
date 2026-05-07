import chess
import time

from src.search import find_best_move

# =========================
# TEST POSITIONS
# =========================
TESTS = [
    # L1 should handle
    {
        "name": "Free Queen",
        "fen": "rnb1kbnr/pppp1ppp/8/4p3/3q4/5N2/PPPPPPPP/RNBQKB1R w KQkq - 0 1",
        "best": ["f3d4"],  # Nxd4
    },
    {
        "name": "Back-rank Mate Threat",
        "fen": "6k1/5ppp/8/8/8/8/5PPP/5RK1 w - - 0 1",
        "best": ["f1a1", "f1b1", "f1c1", "f1d1", "f1e1"],
    },
    {
        "name": "Knight Fork",
        "fen": "r3k2r/pppp1ppp/2n1q3/3Np3/8/8/PPP2PPP/R1BQ1RK1 w kq - 0 1",
        "best": ["d5c7"],  # Nc7+
    },
    {
        "name": "Remove Defender",
        "fen": "1k6/p7/1p1prrB1/7P/4R3/2P3K1/PP3P2/8 b - - 0 1",
        "best": ["f6g6"],  # dxe5
    },
    {
        "name": "Mate in 1",
        "fen": "6k1/5ppp/8/8/8/8/5PPP/4RRK1 w - - 0 1",
        "best": ["e1e8"],
    },
    # L2 should handle well
    {
        "name": "Provoking Positional Weakness",
        "fen": "r2q1rk1/ppp1b1pp/2n1bp2/3p4/5B2/2PB1N2/PP3PPP/R2Q1RK1 w - - 0 1",
        "best": ["d1c2"],
    },
    {
        "name": "Mate in 3 + Queen Sac",
        "fen": "r4rk1/1p3ppp/3Rn3/p4NR1/1P6/5K2/P1Q1PP1P/q7 w - - 12 27",
        "best": ["f5e7"],
    },
    {
        "name": "Greek Gift Mate in 7",
        "fen": "rnb2rk1/pp1nqppp/4p3/3pP3/3p3P/2NB3N/PPP2PP1/R2QK2R w KQ - 0 10",
        "best": ["d3h7"],
    },
    {
        "name": "Multiple exchanges",
        "fen": "rnb2rk1/pp3pbp/6p1/q1pPN3/2B1n3/2N5/PP1B1PPP/R2QK2R b KQ - 2 12",
        "best": ["e4d2"],
    },
    {
        "name": "Trade sequence in Berlin defense",
        "fen": "r1bqkb1r/pppp1ppp/2nn4/1B2p3/3P4/5N2/PPP2PPP/RNBQ1RK1 w kq - 1 6",
        "best": ["b5c6"],
    },
    {
        "name": "Pawn structures",
        "fen": "rnb4r/1p2kpp1/p7/4p1N1/1b5p/2N4P/PPP3P1/2KR1B1R b - - 2 15",
        "best": ["b4c3"],
    },
    {
        "name": "Rook Sac to Open White's King",
        "fen": "2rq1rk1/pp1bpp2/3p1npQ/4n2p/3NP2P/1BN2P2/PPP3P1/2KR3R b - - 0 14",
        "best": ["c8c3"],
    },
    # L3 should Optimize
    {
        "name": "Symmetrical Position (Optimization with TT)",
        "fen": "r2q1rk1/ppp2ppp/2n2n2/3pp3/3PP3/2N2N2/PPP2PPP/R2Q1RK1 w - - 0 1",
        "best": ["d4e5", "e4d5"],
    },
    {
        "name": "Open Games",
        "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1",
        "best": ["f1c4", "f1b5", "d2d4", "b1c3"],
    },
    {
        "name": "Silent Killer Move",
        "fen": "r2qk2r/1p1b1pp1/p1pBpn1p/2P1N3/1n1P4/3B4/PPQ2PPP/2KR3R w kq - 0 1",
        "best": ["d3g6"],
    },
    {
        "name": "Should a hold a draw with a silent move",
        "fen": "4r2k/1b3Q1p/p1q3p1/1p4B1/2pb4/8/PPB3PP/5R1K w - - 0 1",
        "best": ["c2e4"],
    },
    {
        "name": "Should spot a silent move that traps the queen, forcing white to give up material",
        "fen": "4rrk1/ppp3pp/3p2n1/3Ppqb1/nPP5/6P1/P1NBQP1P/2R1NRK1 b - - 0 1",
        "best": ["a4c3"],
    },
]


# =========================
# TEST RUNNER
# =========================
def run_tests(depth=3):
    correct = 0
    total_time = 0

    print(f"\nRunning tests at depth {depth}\n")

    for test in TESTS:
        board = chess.Board(test["fen"])
        print(board)

        start = time.time()
        score, move = find_best_move(board, depth)
        end = time.time()

        elapsed = end - start
        total_time += elapsed

        is_correct = move.uci() in test["best"]

        if is_correct:
            correct += 1
            result = "✅"
        else:
            result = "❌"

        print(f"{result} {test['name']}")
        print(f"   Move: {move.uci()} (score: {score})")
        print(f"   Expected: {test['best']}")
        print(f"   Time: {elapsed:.4f}s\n")

    print("======== SUMMARY ========")
    print(f"Score: {correct}/{len(TESTS)}")
    print(f"Accuracy: {correct / len(TESTS) * 100:.1f}%")
    print(f"Total time: {total_time:.2f}s")
    print("=========================")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    run_tests(depth=5)
