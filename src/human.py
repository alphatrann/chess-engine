# =========================================
# GET HUMAN MOVE
# =========================================


import random
import sqlite3

import chess
import chess.polyglot

from src.config import LEVELS
from src.const import DATABASE_PATH
from src.search import find_best_move


def get_human_move(
    board: chess.Board,
    level: int,
) -> chess.Move | None:

    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    zobrist = chess.polyglot.zobrist_hash(board)

    cur.execute(
        """
        SELECT move, count
        FROM book
        WHERE level = ? AND zobrist = ?
        ORDER BY count DESC
        """,
        (level, str(zobrist)),
    )

    rows = cur.fetchall()

    conn.close()

    if not rows:
        return None

    legal_moves = []
    weights = []

    for move_uci, count in rows:
        move = chess.Move.from_uci(move_uci)

        if move in board.legal_moves:
            legal_moves.append(move)
            weights.append(count)

    if not legal_moves:
        return None

    return random.choices(
        legal_moves,
        weights=weights,
        k=1,
    )[0]


# =========================================
# EXAMPLE ENGINE INTEGRATION
# =========================================


def choose_move(board: chess.Board, level: int):

    # opening book phase
    human_move = get_human_move(board, level)

    if human_move:
        print("📖 Human book:", human_move)
        return human_move

    # fallback to engine
    print("🧠 Engine search")
    _, move = find_best_move(board, LEVELS[level])

    return move
