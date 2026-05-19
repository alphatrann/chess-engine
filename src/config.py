from dataclasses import dataclass


@dataclass(slots=True)
class EngineConfig:

    # strength
    level: int

    # search limits
    max_depth: int
    max_time_ms: int

    # aspiration
    aspiration_window: int = 40

    # pruning
    null_move: bool = True
    null_move_reduction: int = 2

    futility_pruning: bool = True
    late_move_reduction: bool = True

    # extensions
    check_extensions: bool = True

    # qsearch
    delta_pruning: bool = True

    # move ordering
    killer_moves: bool = True
    history_heuristic: bool = True

    # optional weakening
    random_move_chance: float = 0.0


LEVELS: dict[int, EngineConfig] = {
    1: EngineConfig(
        level=1,
        max_depth=3,
        max_time_ms=200,
        late_move_reduction=False,
        null_move=False,
    ),
    2: EngineConfig(
        level=2,
        max_depth=3,
        max_time_ms=500,
    ),
    3: EngineConfig(
        level=3,
        max_depth=3,
        max_time_ms=1000,
    ),
    4: EngineConfig(
        level=4,
        max_depth=4,
        max_time_ms=2000,
    ),
    5: EngineConfig(
        level=5,
        max_depth=5,
        max_time_ms=4000,
    ),
    6: EngineConfig(
        level=6,
        max_depth=6,
        max_time_ms=6000,
    ),
    7: EngineConfig(
        level=7,
        max_depth=8,
        max_time_ms=8000,
    ),
    8: EngineConfig(
        level=8,
        max_depth=12,
        max_time_ms=10000,
    ),
    9: EngineConfig(
        level=9,
        max_depth=16,
        max_time_ms=15000,
    ),
    10: EngineConfig(
        level=10,
        max_depth=20,
        max_time_ms=20000,
    ),
}
