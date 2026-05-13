import chess
import time

from src.search import find_best_move

# =========================
# CONFIG
# =========================
ENGINE_DEPTH = 5


# =========================
# HELPERS
# =========================
def print_board(board: chess.Board):
    print()
    print(board)
    print()

    print(f"FEN: {board.fen()}")
    print()


def print_game_status(board: chess.Board):
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        print(f"Checkmate! {winner} wins.")
        return True

    if board.is_stalemate():
        print("Stalemate.")
        return True

    if board.is_insufficient_material():
        print("Draw by insufficient material.")
        return True

    if board.is_fifty_moves():
        print("Draw by fifty-move rule.")
        return True

    if board.is_repetition():
        print("Draw by repetition.")
        return True

    return False


def get_player_move(board: chess.Board) -> chess.Move:
    while True:
        move_input = input("Your move (UCI): ").strip()

        try:
            move = chess.Move.from_uci(move_input)

            if move in board.legal_moves:
                return move

            print("Illegal move.")

        except:
            print("Invalid UCI format.")

        print("Example inputs:")
        print("  e2e4")
        print("  g1f3")
        print("  e7e8q (promotion)")
        print()


# =========================
# GAME LOOP
# =========================
def play_game():
    board = chess.Board()

    print("\n=========================")
    print(" CLI Chess Engine")
    print("=========================")
    print()
    print("You play as White.")
    print(f"Engine depth: {ENGINE_DEPTH}")
    print()
    print("Enter moves in UCI format.")
    print("Examples:")
    print("  e2e4")
    print("  g1f3")
    print("  e7e8q")
    print()

    while True:

        # =========================
        # PLAYER TURN
        # =========================
        print_board(board)

        if print_game_status(board):
            break

        move = get_player_move(board)

        board.push(move)

        print(f"\nYou played: {move.uci()}")

        if print_game_status(board):
            print_board(board)
            break

        # =========================
        # ENGINE TURN
        # =========================
        print("\nEngine thinking...\n")

        start = time.time()

        score, engine_move = find_best_move(board, ENGINE_DEPTH)

        end = time.time()

        elapsed = end - start

        board.push(engine_move)

        print(f"Engine move: {engine_move.uci()}")
        print(f"Evaluation: {score}")
        print(f"Time: {elapsed:.4f}s")

        if print_game_status(board):
            print_board(board)
            break


# =========================
# RUN
# =========================
if __name__ == "__main__":
    play_game()
