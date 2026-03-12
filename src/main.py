from __future__ import annotations

import ctypes
import random
import tkinter as tk
import webbrowser
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Dict, List, Optional, Set, Tuple

from PIL import Image, ImageDraw, ImageFont

from solver import Cage, SolveConfig, SudokuSolver, parse_cages

SYMBOLS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


TRANSLATIONS = {
    "en": {
        "app_title": "Sudoku Studio",
        "main_tab": "Boards",
        "gen_tab": "Generator",
        "size": "Board size",
        "mode": "Sudoku variant",
        "classic": "Classic",
        "diagonal": "Diagonal",
        "hyper": "Hyper",
        "killer": "Killer",
        "timeout": "Solve timeout (sec)",
        "new_board": "New board",
        "clear": "Clear all",
        "save": "Save image",
        "killer_cfg": "Killer cages",
        "killer_pick": "Create cage from selected cells",
        "support": "Support author",
        "status_ready": "Ready",
        "status_conflict": "⚠ Rule violation",
        "status_solving": "Solving...",
        "lang": "Language",
        "about": "About",
        "solve": "Solve",
        "invalid": "Invalid value for selected rules",
        "killer_help": "Format: 15:r1c1,r1c2;10:r2c1,r3c1",
        "generator_difficulty": "Difficulty",
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
        "generate": "Generate",
        "save_unsolved": "Save unsolved",
        "save_solved": "Save solved",
    },
    "ru": {
        "app_title": "Sudoku Studio",
        "main_tab": "Поля",
        "gen_tab": "Генератор",
        "size": "Размер поля",
        "mode": "Вариант судоку",
        "classic": "Классика",
        "diagonal": "Диагональное",
        "hyper": "Hyper",
        "killer": "Killer",
        "timeout": "Таймаут решения (сек)",
        "new_board": "Новое поле",
        "clear": "Очистить",
        "save": "Сохранить фото",
        "killer_cfg": "Настройка killer",
        "killer_pick": "Создать клетку из выделения",
        "support": "Поддержать автора",
        "status_ready": "Готово",
        "status_conflict": "⚠ Нарушение правил",
        "status_solving": "Решение...",
        "lang": "Язык",
        "about": "О программе",
        "solve": "Решить",
        "invalid": "Значение нарушает правила",
        "killer_help": "Формат: 15:r1c1,r1c2;10:r2c1,r3c1",
        "generator_difficulty": "Сложность",
        "easy": "Легко",
        "medium": "Средне",
        "hard": "Сложно",
        "generate": "Генерировать",
        "save_unsolved": "Сохранить нерешенное",
        "save_solved": "Сохранить решенное",
    },
}

MODE_INFO = {
    "classic": "Rows/columns are unique; subgrids are unique when size has square root.",
    "diagonal": "Classic rules + both main diagonals must contain unique symbols.",
    "hyper": "Classic rules + 4 internal hyper boxes must contain unique symbols.",
    "killer": "Classic rules + cages with target sums and no repeats in a cage.",
}


@dataclass
class BoardState:
    size: int = 9
    mode: str = "classic"
    grid: List[List[int]] = field(default_factory=list)
    cages: Tuple[Cage, ...] = ()
    active: Tuple[int, int] = (0, 0)
    selected: Set[Tuple[int, int]] = field(default_factory=set)
    drag_anchor: Optional[Tuple[int, int]] = None
    solve_future: Optional[Future] = None


class KillerEditor(tk.Toplevel):
    def __init__(self, parent: tk.Misc, initial: str, title: str, help_text: str):
        super().__init__(parent)
        self.result: Optional[str] = None
        self.title(title)
        self.geometry("520x360")
        ttk.Label(self, text=help_text).pack(anchor="w", padx=10, pady=(10, 4))
        self.text = tk.Text(self, wrap="word", undo=True)
        self.text.pack(fill="both", expand=True, padx=10, pady=6)
        self.text.insert("1.0", initial)
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=10)
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right", padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")

    def _ok(self):
        self.result = self.text.get("1.0", "end").strip()
        self.destroy()


class SudokuApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.lang = tk.StringVar(value="en")
        self.status_var = tk.StringVar(value=self.t("status_ready"))
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.board_tabs: Dict[str, BoardState] = {}

        self.root.geometry("1480x930")
        self.root.title(self.t("app_title"))
        self._apply_icon()

        self._build_ui()
        self._create_board_tab()
        self.root.bind_all("<Key>", self._on_key)

    def t(self, key: str) -> str:
        return TRANSLATIONS[self.lang.get()].get(key, key)

    def _apply_icon(self):
        icon_path = Path("assets/app.ico")
        if icon_path.exists():
            try:
                self.root.iconbitmap(default=str(icon_path))
            except tk.TclError:
                pass
        if Path("assets/app.ico").exists() and self._is_windows():
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("sudoku.studio.app")

    @staticmethod
    def _is_windows() -> bool:
        import sys

        return sys.platform.startswith("win")

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text=self.t("lang")).pack(side="left")
        ttk.Combobox(top, textvariable=self.lang, values=["en", "ru"], width=6, state="readonly").pack(side="left", padx=6)
        ttk.Button(top, text=self.t("about"), command=self._about).pack(side="left", padx=6)
        ttk.Button(top, text=self.t("new_board"), command=self._create_board_tab).pack(side="left", padx=6)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self._refresh_current())

        self.gen_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.gen_tab, text=self.t("gen_tab"))
        self._build_generator()

        bottom = ttk.Frame(self.root, padding=(10, 8))
        bottom.pack(fill="x")
        self.status_label = ttk.Label(bottom, textvariable=self.status_var)
        self.status_label.pack(side="left")
        ttk.Button(bottom, text=self.t("support"), command=lambda: webbrowser.open("https://www.donationalerts.com/r/supermine_")).pack(side="right")

    def _about(self):
        text = "Sudoku Studio\nClassic/Diagonal/Hyper/Killer\nMulti-tab, generator, PNG export."
        messagebox.showinfo(self.t("about"), text)

    def _create_board_tab(self):
        frame = ttk.Frame(self.notebook)
        board_id = f"board_{len(self.board_tabs)+1}"
        self.board_tabs[board_id] = BoardState()
        self._init_board(self.board_tabs[board_id])

        main = ttk.Frame(frame, padding=8)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(main, width=360)
        right.pack(side="right", fill="y", padx=(10, 0))

        canvas = tk.Canvas(left, bg="white", highlightthickness=1, highlightbackground="#C8C8C8")
        canvas.pack(fill="both", expand=True)
        canvas.bind("<Configure>", lambda _e, bid=board_id: self._redraw(bid))
        canvas.bind("<Button-1>", lambda e, bid=board_id: self._click_cell(e, bid, add=self._is_shift_pressed(e)))
        canvas.bind("<B1-Motion>", lambda e, bid=board_id: self._drag_select(e, bid))
        canvas.bind("<ButtonRelease-1>", lambda _e, bid=board_id: self._finish_drag(bid))

        size_var = tk.IntVar(value=9)
        timeout_var = tk.DoubleVar(value=20)
        mode_var = tk.StringVar(value="classic")

        widgets = {
            "frame": frame,
            "canvas": canvas,
            "size_var": size_var,
            "timeout_var": timeout_var,
            "mode_var": mode_var,
        }
        self.board_tabs[board_id].widgets = widgets  # type: ignore[attr-defined]

        ttk.Label(right, text=self.t("size")).pack(anchor="w")
        ttk.Spinbox(right, from_=3, to=30, width=8, textvariable=size_var).pack(anchor="w", pady=(0, 6))

        ttk.Label(right, text=self.t("mode")).pack(anchor="w", pady=(6, 2))
        for mode in ["classic", "diagonal", "hyper", "killer"]:
            row = ttk.Frame(right)
            row.pack(anchor="w", fill="x")
            ttk.Radiobutton(row, text=self.t(mode), value=mode, variable=mode_var, command=lambda bid=board_id: self._switch_mode(bid)).pack(side="left")
            ttk.Button(row, text="i", width=2, command=lambda m=mode: self._show_mode_info(m)).pack(side="left", padx=4)

        ttk.Button(right, text=self.t("killer_cfg"), command=lambda bid=board_id: self._configure_killer_text(bid)).pack(fill="x", pady=(8, 2))
        ttk.Button(right, text=self.t("killer_pick"), command=lambda bid=board_id: self._create_killer_cage_from_selection(bid)).pack(fill="x", pady=2)

        ttk.Label(right, text=self.t("timeout")).pack(anchor="w", pady=(8, 2))
        ttk.Spinbox(right, from_=1, to=180, increment=1, width=8, textvariable=timeout_var).pack(anchor="w", pady=(0, 8))

        ttk.Button(right, text=self.t("new_board"), command=lambda bid=board_id: self._reset_grid(bid)).pack(fill="x", pady=2)
        ttk.Button(right, text=self.t("clear"), command=lambda bid=board_id: self._clear_selection_or_all(bid)).pack(fill="x", pady=2)
        ttk.Button(right, text=self.t("save"), command=lambda bid=board_id: self._save_image(bid)).pack(fill="x", pady=2)

        ttk.Separator(right).pack(fill="x", pady=8)
        keypad = ttk.Frame(right)
        keypad.pack(fill="x")
        self.board_tabs[board_id].keypad = keypad  # type: ignore[attr-defined]
        self._rebuild_keypad(board_id)

        self.notebook.insert(self.notebook.index("end") - 1, frame, text=f"Board {len(self.board_tabs)}")
        self.notebook.select(frame)
        self._redraw(board_id)

    def _show_mode_info(self, mode: str):
        messagebox.showinfo(self.t(mode), MODE_INFO[mode])

    def _build_generator(self):
        f = ttk.Frame(self.gen_tab, padding=14)
        f.pack(fill="both", expand=True)
        self.gen_size = tk.IntVar(value=9)
        self.gen_mode = tk.StringVar(value="classic")
        self.gen_diff = tk.StringVar(value="medium")
        self.gen_unsolved: Optional[List[List[int]]] = None
        self.gen_solved: Optional[List[List[int]]] = None

        ttk.Label(f, text=self.t("size")).grid(row=0, column=0, sticky="w")
        ttk.Spinbox(f, from_=3, to=30, textvariable=self.gen_size, width=8).grid(row=0, column=1, sticky="w")
        ttk.Label(f, text=self.t("mode")).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(f, textvariable=self.gen_mode, values=["classic", "diagonal", "hyper", "killer"], state="readonly", width=14).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Label(f, text=self.t("generator_difficulty")).grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(f, textvariable=self.gen_diff, values=["easy", "medium", "hard"], state="readonly", width=14).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Button(f, text=self.t("generate"), command=self._generate_puzzle).grid(row=3, column=0, pady=12, sticky="w")
        ttk.Button(f, text=self.t("save_unsolved"), command=lambda: self._save_grid_img(self.gen_unsolved)).grid(row=3, column=1, pady=12, sticky="w")
        ttk.Button(f, text=self.t("save_solved"), command=lambda: self._save_grid_img(self.gen_solved)).grid(row=3, column=2, pady=12, sticky="w")

    def _generate_puzzle(self):
        n = self.gen_size.get()
        mode = self.gen_mode.get()
        cfg = SolveConfig(size=n, use_subgrid=True, diagonal=mode == "diagonal", hyper=mode == "hyper", killer=False, timeout_sec=30)
        solver = SudokuSolver(cfg)
        base = [[0 for _ in range(n)] for _ in range(n)]
        random.seed()
        solved = self._randomized_solve(solver, base)
        if solved is None:
            messagebox.showerror("Error", "Generation failed")
            return
        remove_ratio = {"easy": 0.45, "medium": 0.6, "hard": 0.72}[self.gen_diff.get()]
        puzzle = [row[:] for row in solved]
        cells = [(r, c) for r in range(n) for c in range(n)]
        random.shuffle(cells)
        remove_count = int(len(cells) * remove_ratio)
        for r, c in cells[:remove_count]:
            puzzle[r][c] = 0
        self.gen_unsolved = puzzle
        self.gen_solved = solved
        self.status_var.set("Generated")

    def _randomized_solve(self, solver: SudokuSolver, grid: List[List[int]]) -> Optional[List[List[int]]]:
        n = len(grid)

        def rec(board: List[List[int]]) -> bool:
            best = None
            best_mask = 0
            row_used = [0] * n
            col_used = [0] * n
            box_used = [0] * n
            diag_used = [0, 0]
            hyper_used = [0] * 4
            for rr in range(n):
                for cc in range(n):
                    v = board[rr][cc]
                    if v:
                        bit = 1 << (v - 1)
                        row_used[rr] |= bit
                        col_used[cc] |= bit
                        if solver.cfg.use_subgrid and solver.has_square_subgrid:
                            box_used[solver._box_index(rr, cc)] |= bit
                        if solver.cfg.diagonal:
                            if rr == cc:
                                diag_used[0] |= bit
                            if rr + cc == n - 1:
                                diag_used[1] |= bit
                        if solver.cfg.hyper:
                            hi = solver._hyper_index(rr, cc)
                            if hi != -1:
                                hyper_used[hi] |= bit
            for rr in range(n):
                for cc in range(n):
                    if board[rr][cc] != 0:
                        continue
                    mask = solver._candidate_mask(rr, cc, row_used, col_used, box_used, diag_used, hyper_used)
                    cnt = mask.bit_count()
                    if cnt == 0:
                        return False
                    if best is None or cnt < best[2]:
                        best = (rr, cc, cnt)
                        best_mask = mask
            if best is None:
                return True
            rr, cc, _ = best
            vals = [b.bit_length() for b in _bits(best_mask)]
            random.shuffle(vals)
            for v in vals:
                board[rr][cc] = v
                if rec(board):
                    return True
                board[rr][cc] = 0
            return False

        b = [row[:] for row in grid]
        return b if rec(b) else None

    def _save_grid_img(self, grid: Optional[List[List[int]]]):
        if not grid:
            messagebox.showinfo("Info", "Generate puzzle first")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self._draw_grid_to_image(grid, path)

    def _switch_mode(self, board_id: str):
        self._redraw(board_id)

    def _current_board_id(self) -> Optional[str]:
        current = self.notebook.select()
        for bid, st in self.board_tabs.items():
            if str(st.widgets["frame"]) == current:
                return bid
        return None

    def _refresh_current(self):
        bid = self._current_board_id()
        if bid:
            self._redraw(bid)

    def _init_board(self, st: BoardState):
        st.grid = [[0 for _ in range(st.size)] for _ in range(st.size)]
        st.active = (0, 0)
        st.selected = {(0, 0)}
        st.drag_anchor = None

    def _reset_grid(self, board_id: str):
        st = self.board_tabs[board_id]
        st.size = st.widgets["size_var"].get()
        st.mode = st.widgets["mode_var"].get()
        self._init_board(st)
        self._rebuild_keypad(board_id)
        self._redraw(board_id)

    def _rebuild_keypad(self, board_id: str):
        st = self.board_tabs[board_id]
        panel = st.keypad
        for w in panel.winfo_children():
            w.destroy()
        for i in range(1, 10):
            ttk.Button(panel, text=str(i), width=4, command=lambda v=i, bid=board_id: self._set_value_selected(bid, v)).grid(row=(i - 1) // 3, column=(i - 1) % 3, padx=2, pady=2)
        ttk.Button(panel, text="→", width=4, command=lambda bid=board_id: self._solve(bid)).grid(row=3, column=0, padx=2, pady=2)
        ttk.Button(panel, text="0", width=4, command=lambda bid=board_id: self._set_value_selected(bid, 0)).grid(row=3, column=1, padx=2, pady=2)
        ttk.Button(panel, text="⌫", width=4, command=lambda bid=board_id: self._set_value_selected(bid, 0)).grid(row=3, column=2, padx=2, pady=2)

    def _cell_from_xy(self, board_id: str, x: int, y: int) -> Optional[Tuple[int, int]]:
        st = self.board_tabs[board_id]
        canvas = st.widgets["canvas"]
        n = len(st.grid)
        if n == 0:
            return None
        cell = min(canvas.winfo_width(), canvas.winfo_height()) / n
        x0 = (canvas.winfo_width() - cell * n) / 2
        y0 = (canvas.winfo_height() - cell * n) / 2
        c = int((x - x0) // cell)
        r = int((y - y0) // cell)
        if 0 <= r < n and 0 <= c < n:
            return r, c
        return None

    def _is_shift_pressed(self, event) -> bool:
        return bool(event.state & 0x0001)

    def _click_cell(self, event, board_id: str, add: bool = False):
        st = self.board_tabs[board_id]
        cell = self._cell_from_xy(board_id, event.x, event.y)
        if not cell:
            return
        st.active = cell
        st.drag_anchor = cell
        if add:
            st.selected.add(cell)
        else:
            st.selected = {cell}
        self._redraw(board_id)

    def _drag_select(self, event, board_id: str):
        st = self.board_tabs[board_id]
        if st.drag_anchor is None:
            return
        cell = self._cell_from_xy(board_id, event.x, event.y)
        if not cell:
            return
        r1, c1 = st.drag_anchor
        r2, c2 = cell
        selected = set()
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                selected.add((r, c))
        st.selected = selected
        st.active = cell
        self._redraw(board_id)

    def _finish_drag(self, board_id: str):
        self.board_tabs[board_id].drag_anchor = None

    def _find_conflicts(self, st: BoardState) -> Set[Tuple[int, int]]:
        n = len(st.grid)
        conflicts: Set[Tuple[int, int]] = set()
        sqrt_n = int(n**0.5)
        has_square = sqrt_n * sqrt_n == n

        def dupes(cells):
            seen = {}
            for r, c in cells:
                v = st.grid[r][c]
                if not v:
                    continue
                if v in seen:
                    conflicts.add((r, c))
                    conflicts.add(seen[v])
                else:
                    seen[v] = (r, c)

        for i in range(n):
            dupes([(i, c) for c in range(n)])
            dupes([(r, i) for r in range(n)])
        if has_square:
            for br in range(0, n, sqrt_n):
                for bc in range(0, n, sqrt_n):
                    dupes([(r, c) for r in range(br, br + sqrt_n) for c in range(bc, bc + sqrt_n)])
        if st.mode == "diagonal":
            dupes([(i, i) for i in range(n)])
            dupes([(i, n - i - 1) for i in range(n)])
        if st.mode == "hyper" and n >= 9:
            s, o = n // 3, n // 6
            for br, bc in [(o, o), (o, o + s), (o + s, o), (o + s, o + s)]:
                dupes([(r, c) for r in range(br, br + s) for c in range(bc, bc + s)])
        if st.mode == "killer":
            for cage in st.cages:
                vals = [st.grid[r][c] for r, c in cage.cells if st.grid[r][c] != 0]
                if len(vals) != len(set(vals)):
                    conflicts.update(cage.cells)
                if sum(vals) > cage.total:
                    conflicts.update(cage.cells)
                if len(vals) == len(cage.cells) and sum(vals) != cage.total:
                    conflicts.update(cage.cells)
        return conflicts

    def _set_value_selected(self, board_id: str, value: int):
        st = self.board_tabs[board_id]
        if not st.selected:
            st.selected = {st.active}
        backup = [row[:] for row in st.grid]
        for r, c in st.selected:
            st.grid[r][c] = value
        if self._find_conflicts(st):
            st.grid = backup
            self.status_var.set(self.t("status_conflict"))
            self.status_label.configure(foreground="#b00020")
        else:
            self.status_var.set(self.t("status_ready"))
            self.status_label.configure(foreground="#1b5e20")
        self._redraw(board_id)

    def _clear_selection_or_all(self, board_id: str):
        st = self.board_tabs[board_id]
        if st.selected:
            for r, c in st.selected:
                st.grid[r][c] = 0
        else:
            for r in range(len(st.grid)):
                for c in range(len(st.grid)):
                    st.grid[r][c] = 0
        self._redraw(board_id)

    def _on_key(self, event):
        bid = self._current_board_id()
        if not bid:
            return
        st = self.board_tabs[bid]
        if event.keysym in ("Delete", "BackSpace"):
            self._set_value_selected(bid, 0)
            return
        if event.keysym in ("Up", "Down", "Left", "Right"):
            r, c = st.active
            n = len(st.grid)
            drdc = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
            dr, dc = drdc[event.keysym]
            st.active = ((r + dr) % n, (c + dc) % n)
            st.selected = {st.active}
            self._redraw(bid)
            return
        ch = event.char.upper()
        symbols = SYMBOLS[: len(st.grid)]
        if ch in symbols:
            self._set_value_selected(bid, symbols.index(ch) + 1)
        elif ch == "0":
            self._set_value_selected(bid, 0)

    def _solve(self, board_id: str):
        st = self.board_tabs[board_id]
        if st.solve_future and not st.solve_future.done():
            return
        cfg = SolveConfig(
            size=len(st.grid),
            use_subgrid=True,
            diagonal=st.mode == "diagonal",
            hyper=st.mode == "hyper",
            killer=st.mode == "killer",
            cages=st.cages,
            timeout_sec=float(st.widgets["timeout_var"].get()),
        )
        solver = SudokuSolver(cfg)
        st.solve_future = self.executor.submit(solver.solve, [row[:] for row in st.grid])
        self.status_var.set(self.t("status_solving"))
        self.status_label.configure(foreground="#ef6c00")
        self.root.after(100, lambda bid=board_id: self._poll_solve(bid))

    def _poll_solve(self, board_id: str):
        st = self.board_tabs[board_id]
        if not st.solve_future:
            return
        if not st.solve_future.done():
            self.root.after(100, lambda bid=board_id: self._poll_solve(bid))
            return
        res = st.solve_future.result()
        if res.solved:
            st.grid = res.grid
            self.status_var.set(f"{self.t('solve')} OK ({res.elapsed_sec:.2f}s)")
            self.status_label.configure(foreground="#1b5e20")
        else:
            self.status_var.set(res.message)
            self.status_label.configure(foreground="#b00020")
        self._redraw(board_id)

    def _configure_killer_text(self, board_id: str):
        st = self.board_tabs[board_id]
        init = ";".join(f"{c.total}:" + ",".join(f"r{r+1}c{cc+1}" for r, cc in c.cells) for c in st.cages)
        editor = KillerEditor(self.root, init, self.t("killer_cfg"), self.t("killer_help"))
        self.root.wait_window(editor)
        if editor.result is None:
            return
        try:
            st.cages = parse_cages(editor.result)
            self.status_var.set(f"Cages: {len(st.cages)}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _create_killer_cage_from_selection(self, board_id: str):
        st = self.board_tabs[board_id]
        if st.mode != "killer":
            messagebox.showinfo("Info", "Switch mode to Killer first")
            return
        if not st.selected:
            return
        value = simpledialog.askinteger("Killer", "Enter cage sum")
        if value is None:
            return
        st.cages = tuple(list(st.cages) + [Cage(total=value, cells=tuple(sorted(st.selected)))])
        self.status_var.set(f"Cages: {len(st.cages)}")

    def _redraw(self, board_id: str):
        st = self.board_tabs[board_id]
        canvas: tk.Canvas = st.widgets["canvas"]
        canvas.delete("all")
        n = len(st.grid)
        if n == 0:
            return
        conflicts = self._find_conflicts(st)
        w, h = canvas.winfo_width(), canvas.winfo_height()
        cell = min(w, h) / n
        x0 = (w - cell * n) / 2
        y0 = (h - cell * n) / 2
        sqrt_n = int(n**0.5)
        has_square = sqrt_n * sqrt_n == n

        for r, c in st.selected:
            canvas.create_rectangle(x0 + c * cell, y0 + r * cell, x0 + (c + 1) * cell, y0 + (r + 1) * cell, fill="#E3F2FD", width=0)

        for r in range(n):
            for c in range(n):
                x1, y1 = x0 + c * cell, y0 + r * cell
                x2, y2 = x1 + cell, y1 + cell
                canvas.create_rectangle(x1, y1, x2, y2, outline="#BDBDBD")
                v = st.grid[r][c]
                if v:
                    color = "#c62828" if (r, c) in conflicts else "#0d47a1"
                    canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=SYMBOLS[v - 1], fill=color, font=("Segoe UI", max(8, int(cell * 0.45)), "bold"))

        ar, ac = st.active
        canvas.create_rectangle(x0 + ac * cell, y0 + ar * cell, x0 + (ac + 1) * cell, y0 + (ar + 1) * cell, outline="#1565c0", width=3)
        for i in range(n + 1):
            width = 3 if has_square and i % sqrt_n == 0 else 1
            canvas.create_line(x0 + i * cell, y0, x0 + i * cell, y0 + n * cell, width=width)
            canvas.create_line(x0, y0 + i * cell, x0 + n * cell, y0 + i * cell, width=width)

    def _save_image(self, board_id: str):
        st = self.board_tabs[board_id]
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self._draw_grid_to_image(st.grid, path)

    def _draw_grid_to_image(self, grid: List[List[int]], path: str):
        n = len(grid)
        size_px = max(1200, n * 70)
        margin = max(40, size_px // 24)
        cell = (size_px - margin * 2) / n
        img = Image.new("RGB", (size_px, size_px), "white")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", max(18, int(cell * 0.62)))
        except OSError:
            font = ImageFont.load_default()

        sqrt_n = int(n**0.5)
        has_square = sqrt_n * sqrt_n == n
        for i in range(n + 1):
            line_w = 4 if has_square and i % sqrt_n == 0 else 2
            x = margin + i * cell
            y = margin + i * cell
            draw.line((x, margin, x, size_px - margin), fill="black", width=line_w)
            draw.line((margin, y, size_px - margin, y), fill="black", width=line_w)

        for r in range(n):
            for c in range(n):
                v = grid[r][c]
                if not v:
                    continue
                text = SYMBOLS[v - 1]
                bbox = draw.textbbox((0, 0), text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                x = margin + c * cell + (cell - tw) / 2
                y = margin + r * cell + (cell - th) / 2
                draw.text((x, y), text, fill="black", font=font)
        img.save(path)


def _bits(mask: int):
    while mask:
        b = mask & -mask
        mask -= b
        yield b


def main():
    root = tk.Tk()
    SudokuApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
