import socket
import json
import chess


HOST = "127.0.0.1"
PORT = 8765


# =========================================================
# HELPERS
# =========================================================


def send(sock, payload):

    sock.sendall((json.dumps(payload) + "\n").encode())

    response = sock.recv(65536)

    return json.loads(response.decode())


def print_board(fen):

    board = chess.Board(fen)

    print()
    print(board)
    print()
    print(f"FEN: {fen}")
    print()


# =========================================================
# MAIN
# =========================================================


def main():

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((HOST, PORT))

    print(f"Connected to engine at {HOST}:{PORT}")

    # -----------------------------------------------------
    # START GAME
    # -----------------------------------------------------

    response = send(sock, {"cmd": "new_game", "level": 5})

    print(response)

    fen = response["fen"]

    # -----------------------------------------------------
    # GAME LOOP
    # -----------------------------------------------------

    while True:
        print_board(fen)

        move = input("Your move (uci): ").strip()

        # -------------------------------------------------
        # PLAYER MOVE
        # -------------------------------------------------

        response = send(sock, {"cmd": "player_move", "move": move})

        print("\nPLAYER RESPONSE:")
        print(json.dumps(response, indent=2))

        if not response["ok"]:
            continue

        fen = response["fen"]

        status = response["status"]

        if status["over"]:
            print("\nGAME OVER")
            print(status)
            break

        # -------------------------------------------------
        # ENGINE MOVE
        # -------------------------------------------------

        print("\nEngine thinking...\n")

        response = send(sock, {"cmd": "engine_move"})

        print("ENGINE RESPONSE:")
        print(json.dumps(response, indent=2))

        if not response["ok"]:
            print("Engine failed.")
            break

        fen = response["fen"]

        status = response["status"]

        print(f"\nEngine played: {response['move']}")

        if status["over"]:
            print_board(fen)

            print("\nGAME OVER")
            print(status)
            break

    sock.close()


if __name__ == "__main__":
    main()
