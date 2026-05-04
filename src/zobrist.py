from typing import TypedDict

import chess
import random

SQUARES_COUNT = 64
PIECE_TYPES_COUNT = 12


class ZobristTables(TypedDict):
    table: list[list[int]]
    castling: list[list[int]]
    en_passant: list[int]
    is_black_turn: int


def get_piece_index(piece: chess.Piece):
    return (0 if piece.color == chess.WHITE else 6) + (piece.piece_type - 1)


def init_zobrist() -> ZobristTables:
    table = [
        [random.getrandbits(64) for _ in range(PIECE_TYPES_COUNT)]
        for _ in range(SQUARES_COUNT)
    ]

    # [WK  WQ] (zobrist checking white's king and queen side castling rights)
    # [BK  BQ] (zobrist checking black's king and queen side castling rights)
    castling = [[random.getrandbits(64) for _ in range(2)] for _ in range(2)]

    en_passant = [random.getrandbits(64) for _ in range(8)]
    return {
        "table": table,
        "castling": castling,
        "en_passant": en_passant,
        "is_black_turn": random.getrandbits(64),
    }


def zobrist_hash(board: chess.Board, zobrist_tables: ZobristTables):
    h = 0
    if board.turn == chess.BLACK:
        h ^= zobrist_tables["is_black_turn"]

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            index = get_piece_index(piece)
            h ^= zobrist_tables["table"][square][index - 1]

    if board.has_kingside_castling_rights(chess.WHITE):
        h ^= zobrist_tables["castling"][0][0]
    if board.has_queenside_castling_rights(chess.WHITE):
        h ^= zobrist_tables["castling"][0][1]
    if board.has_kingside_castling_rights(chess.BLACK):
        h ^= zobrist_tables["castling"][1][0]
    if board.has_queenside_castling_rights(chess.BLACK):
        h ^= zobrist_tables["castling"][1][1]

    if board.ep_square is not None:
        h ^= zobrist_tables["en_passant"][board.ep_square % 8]

    return h
