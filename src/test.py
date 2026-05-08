import chess
import time
import csv
from src.search import find_best_move

# =========================
# TEST POSITIONS
# =========================
TESTS = []
with open("positions.csv", mode="r") as file:
    reader = csv.reader(file)
    for i, row in enumerate(reader):
        if i == 0:
            continue
        print(row)
        TESTS.append({"name": row[0], "fen": row[1], "best": row[2]})


# =========================
# TEST RUNNER
# =========================
def run_tests(depth=3):
    correct = 0
    total_time = 0

    print(f"\nRunning tests at depth {depth}\n")

    for test in TESTS:
        print(test["fen"])
        board = chess.Board(test["fen"])
        print(board)

        start = time.time()
        score, move = find_best_move(board, depth)
        end = time.time()

        elapsed = end - start
        total_time += elapsed

        is_correct = move.uci() == test["best"]

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
