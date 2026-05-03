# Overview

Chess Engine consists of two layers:

- Engine evaluation (Minimax + Alpha-beta)
- Human play (aggregated from common moves in Lichess database, categorized by rating)

Input: FEN string representing the board

Output: the UCI of the next move after two-layer evaluation

# Progression

The chess engine goes through 5 different stages of improvement. Each stage equips the engine with specific capabilities that make it more

v1: correct but shallow

v2: deeper and stable

v3: efficient and memory-aware

v4: selective and strategic

v5: human-aligned

# Engine

## v1: Foundation Model

### Minimax

This is a variant of traditional backtracking. Instead of finding a set of results that satisfies constraints, it simply outputs the evaluation scores for all next legal moves.

Given a FEN string and a value `depth`, here’s how it works:

1. List out all next legal moves
2. For each legal move, evaluates all the opponent’s possible legal responses
3. Recursively repeat step 1 up to `depth`
4. Score all the positions arising after `depth`
5. Pick the move in step 1 that yields the highest score

Below is a tree after evaluation with depth = 2 where the engine is trying to find the best move for white. Suppose white has two legal moves: A and B, for each legal move, the engine considers two black’s legal moves: A1, A2 and B1, B2. It realizes that black’s best play yields +0.8 for white if white plays move A, and only +0.2 if move B is made. Therefore, move A is the best in the position.

```
             (Root: White)
             /           \
         Move A         Move B
        /      \        /      \
     A1         A2    B1       B2
    +0.8       +1.2  +0.2     +0.5
```

### Alpha-beta pruning

Instead of exhaustively considering every possible moves which is extremely slow at a high depth, it optimizes search by:

1. Evaluate the first move like in minimax, which gives a score of X with best play from the opponent.
2. Then consider the second move. Two possible cases:
    1. If best play from the opponent yields a lower score compared to the first move, stop searching
    2. Otherwise, mark the second move as the current best move found.
3. Repeat step 2 for third move and so on.

### Scoring Function

Scoring in v1 is solely based on materials only. Although this is basic, it’s laying the groundwork for more complex scoring later.

```
Pawn   = 1
Knight = 3
Bishop = 3
Rook   = 5
Queen  = 9
```

## v2: Search Efficiency + Stable Evaluation

### Overview

At v1, the engine is logically correct but behaves like a beginner who:

- calculates a few moves ahead
- but misses deeper tactics
- and sometimes evaluates unstable positions incorrectly

v2 improves **how the engine searches**, not just what it evaluates.

The key idea:

> Instead of thinking once very hard, think multiple times and refine.
>

---

### Iterative Deepening

In v1, given depth = 4, the engine directly builds a tree of depth 4.

In v2, it does:

```
depth = 1 → evaluate all moves
depth = 2 → re-evaluate with opponent responses
depth = 3 → deeper refinement
depth = 4 → final decision
```

#### Intuition

At depth = 1:

- engine might think Qh5+ is best

At depth = 2:

- realizes opponent can defend easily → score drops

At depth = 3:

- finds Qxd8 wins material → becomes best move

So instead of guessing blindly at depth 4, it **builds understanding progressively**.

---

#### Why this improves alpha-beta

At depth = 3, suppose the best move found is:

```
Qxd8 → score +5
```

Now at depth = 4:

- engine tries Qxd8 first
- quickly establishes a strong baseline (+5)

When evaluating other moves:

- if they can’t beat +5, they get pruned early

Without iterative deepening:

- move order is random → pruning is weak

---

### Move Ordering

In v1, moves are evaluated in arbitrary order.

In v2, we deliberately try “promising” moves first.

#### Example

White to move:

- Qxd8 (wins queen)
- Qh5+ (check)
- a3 (quiet)

If evaluated in this order:

```
[a3, Qh5+, Qxd8]
```

Engine wastes time:

- explores a3 deeply before realizing it's bad

Instead reorder:

```
[Qxd8, Qh5+, a3]
```

Now:

- Qxd8 gives +9 immediately
- other moves get pruned faster

---

#### What counts as “promising”

At this stage, we don’t need complex heuristics.

We just assume:

- capturing valuable pieces is good
- giving check is forcing
- promotions are decisive

That’s enough to dramatically improve pruning.

---

### Quiescence Search

This fixes a subtle but important problem.

#### Problem Example

Engine reaches depth limit at this position:

- White can capture Black’s queen

So it evaluates:

```
+9 → winning
```

But in reality:

- Black can immediately recapture

True position:

```
material equal → score ≈ 0
```

---

#### Fix

When depth = 0:

- don’t stop immediately
- continue exploring **captures only**

So instead of:

```
depth 0 → evaluate
```

We do:

```
depth 0:
    if captures exist:
        explore captures
    else:
        evaluate
```

---

#### Intuition

The engine waits until the position becomes **“quiet”**, meaning:

- no immediate tactical explosions
- no obvious captures pending

Only then does it trust its evaluation.

---

### Scoring Function

Evaluation is now composed of two parts:

```
total_score = material + positional_score
```

---

#### Material

Same as v1:

```
Pawn   = 1
Knight = 3
Bishop = 3
Rook   = 5
Queen  = 9
```

---

#### Positional Score (Piece-Square Tables)

This is the main upgrade in v2.

For each piece type, define an **8×8 table**:

- each square has a small bonus or penalty
- represents how good that square is for that piece

---

#### Example: Knight Table

Knights prefer the center:

```
-0.5  -0.4  -0.3  -0.3  -0.3  -0.3  -0.4  -0.5
-0.4  -0.2   0.0   0.1   0.1   0.0  -0.2  -0.4
-0.3   0.1   0.3   0.4   0.4   0.3   0.1  -0.3
-0.3   0.2   0.4   0.5   0.5   0.4   0.2  -0.3
-0.3   0.2   0.4   0.5   0.5   0.4   0.2  -0.3
-0.3   0.1   0.3   0.4   0.4   0.3   0.1  -0.3
-0.4  -0.2   0.0   0.1   0.1   0.0  -0.2  -0.4
-0.5  -0.4  -0.3  -0.3  -0.3  -0.3  -0.4  -0.5
```

---

#### Pawn Structure

Simple penalties:

```
Doubled pawn → -0.2
Isolated pawn → -0.2
```

---

#### King Safety (Basic)

If king has weak pawn cover:

```
penalty ≈ -0.3
```

---

#### Example Evaluation

Position:

- White knight on d4 → +0.5
- Black knight on a8 → -0.5

```
positional_score = +1.0
```

Even with equal material:

→ engine prefers White

---

#### Handling Black Pieces

Instead of defining separate tables:

- reuse the same table
- mirror the board vertically

```
black_score = -white_table[mirrored_square]
```

---

### End Result

The engine now:

- avoids obvious tactical mistakes
- evaluates positions more stably
- searches deeper without exponential slowdown

It still isn’t “smart”, but it is now **reliable**.

---

## v3: Memory + Refined Positional Understanding

### Overview

At v2, the engine has:

- stable evaluation (material + piece-square tables)
- deeper and cleaner search

But it still behaves like:

> “I will recompute everything from scratch every time.”
>

This is inefficient because in chess:

- the same position can appear through different move orders

v3 introduces:

> memory and reuse of previous results
>

---

### Transposition Table

Different sequences can lead to the same position.

### Example

```
Line A:
1. Nf3 Nc6
2. d4 d5

Line B:
1. d4 d5
2. Nf3 Nc6
```

Same resulting position.

In v2:

- both lines are evaluated independently

In v3:

- first evaluation is stored
- second one is reused instantly

---

### Mechanism

We store:

```
position_hash → (depth, score, best_move)
```

When revisiting:

- if stored depth ≥ current depth
→ reuse score

---

### Intuition

The engine starts building a **memory of explored positions**, instead of recomputing them.

This reduces redundant work and allows deeper search.

---

### Move Ordering (Improved)

In v2, ordering was based on simple heuristics.

In v3, we reuse knowledge from previous searches.

---

### Priority Order

1. Best move from transposition table
2. Captures (prefer winning captures)
3. Previously strong moves (killer moves)
4. Historically good moves (history heuristic)
5. Remaining moves

---

### Example

At a node:

```
Moves: [a3, Qh5+, Re1, Qxd8]
```

After learning:

```
[Qxd8, Re1, Qh5+, a3]
```

Even though Re1 is a quiet move, it is tried early because it was effective before.

---

### Killer Moves

During search, some moves consistently cause pruning.

Example:

- move Re1 leads to strong pressure
- opponent cannot respond effectively
→ branch is cut early

This move is stored as a **killer move**

---

### Reuse

At similar depths:

- try Re1 early
- even if it is not a capture or check

---

### History Heuristic

Instead of remembering only a few moves:

- track how often each move improves evaluation

Example:

```
e4 → frequently improves score → high priority
h3 → rarely useful → low priority
```

---

### Scoring Function (v3)

We now extend v2:

```
total_score =
    material
  + piece_square_score
  + structural_score
```

Piece-square tables remain the **foundation**.

---

### Pawn Structure (Expanded)

From v2:

```
Doubled pawn → -0.2
Isolated pawn → -0.2
```

Add:

```
Passed pawn → +0.5 to +1.0 (increases as it advances)
```

---

### Mobility

Pieces with more legal moves are more active.

Example:

```
Knight with 8 moves → +0.2
Knight with 2 moves → -0.2
```

---

### King Safety (Improved)

Instead of a flat penalty:

- open file near king → -0.3
- missing pawn shield → -0.2

---

### Example Evaluation

Move A:

```
Material: +1
Piece-square: +0.2
King exposed: -0.6
Total: +0.6
```

Move B:

```
Material: 0
Piece-square: +0.5
Mobility: +0.3
Total: +0.8
```

→ engine prefers Move B

---

### End Result

The engine now:

- avoids recomputing positions
- searches significantly deeper
- starts making positional trade-offs (not just material)

It begins to feel **consistent across different lines**, not just locally correct.

---

## v4: Selective Search + Phase-Aware Evaluation

### Overview

At v3, the engine:

- searches efficiently
- evaluates positions reasonably well

But it still treats most moves similarly in depth.

In reality:

- some moves are critical (checks, captures)
- others are low impact

v4 introduces:

> selective search — spend effort where it matters
>

---

### Check Extensions

If a move gives check:

```
depth = d → search at d + 1
```

---

### Example

```
Qh5+ → forces response
```

Engine looks deeper because:

- opponent has limited replies
- tactical consequences are likely

---

### Late Move Reductions (LMR)

After evaluating best moves, remaining moves are less promising.

Example:

```
Move 1 → full depth
Move 2 → full depth
Move 8 → reduced depth (d - 1)
```

---

### Intuition

If a move:

- is not a capture
- not a check
- appears late

Then it is unlikely to be critical.

---

### Null Move Pruning

Engine asks:

> “If I skip my turn, am I still winning?”
>

If yes:

- opponent cannot threaten enough
→ prune branch

---

### Example

```
Position ≈ +3
Null move → still +2.5
```

→ no need to explore deeply

---

### Scoring Function (v4)

We now make evaluation **phase-aware**.

Still based on:

```
material + piece_square + structure
```

But weights change depending on game phase.

---

### King Tables (Important Upgrade)

In v2:

- king prefers safety (corner)

In v4:

- use different tables:

Early game:

```
king in corner → positive
king in center → negative
```

Endgame:

```
king in center → positive
```

---

### Piece Coordination

Add bonuses:

```
Connected rooks → +0.3
Bishop pair → +0.3
```

---

### Space Advantage

Reward control of central squares:

```
more central control → +0.2 to +0.5
```

---

### Example Evaluation (Endgame)

```
Material: 0
King centralization: +0.6
Passed pawn: +1.0
Total: +1.6
```

Engine prefers activating king over passive play.

---

### End Result

The engine now:

- focuses on critical lines
- skips irrelevant branches
- adapts evaluation to game phase

It becomes **strategically aware**, not just tactically correct.

---

## v5: Human Layer Integration

### Overview

At v4, the engine is:

- strong tactically
- reasonably good positionally

Now we reintroduce your second layer:

- human play patterns from database

The goal is not to override the engine, but to **guide it slightly**.

---

### Opening Book

From database (e.g. Lichess):

```
Position → {
  e4: 55%,
  d4: 35%,
  Nf3: 10%
}
```

Filter by rating if needed.

---

### Usage

In early game:

- choose among top moves
- optionally randomize slightly

This avoids:

- rare or unnatural openings

---

### Blended Evaluation

Outside opening phase, combine both layers:

```
final_score = engine_score + λ * human_score
```

Where:

- human_score = normalized frequency
- λ = small constant (0.1–0.3)

---

### Example

```
Move A:
engine = +0.5
human = 0.9
final = +0.59

Move B:
engine = +0.7
human = 0.1
final = +0.71
```

→ engine still chooses Move B

---

### Intuition

- engine handles correctness
- human layer biases toward common, practical moves

---

### Interaction with Piece-Square Tables

Important:

- human layer does **not replace evaluation**
- piece-square tables and structural scoring remain core

Human data only:

- nudges move choice
- especially in early game

---

### End Result

The engine now:

- plays natural openings
- avoids rare or awkward moves
- maintains tactical accuracy

It behaves less like a brute-force calculator and more like a **strong human player with calculation ability**.