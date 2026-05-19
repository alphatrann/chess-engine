import chess
import time

from src.human import choose_move

# =========================
# CONFIG
# =========================

MIN_LEVEL = 1
MAX_LEVEL = 10


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

        print(f"\nCheckmate! {winner} wins.")
        return True

    if board.is_stalemate():
        print("\nDraw by stalemate.")
        return True

    if board.is_insufficient_material():
        print("\nDraw by insufficient material.")
        return True

    if board.is_fifty_moves():
        print("\nDraw by fifty-move rule.")
        return True

    if board.is_repetition():
        print("\nDraw by repetition.")
        return True

    return False


def get_player_move(board: chess.Board) -> chess.Move:

    while True:

        move_input = input("Your move (UCI): ").strip().lower()

        try:

            move = chess.Move.from_uci(move_input)

            if move in board.legal_moves:
                return move

            print("Illegal move.")

        except:
            print("Invalid UCI format.")

        print()
        print("Examples:")
        print("  e2e4")
        print("  g1f3")
        print("  e7e8q")
        print()


def get_player_color() -> bool:

    while True:

        color = input("Choose your color ([w]hite / [b]lack): ").strip().lower()

        if color == "w":
            return chess.WHITE

        if color == "b":
            return chess.BLACK

        print("Invalid choice. Enter 'w' or 'b'.")
        print()


def get_engine_level() -> int:

    while True:

        level_input = input(f"Choose engine level ({MIN_LEVEL}-{MAX_LEVEL}): ").strip()

        try:

            level = int(level_input)

            if MIN_LEVEL <= level <= MAX_LEVEL:
                return level

        except:
            pass

        print(f"Invalid level. Enter a number from {MIN_LEVEL} to {MAX_LEVEL}.")
        print()


def print_engine_info(level: int):

    estimated_times = {
        1: "~0.05s",
        2: "~0.10s",
        3: "~0.20s",
        4: "~0.40s",
        5: "~0.80s",
        6: "~1.5s",
        7: "~3s",
        8: "~6s",
        9: "~10s",
        10: "~20s",
    }

    print()
    print("=========================")
    print(" ENGINE SETTINGS")
    print("=========================")
    print(f"Level: {level}")
    print(f"Estimated think time: {estimated_times[level]}")
    print()


# =========================
# GAME LOOP
# =========================


def play_game():

    board = chess.Board()

    print()
    print("=========================")
    print("      CLI CHESS")
    print("=========================")
    print()

    player_color = get_player_color()
    engine_level = get_engine_level()

    print_engine_info(engine_level)

    print(f"You play as {'White' if player_color == chess.WHITE else 'Black'}.")

    print()
    print("Enter moves in UCI format:")
    print("  e2e4")
    print("  g1f3")
    print("  e7e8q")
    print()

    while True:

        print_board(board)

        if print_game_status(board):
            break

        # =====================================
        # PLAYER TURN
        # =====================================

        if board.turn == player_color:

            move = get_player_move(board)

            board.push(move)

            print(f"\nYou played: {move.uci()}")

        # =====================================
        # ENGINE TURN
        # =====================================

        else:

            print("\nEngine thinking...\n")

            start = time.perf_counter()

            engine_move = choose_move(
                board,
                level=engine_level,
            )

            elapsed = time.perf_counter() - start

            if engine_move is None:
                print("Engine failed to find a move.")
                break

            board.push(engine_move)

            print(f"Engine move: {engine_move.uci()}")
            print(f"Think time: {elapsed:.3f}s")

        # =====================================
        # END CHECK
        # =====================================

        if print_game_status(board):

            print_board(board)
            break


# =========================
# RUN
# =========================

if __name__ == "__main__":
    play_game()
