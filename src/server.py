import asyncio
import json
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler

import chess
import msgpack

from src.human import choose_move


# =========================================================
# CONFIG
# =========================================================

HOST = "127.0.0.1"
PORT = 8765

DEFAULT_LEVEL = 5

USE_MSGPACK = False

LOG_FILE = "engine.log"
MAX_LOG_SIZE = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger("engine")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=MAX_LOG_SIZE,
    backupCount=LOG_BACKUP_COUNT,
)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)


# =========================================================
# ENGINE
# =========================================================

class EngineSession:

    def __init__(self):

        self.board = chess.Board()
        self.engine_level = DEFAULT_LEVEL

        self.stop_requested = False
        self.search_executor = ThreadPoolExecutor(max_workers=1)

        self._warmup()

    # -----------------------------------------------------

    def _warmup(self):

        logger.info("Warming up engine...")

        start = time.perf_counter()

        # Example warmup search
        temp_board = chess.Board()

        try:
            choose_move(temp_board, level=1)
        except:
            pass

        elapsed = time.perf_counter() - start

        logger.info(f"Warmup completed in {elapsed:.3f}s")

    # -----------------------------------------------------

    def reset(self):

        self.board.reset()
        self.stop_requested = False

    # -----------------------------------------------------

    def set_position(self, fen: str):

        self.board = chess.Board(fen)

    # -----------------------------------------------------

    def make_move(self, move_uci: str):

        move = chess.Move.from_uci(move_uci)

        if move not in self.board.legal_moves:
            raise ValueError(f"Illegal move: {move_uci}")

        self.board.push(move)

    # -----------------------------------------------------

    def request_stop(self):

        logger.info("Stop requested")
        self.stop_requested = True

    # -----------------------------------------------------

    def engine_move(self, movetime=None):

        self.stop_requested = False

        start = time.perf_counter()

        # =================================================
        # Replace this with proper iterative deepening later
        # =================================================

        move = choose_move(
            self.board,
            level=self.engine_level,
        )

        if self.stop_requested:
            logger.info("Search interrupted")
            return None

        if move is None:
            return None

        self.board.push(move)

        elapsed = time.perf_counter() - start

        logger.info(
            f"Engine move={move.uci()} time={elapsed:.3f}s"
        )

        return move

    # -----------------------------------------------------

    def game_status(self):

        board = self.board

        if board.is_checkmate():

            winner = "black" if board.turn == chess.WHITE else "white"

            return {
                "over": True,
                "result": "checkmate",
                "winner": winner,
            }

        if board.is_stalemate():
            return {
                "over": True,
                "result": "stalemate",
            }

        if board.is_insufficient_material():
            return {
                "over": True,
                "result": "insufficient_material",
            }

        if board.is_fifty_moves():
            return {
                "over": True,
                "result": "fifty_move_rule",
            }

        if board.is_repetition():
            return {
                "over": True,
                "result": "repetition",
            }

        return {
            "over": False,
        }


# =========================================================
# SERIALIZATION
# =========================================================

async def read_message(reader):

    raw = await reader.readline()

    if not raw:
        return None

    if USE_MSGPACK:
        return msgpack.unpackb(raw, raw=False)

    return json.loads(raw.decode())


async def write_message(writer, payload):

    if USE_MSGPACK:

        packed = msgpack.packb(payload)

        writer.write(packed + b"\n")

    else:

        writer.write(
            (json.dumps(payload) + "\n").encode()
        )

    await writer.drain()


# =========================================================
# UCI SUPPORT
# =========================================================

async def process_uci(session, line: str):

    line = line.strip()

    logger.info(f"UCI << {line}")

    if line == "uci":

        return "id name UnityPythonEngine\nid author OpenAI\nuciok"

    elif line == "isready":

        return "readyok"

    elif line == "ucinewgame":

        session.reset()

        return ""

    elif line.startswith("position"):

        tokens = line.split()

        if "fen" in tokens:

            fen_index = tokens.index("fen") + 1
            fen = " ".join(tokens[fen_index:fen_index + 6])

            session.set_position(fen)

        elif "startpos" in tokens:

            session.reset()

        return ""

    elif line.startswith("go"):

        loop = asyncio.get_running_loop()

        move = await loop.run_in_executor(
            session.search_executor,
            session.engine_move,
            None,
        )

        if move:
            return f"bestmove {move.uci()}"

        return "bestmove 0000"

    elif line == "stop":

        session.request_stop()

        return ""

    elif line == "quit":

        return "quit"

    return ""


# =========================================================
# JSON PROTOCOL
# =========================================================

async def process_json(session, request):

    cmd = request.get("cmd")

    # -----------------------------------------------------

    if cmd == "new_game":

        level = request.get("level", DEFAULT_LEVEL)

        session.engine_level = level
        session.reset()

        return {
            "ok": True,
            "fen": session.board.fen(),
        }

    # -----------------------------------------------------

    elif cmd == "set_position":

        fen = request["fen"]

        session.set_position(fen)

        return {
            "ok": True,
            "fen": session.board.fen(),
        }

    # -----------------------------------------------------

    elif cmd == "player_move":

        move = request["move"]

        session.make_move(move)

        return {
            "ok": True,
            "fen": session.board.fen(),
            "status": session.game_status(),
        }

    # -----------------------------------------------------

    elif cmd == "engine_move":

        movetime = request.get("movetime")

        loop = asyncio.get_running_loop()

        move = await loop.run_in_executor(
            session.search_executor,
            session.engine_move,
            movetime,
        )

        if move is None:

            return {
                "ok": False,
                "error": "Engine failed to find move",
            }

        return {
            "ok": True,
            "move": move.uci(),
            "fen": session.board.fen(),
            "status": session.game_status(),
        }

    # -----------------------------------------------------

    elif cmd == "stop":

        session.request_stop()

        return {
            "ok": True,
        }

    # -----------------------------------------------------

    elif cmd == "ping":

        return {
            "ok": True,
            "message": "pong",
        }

    # -----------------------------------------------------

    elif cmd == "get_board":

        return {
            "ok": True,
            "fen": session.board.fen(),
            "turn": "white" if session.board.turn else "black",
        }

    # -----------------------------------------------------

    return {
        "ok": False,
        "error": f"Unknown command: {cmd}",
    }


# =========================================================
# CLIENT HANDLER
# =========================================================

async def handle_client(reader, writer):

    addr = writer.get_extra_info("peername")

    logger.info(f"Client connected: {addr}")

    session = EngineSession()

    try:

        while True:

            raw = await reader.readline()

            if not raw:
                break

            try:

                line = raw.decode().strip()

                # =================================================
                # AUTO-DETECT UCI OR JSON
                # =================================================

                if line.startswith("{"):

                    request = json.loads(line)

                    response = await process_json(
                        session,
                        request,
                    )

                    await write_message(writer, response)

                else:

                    response = await process_uci(
                        session,
                        line,
                    )

                    if response == "quit":
                        break

                    if response:

                        writer.write(
                            (response + "\n").encode()
                        )

                        await writer.drain()

            except Exception as e:

                logger.error(traceback.format_exc())

                error_response = {
                    "ok": False,
                    "error": str(e),
                }

                await write_message(writer, error_response)

    finally:

        logger.info(f"Client disconnected: {addr}")

        writer.close()
        await writer.wait_closed()


# =========================================================
# MAIN
# =========================================================

async def main():

    logger.info(
        f"Starting chess engine server on {HOST}:{PORT}"
    )

    server = await asyncio.start_server(
        handle_client,
        HOST,
        PORT,
    )

    async with server:
        await server.serve_forever()


if __name__ == "__main__":

    asyncio.run(main())