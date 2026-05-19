

# Install

```bash
pip install python-chess msgpack nuitka
```

# Run

```bash
python main.py
```

# Build Executable

```bash
python -m nuitka \
  --standalone \
  --follow-imports \
  --assume-yes-for-downloads \
  main.py
```

# Unity JSON Example

Send:

```json
{"cmd":"new_game","level":5}
```

```json
{"cmd":"player_move","move":"e2e4"}
```

```json
{"cmd":"engine_move","movetime":1000}
```

Response:

```json
{
  "ok": true,
  "move": "e7e5",
  "fen": "...",
  "status": {
    "over": false
  }
}
```

# Unity UCI Example

```text
uci
isready
ucinewgame
position startpos
go movetime 1000
```