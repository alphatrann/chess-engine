from dataclasses import dataclass


@dataclass(slots=True)
class EngineConfig:
    level: int

    max_depth: int
    max_time_ms: int

    aspiration_window: int = 40

    use_tt: bool = True

    null_move: bool = True
    null_move_reduction: int = 2

    futility_pruning: bool = True
    futility_margin: int = 100

    late_move_reduction: bool = True
    lmr_min_depth: int = 4
    lmr_min_move: int = 4

    check_extensions: bool = True
    max_extensions: int = 8

    delta_pruning: bool = True
    delta_margin: int = 200

    killer_moves: bool = True
    history_heuristic: bool = True

    random_move_chance: float = 0.0


LEVELS: dict[int, EngineConfig] = {
    # =====================================================
    # LEVEL 1
    # Beginner
    # =====================================================
    1: EngineConfig(
        level=1,
        max_depth=2,
        max_time_ms=100,
        use_tt=False,
        null_move=False,
        futility_pruning=False,
        delta_pruning=False,
        late_move_reduction=False,
        check_extensions=False,
        killer_moves=False,
        history_heuristic=False,
        random_move_chance=0.35,
    ),
    # =====================================================
    # LEVEL 2
    # Casual Beginner
    # =====================================================
    2: EngineConfig(
        level=2,
        max_depth=3,
        max_time_ms=300,
        use_tt=True,
        null_move=False,
        futility_pruning=False,
        delta_pruning=False,
        late_move_reduction=False,
        check_extensions=False,
        killer_moves=True,
        history_heuristic=False,
        random_move_chance=0.20,
    ),
    # =====================================================
    # LEVEL 3
    # Intermediate
    # =====================================================
    3: EngineConfig(
        level=3,
        max_depth=4,
        max_time_ms=800,
        use_tt=True,
        null_move=False,
        futility_pruning=False,
        delta_pruning=False,
        late_move_reduction=False,
        check_extensions=True,
        max_extensions=2,
        killer_moves=True,
        history_heuristic=True,
    ),
    # =====================================================
    # LEVEL 4
    # Club
    # =====================================================
    4: EngineConfig(
        level=4,
        max_depth=5,
        max_time_ms=1500,
        use_tt=True,
        null_move=False,
        futility_pruning=True,
        futility_margin=180,
        delta_pruning=True,
        delta_margin=250,
        late_move_reduction=False,
        check_extensions=True,
        max_extensions=3,
        killer_moves=True,
        history_heuristic=True,
    ),
    # =====================================================
    # LEVEL 5
    # Strong Club
    # =====================================================
    5: EngineConfig(
        level=5,
        max_depth=6,
        max_time_ms=3000,
        use_tt=True,
        null_move=True,
        null_move_reduction=2,
        futility_pruning=True,
        futility_margin=150,
        delta_pruning=True,
        delta_margin=220,
        late_move_reduction=True,
        lmr_min_depth=6,
        lmr_min_move=8,
        check_extensions=True,
        max_extensions=4,
        killer_moves=True,
        history_heuristic=True,
    ),
    # =====================================================
    # LEVEL 6
    # Expert
    # =====================================================
    6: EngineConfig(
        level=6,
        max_depth=7,
        max_time_ms=5000,
        use_tt=True,
        null_move=True,
        null_move_reduction=2,
        futility_pruning=True,
        futility_margin=120,
        delta_pruning=True,
        delta_margin=200,
        late_move_reduction=True,
        lmr_min_depth=5,
        lmr_min_move=6,
        check_extensions=True,
        max_extensions=5,
        killer_moves=True,
        history_heuristic=True,
    ),
    # =====================================================
    # LEVEL 7
    # Candidate Master
    # =====================================================
    7: EngineConfig(
        level=7,
        max_depth=8,
        max_time_ms=8000,
        use_tt=True,
        null_move=True,
        null_move_reduction=3,
        futility_pruning=True,
        futility_margin=100,
        delta_pruning=True,
        delta_margin=180,
        late_move_reduction=True,
        lmr_min_depth=4,
        lmr_min_move=5,
        check_extensions=True,
        max_extensions=6,
        killer_moves=True,
        history_heuristic=True,
    ),
    # =====================================================
    # LEVEL 8
    # Master
    # =====================================================
    8: EngineConfig(
        level=8,
        max_depth=9,
        max_time_ms=11000,
        use_tt=True,
        null_move=True,
        null_move_reduction=3,
        futility_pruning=True,
        futility_margin=90,
        delta_pruning=True,
        delta_margin=160,
        late_move_reduction=True,
        lmr_min_depth=4,
        lmr_min_move=4,
        check_extensions=True,
        max_extensions=7,
        killer_moves=True,
        history_heuristic=True,
    ),
    # =====================================================
    # LEVEL 9
    # Strong Master
    # =====================================================
    9: EngineConfig(
        level=9,
        max_depth=10,
        max_time_ms=14000,
        use_tt=True,
        null_move=True,
        null_move_reduction=3,
        futility_pruning=True,
        futility_margin=80,
        delta_pruning=True,
        delta_margin=140,
        late_move_reduction=True,
        lmr_min_depth=3,
        lmr_min_move=4,
        check_extensions=True,
        max_extensions=8,
        killer_moves=True,
        history_heuristic=True,
    ),
    # =====================================================
    # LEVEL 10
    # Full Strength
    # =====================================================
    10: EngineConfig(
        level=10,
        max_depth=12,
        max_time_ms=16000,
        use_tt=True,
        null_move=True,
        null_move_reduction=3,
        futility_pruning=True,
        futility_margin=70,
        delta_pruning=True,
        delta_margin=120,
        late_move_reduction=True,
        lmr_min_depth=3,
        lmr_min_move=3,
        check_extensions=True,
        max_extensions=10,
        killer_moves=True,
        history_heuristic=True,
    ),
}
