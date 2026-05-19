import sqlite3

import chess
import chess.pgn
import chess.polyglot

from src.const import DATABASE_PATH, MAX_PLY
from src.utils import get_level

# =========================================
# SQLITE SETUP
# =========================================


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS book (
        level INTEGER,
        zobrist INTEGER,
        move TEXT,
        count INTEGER,
        PRIMARY KEY(level, zobrist, move)
    )
    """)

    conn.commit()
    return conn


# =========================================
# BUILD BOOK
# =========================================


def build_book_from_pgn(pgn_path: str):
    conn = init_db()
    cur = conn.cursor()

    games_processed = 0

    with open(pgn_path, encoding="utf-8", errors="ignore") as pgn:

        while True:
            game = chess.pgn.read_game(pgn)

            if game is None:
                break

            try:
                white_elo = int(game.headers.get("WhiteElo", 0))
                black_elo = int(game.headers.get("BlackElo", 0))
            except ValueError:
                continue

            avg_elo = (white_elo + black_elo) // 2

            if avg_elo == 0:
                continue

            level = get_level(avg_elo)

            board = game.board()

            for ply, move in enumerate(game.mainline_moves()):

                if ply >= MAX_PLY:
                    break

                zobrist = chess.polyglot.zobrist_hash(board)

                cur.execute(
                    """
                    INSERT INTO book(level, zobrist, move, count)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(level, zobrist, move)
                    DO UPDATE SET count = count + 1
                    """,
                    (
                        level,
                        str(zobrist),
                        move.uci(),
                    ),
                )

                board.push(move)

            games_processed += 1

            if games_processed % 10000 == 0:
                conn.commit()
                print(f"Processed {games_processed} games")

    conn.commit()
    conn.close()

    print("Done building book")
