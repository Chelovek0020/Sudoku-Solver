from __future__ import annotations

from dataclasses import dataclass
from math import isqrt
from time import perf_counter
from typing import Dict, List, Optional, Sequence, Set, Tuple

Coord = Tuple[int, int]


@dataclass(frozen=True)
class Cage:
    total: int
    cells: Tuple[Coord, ...]


@dataclass
class SolveConfig:
    size: int
    use_subgrid: bool = True
    diagonal: bool = False
    hyper: bool = False
    killer: bool = False
    cages: Tuple[Cage, ...] = ()
    timeout_sec: float = 20.0


@dataclass
class SolveResult:
    solved: bool
    grid: List[List[int]]
    elapsed_sec: float
    message: str = ""


class SudokuSolver:
    def __init__(self, config: SolveConfig):
        self.cfg = config
        self.n = config.size
        self.all_mask = (1 << self.n) - 1
        self.start_time = 0.0
        self.sqrt_n = isqrt(self.n)
        self.has_square_subgrid = self.sqrt_n * self.sqrt_n == self.n
        self.cell_to_cage: Dict[Coord, int] = {}
        self.cage_used_values: List[Set[int]] = []
        self.cage_sums: List[int] = []
        self._prepare_cages()

    def _prepare_cages(self) -> None:
        if not self.cfg.killer:
            return
        for idx, cage in enumerate(self.cfg.cages):
            self.cage_used_values.append(set())
            self.cage_sums.append(0)
            for c in cage.cells:
                self.cell_to_cage[c] = idx

    def _timeout(self) -> bool:
        return perf_counter() - self.start_time > self.cfg.timeout_sec

    def solve(self, grid: Sequence[Sequence[int]]) -> SolveResult:
        self.start_time = perf_counter()
        board = [list(row) for row in grid]
        if not self._validate_initial(board):
            return SolveResult(False, board, perf_counter() - self.start_time, "Некорректная стартовая сетка")

        row_used = [0] * self.n
        col_used = [0] * self.n
        box_used = [0] * self.n
        diag_used = [0, 0]
        hyper_used = [0] * 4

        for r in range(self.n):
            for c in range(self.n):
                val = board[r][c]
                if val == 0:
                    continue
                bit = 1 << (val - 1)
                row_used[r] |= bit
                col_used[c] |= bit
                if self.cfg.use_subgrid and self.has_square_subgrid:
                    box_used[self._box_index(r, c)] |= bit
                if self.cfg.diagonal:
                    if r == c:
                        diag_used[0] |= bit
                    if r + c == self.n - 1:
                        diag_used[1] |= bit
                if self.cfg.hyper:
                    hi = self._hyper_index(r, c)
                    if hi != -1:
                        hyper_used[hi] |= bit
                if self.cfg.killer and (r, c) in self.cell_to_cage:
                    cage_id = self.cell_to_cage[(r, c)]
                    self.cage_used_values[cage_id].add(val)
                    self.cage_sums[cage_id] += val

        ok = self._dfs(board, row_used, col_used, box_used, diag_used, hyper_used)
        elapsed = perf_counter() - self.start_time
        if self._timeout():
            return SolveResult(False, board, elapsed, "Превышен лимит времени решения")
        return SolveResult(ok, board, elapsed, "" if ok else "Решение не найдено")

    def _box_index(self, r: int, c: int) -> int:
        return (r // self.sqrt_n) * self.sqrt_n + (c // self.sqrt_n)

    def _hyper_index(self, r: int, c: int) -> int:
        if self.n < 9:
            return -1
        s = self.n // 3
        o = self.n // 6
        blocks = [
            (o, o),
            (o, o + s),
            (o + s, o),
            (o + s, o + s),
        ]
        for i, (rr, cc) in enumerate(blocks):
            if rr <= r < rr + s and cc <= c < cc + s:
                return i
        return -1

    def _candidate_mask(
        self,
        r: int,
        c: int,
        row_used: List[int],
        col_used: List[int],
        box_used: List[int],
        diag_used: List[int],
        hyper_used: List[int],
    ) -> int:
        used = row_used[r] | col_used[c]
        if self.cfg.use_subgrid and self.has_square_subgrid:
            used |= box_used[self._box_index(r, c)]
        if self.cfg.diagonal:
            if r == c:
                used |= diag_used[0]
            if r + c == self.n - 1:
                used |= diag_used[1]
        if self.cfg.hyper:
            hi = self._hyper_index(r, c)
            if hi != -1:
                used |= hyper_used[hi]
        mask = self.all_mask & ~used

        if self.cfg.killer and (r, c) in self.cell_to_cage:
            cage_id = self.cell_to_cage[(r, c)]
            cage = self.cfg.cages[cage_id]
            present = self.cage_used_values[cage_id]
            current_sum = self.cage_sums[cage_id]
            empty_left = sum(1 for rr, cc in cage.cells if rr != r or cc != c)
            out = 0
            for v in range(1, self.n + 1):
                if not (mask & (1 << (v - 1))):
                    continue
                if v in present:
                    continue
                target = cage.total - (current_sum + v)
                if empty_left == 0:
                    if target == 0:
                        out |= 1 << (v - 1)
                    continue
                min_possible = sum(i for i in range(1, empty_left + 1))
                max_possible = sum(range(self.n - empty_left + 1, self.n + 1))
                if min_possible <= target <= max_possible:
                    out |= 1 << (v - 1)
            return out

        return mask

    def _dfs(
        self,
        board: List[List[int]],
        row_used: List[int],
        col_used: List[int],
        box_used: List[int],
        diag_used: List[int],
        hyper_used: List[int],
    ) -> bool:
        if self._timeout():
            return False

        best: Optional[Tuple[int, int, int]] = None
        for r in range(self.n):
            for c in range(self.n):
                if board[r][c] != 0:
                    continue
                cm = self._candidate_mask(r, c, row_used, col_used, box_used, diag_used, hyper_used)
                count = cm.bit_count()
                if count == 0:
                    return False
                if best is None or count < best[2]:
                    best = (r, c, count)
                    best_mask = cm
                    if count == 1:
                        break
            if best is not None and best[2] == 1:
                break

        if best is None:
            return True

        r, c, _ = best
        mask = best_mask
        while mask:
            bit = mask & -mask
            mask -= bit
            v = bit.bit_length()
            board[r][c] = v

            row_used[r] |= bit
            col_used[c] |= bit
            if self.cfg.use_subgrid and self.has_square_subgrid:
                b = self._box_index(r, c)
                box_used[b] |= bit
            else:
                b = -1
            d1 = d2 = False
            if self.cfg.diagonal:
                if r == c:
                    diag_used[0] |= bit
                    d1 = True
                if r + c == self.n - 1:
                    diag_used[1] |= bit
                    d2 = True
            hi = -1
            if self.cfg.hyper:
                hi = self._hyper_index(r, c)
                if hi != -1:
                    hyper_used[hi] |= bit

            cage_id = -1
            if self.cfg.killer and (r, c) in self.cell_to_cage:
                cage_id = self.cell_to_cage[(r, c)]
                self.cage_used_values[cage_id].add(v)
                self.cage_sums[cage_id] += v

            if self._dfs(board, row_used, col_used, box_used, diag_used, hyper_used):
                return True

            board[r][c] = 0
            row_used[r] &= ~bit
            col_used[c] &= ~bit
            if b != -1:
                box_used[b] &= ~bit
            if d1:
                diag_used[0] &= ~bit
            if d2:
                diag_used[1] &= ~bit
            if hi != -1:
                hyper_used[hi] &= ~bit
            if cage_id != -1:
                self.cage_used_values[cage_id].remove(v)
                self.cage_sums[cage_id] -= v
        return False

    def _validate_initial(self, board: Sequence[Sequence[int]]) -> bool:
        n = self.n
        if len(board) != n or any(len(row) != n for row in board):
            return False
        for r in range(n):
            for c in range(n):
                v = board[r][c]
                if not 0 <= v <= n:
                    return False
        return True


def parse_cages(text: str) -> Tuple[Cage, ...]:
    """Format: 15:r1c1,r1c2;10:r2c1,r3c1"""
    cages: List[Cage] = []
    raw = text.strip()
    if not raw:
        return ()
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        total_s, cells_s = chunk.split(":", 1)
        total = int(total_s.strip())
        cells: List[Coord] = []
        for token in cells_s.split(","):
            token = token.strip().lower()
            if not token.startswith("r") or "c" not in token:
                raise ValueError(f"Bad cell token: {token}")
            r_s, c_s = token[1:].split("c", 1)
            r = int(r_s) - 1
            c = int(c_s) - 1
            cells.append((r, c))
        if not cells:
            raise ValueError("Empty cage")
        cages.append(Cage(total=total, cells=tuple(cells)))
    return tuple(cages)
