# Chess Engine Integration Guide

# Overview

The chess engine is packaged as a standalone executable.

Unity does NOT run Python directly.

Instead:

1. Unity launches `engine.exe`
2. The engine opens a TCP server locally
3. Unity connects to it through a socket
4. Unity sends JSON commands
5. The engine responds with JSON results

Architecture:

```text
Unity <-> TCP Socket <-> engine.exe
```

The communication happens entirely on the local machine.

No internet connection is involved.

---

# Folder Setup

Place the entire `engine` folder into:

```text
Assets/StreamingAssets/engine/
```

Final structure:

```text
Assets/
└── StreamingAssets/
    └── engine/
        ├── engine.exe
        ├── python312.dll
        ├── ...
        └── resources/human_book.db
```

Do NOT remove any DLLs or files from `engine/`.

---

# What Happens At Runtime

When the game launches:

```text
Unity starts
    ↓
Unity launches engine.exe
    ↓
engine.exe opens TCP port 8765
    ↓
Unity connects to 127.0.0.1:8765
    ↓
Unity sends chess commands
    ↓
Engine responds
```

The engine stays alive during the match.

Unity should NOT:
- launch the engine per move
- reconnect every move
- restart the process repeatedly

The engine should be launched once and reused.

---

# Step 1 — Launch The Engine Process

Unity must start the executable manually.

Example:

```csharp
using System.Diagnostics;
using System.IO;
using UnityEngine;

public class ChessEngineLauncher : MonoBehaviour
{
    private Process engineProcess;

    void Start()
    {
        string enginePath = Path.Combine(
            Application.streamingAssetsPath,
            "engine",
            "engine.exe"
        );

        engineProcess = new Process();

        engineProcess.StartInfo.FileName = enginePath;

        engineProcess.StartInfo.CreateNoWindow = true;
        engineProcess.StartInfo.UseShellExecute = false;

        engineProcess.Start();

        UnityEngine.Debug.Log("Chess engine started.");
    }

    private void OnApplicationQuit()
    {
        if (engineProcess != null && !engineProcess.HasExited)
        {
            engineProcess.Kill();
        }
    }
}
```

This launches the engine executable in the background.

---

# Step 2 — Connect To The TCP Server

The engine listens on:

```text
127.0.0.1:8765
```

Unity connects using `TcpClient`.

Example:

```csharp
using System.Net.Sockets;
using System.Threading.Tasks;
using UnityEngine;

public class ChessSocketClient : MonoBehaviour
{
    private TcpClient client;

    async void Start()
    {
        client = new TcpClient();

        await client.ConnectAsync(
            "127.0.0.1",
            8765
        );

        Debug.Log("Connected to chess engine.");
    }
}
```

---

# Step 3 — Send Requests To The Engine

The protocol uses:

- UTF-8 text
- JSON
- newline-delimited messages

VERY IMPORTANT:

Every request MUST end with:

```text
\n
```

Otherwise the server will wait forever.

---

# Full Example — Send A Request

Example Unity script:

```csharp
using System;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;

public class ChessEngineClient : MonoBehaviour
{
    private TcpClient client;
    private NetworkStream stream;

    async void Start()
    {
        client = new TcpClient();

        await client.ConnectAsync(
            "127.0.0.1",
            8765
        );

        stream = client.GetStream();

        Debug.Log("Connected.");

        await StartNewGame();
    }

    async Task StartNewGame()
    {
        string json =
            "{\"cmd\":\"new_game\",\"level\":5}\n";

        byte[] data = Encoding.UTF8.GetBytes(json);

        await stream.WriteAsync(data, 0, data.Length);

        Debug.Log("Request sent.");

        byte[] buffer = new byte[4096];

        int bytesRead = await stream.ReadAsync(
            buffer,
            0,
            buffer.Length
        );

        string response = Encoding.UTF8.GetString(
            buffer,
            0,
            bytesRead
        );

        Debug.Log("Response:");
        Debug.Log(response);
    }
}
```

---

# What Unity Sends

Unity sends:

```json
{"cmd":"new_game","level":5}
```

with a newline appended:

```text
{"cmd":"new_game","level":5}\n
```

The newline is required because the Python server uses:

```python
await reader.readline()
```

without newline:
- the server keeps waiting
- request never completes

---

# Example Response

The engine responds with:

```json
{
  "ok": true,
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

---

# Example Gameplay Flow

## Start Game

Unity sends:

```json
{"cmd":"new_game","level":5}
```

Engine responds:

```json
{
  "ok": true,
  "fen": "..."
}
```

---

## Player Makes Move

Unity sends:

```json
{
  "cmd":"player_move",
  "move":"e2e4"
}
```

Engine responds:

```json
{
  "ok": true,
  "fen":"...",
  "status":{
    "over":false
  }
}
```

---

## Ask Engine For Move

Unity sends:

```json
{
  "cmd":"engine_move"
}
```

Engine responds:

```json
{
  "ok": true,
  "move":"e7e5",
  "fen":"...",
  "status":{
    "over":false
  }
}
```

Unity then updates the board visually.

---

# Important Networking Notes

# 1. Use Async Calls

DO NOT use blocking socket calls on the Unity main thread.

Bad:

```csharp
stream.Read(...)
```

Good:

```csharp
await stream.ReadAsync(...)
```

Blocking the main thread causes:
- frame freezes
- UI stutter
- animation lag

---

# 2. Keep The Connection Open

Correct:

```text
connect once
reuse socket
```

Wrong:

```text
connect
send move
disconnect
repeat
```

The engine is designed as a persistent service.

---

# 3. One JSON Object Per Line

Correct:

```text
{"cmd":"ping"}\n
{"cmd":"get_board"}\n
```

Wrong:

```text
{"cmd":"ping"}{"cmd":"get_board"}
```

The server parses messages line-by-line.

---

# 4. TCP Is Stateful

The engine keeps:
- board state
- move history
- repetition tracking
- engine settings

Unity does NOT need to resend the entire game every move.

---

# Supported Commands

# new_game

Request:

```json
{"cmd":"new_game","level":5}
```

Starts a fresh game.

---

# player_move

Request:

```json
{
  "cmd":"player_move",
  "move":"e2e4"
}
```

Applies the player's move.

---

# engine_move

Request:

```json
{
  "cmd":"engine_move"
}
```

Asks the AI to calculate and play a move.

---

# set_position

Request:

```json
{
  "cmd":"set_position",
  "fen":"..."
}
```

Loads a board position directly.

Useful for:
- save/load
- puzzles
- analysis mode

---

# get_board

Request:

```json
{
  "cmd":"get_board"
}
```

Returns current board state.

---

# ping

Request:

```json
{
  "cmd":"ping"
}
```

Used to test connectivity.

---

# Error Handling

Example error response:

```json
{
  "ok": false,
  "error": "Illegal move: e2e5"
}
```

Unity should always check:

```csharp
if (!response.ok)
{
    // handle error
}
```

---

# Shutdown

When the game closes:

1. close socket
2. kill engine process

Example:

```csharp
client.Close();

engineProcess.Kill();
```

---

# Recommended Unity Architecture

Recommended structure:

```text
ChessEngineManager
├── Launch process
├── Connect socket
├── Send requests
├── Parse responses
└── Shutdown engine
```

Game UI should NOT directly manipulate sockets.

---

# Troubleshooting

# Engine does not start

Check:
- `engine.exe` exists
- all DLLs exist
- antivirus did not quarantine files

---

# Connection refused

Check:
- engine process is running
- port 8765 is open
- firewall permissions

---

# Request hangs forever

Most likely cause:

missing newline.

Wrong:

```text
{"cmd":"ping"}
```

Correct:

```text
{"cmd":"ping"}\n
```

---

# JSON parse errors

Ensure:
- UTF-8 encoding
- valid JSON
- one message per line