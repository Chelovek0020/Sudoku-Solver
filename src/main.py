from __future__ import annotations

import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from solver import Cage, SolveConfig, SudokuSolver, parse_cages

SYMBOLS = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class SudokuApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sudoku Solver")
        self.root.geometry("1300x900")
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.solve_future: Optional[Future] = None

        self.size_var = tk.IntVar(value=9)
        self.timeout_var = tk.DoubleVar(value=15.0)
        self.use_subgrid_var = tk.BooleanVar(value=True)
        self.diag_var = tk.BooleanVar(value=False)
        self.hyper_var = tk.BooleanVar(value=False)
        self.killer_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Готово")

        self.grid_data: List[List[int]] = []
        self.active_cell = (0, 0)
        self.cages: Tuple[Cage, ...] = ()

        self._build_ui()
        self._reset_grid()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(left, bg="white", highlightthickness=1, highlightbackground="#CCCCCC")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._click_cell)
        self.root.bind("<Key>", self._on_key)
        self.canvas.bind("<Configure>", lambda _e: self.redraw())

        right = ttk.Frame(main, width=300)
        right.pack(side="right", fill="y", padx=(10, 0))

        ttk.Label(right, text="Размер поля").pack(anchor="w")
        ttk.Spinbox(right, from_=3, to=30, textvariable=self.size_var, width=8).pack(anchor="w", pady=(0, 6))

        ttk.Checkbutton(right, text="Классические блоки", variable=self.use_subgrid_var, command=self.redraw).pack(anchor="w")
        ttk.Checkbutton(right, text="Diagonal Sudoku", variable=self.diag_var, command=self.redraw).pack(anchor="w")
        ttk.Checkbutton(right, text="Hyper Sudoku", variable=self.hyper_var, command=self.redraw).pack(anchor="w")
        ttk.Checkbutton(right, text="Killer Sudoku", variable=self.killer_var).pack(anchor="w", pady=(0, 6))

        ttk.Button(right, text="Настроить Killer-клетки", command=self._configure_cages).pack(fill="x", pady=(0, 8))

        ttk.Label(right, text="Таймаут решения (сек)").pack(anchor="w")
        ttk.Spinbox(right, from_=1, to=120, increment=1, textvariable=self.timeout_var, width=8).pack(anchor="w", pady=(0, 10))

        ttk.Button(right, text="Создать поле", command=self._reset_grid).pack(fill="x", pady=2)
        ttk.Button(right, text="Решить", command=self.solve).pack(fill="x", pady=2)
        ttk.Button(right, text="Удалить символ", command=lambda: self._set_value(self.active_cell[0], self.active_cell[1], 0)).pack(fill="x", pady=2)
        ttk.Button(right, text="Очистить всё", command=self._clear_all).pack(fill="x", pady=2)
        ttk.Button(right, text="Сохранить как изображение", command=self.save_image).pack(fill="x", pady=2)

        ttk.Label(right, text="Панель ввода").pack(anchor="w", pady=(12, 4))
        panel = ttk.Frame(right)
        panel.pack(fill="x")
        self.keypad_container = panel
        self._rebuild_keypad()

        ttk.Separator(self.root, orient="horizontal").pack(fill="x")
        bottom = ttk.Frame(self.root, padding=(10, 6))
        bottom.pack(fill="x")
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left")
        link = ttk.Button(bottom, text="Поддержать автора", command=self._open_support)
        link.pack(side="right")

    def _open_support(self):
        import webbrowser

        webbrowser.open("https://www.donationalerts.com/r/supermine_")

    def _configure_cages(self) -> None:
        existing = ";".join(
            f"{c.total}:" + ",".join(f"r{r+1}c{cc+1}" for r, cc in c.cells)
            for c in self.cages
        )
        text = simpledialog.askstring(
            "Killer клетки",
            "Формат: 15:r1c1,r1c2;10:r2c1,r3c1",
            initialvalue=existing,
        )
        if text is None:
            return
        try:
            self.cages = parse_cages(text)
            self.status_var.set(f"Killer клеток: {len(self.cages)}")
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Некорректный формат: {exc}")

    def _rebuild_keypad(self):
        for w in self.keypad_container.winfo_children():
            w.destroy()
        n = self.size_var.get()
        cols = 6
        for idx in range(n):
            sym = SYMBOLS[idx]
            ttk.Button(self.keypad_container, text=sym, width=4, command=lambda v=idx + 1: self._set_value(self.active_cell[0], self.active_cell[1], v)).grid(row=idx // cols, column=idx % cols, padx=1, pady=1)

    def _reset_grid(self):
        n = self.size_var.get()
        self.grid_data = [[0 for _ in range(n)] for _ in range(n)]
        self.active_cell = (0, 0)
        self._rebuild_keypad()
        self.redraw()

    def _clear_all(self):
        for r in range(len(self.grid_data)):
            for c in range(len(self.grid_data)):
                self.grid_data[r][c] = 0
        self.redraw()

    def _click_cell(self, event):
        n = len(self.grid_data)
        if n == 0:
            return
        cell = min(self.canvas.winfo_width(), self.canvas.winfo_height()) / n
        x0 = (self.canvas.winfo_width() - cell * n) / 2
        y0 = (self.canvas.winfo_height() - cell * n) / 2
        c = int((event.x - x0) // cell)
        r = int((event.y - y0) // cell)
        if 0 <= r < n and 0 <= c < n:
            self.active_cell = (r, c)
            self.redraw()

    def _on_key(self, event):
        if not self.grid_data:
            return
        r, c = self.active_cell
        if event.keysym in ("BackSpace", "Delete"):
            self._set_value(r, c, 0)
            return
        char = event.char.upper()
        if char in SYMBOLS[: len(self.grid_data)]:
            self._set_value(r, c, SYMBOLS.index(char) + 1)
        elif event.keysym in ("Up", "Down", "Left", "Right"):
            n = len(self.grid_data)
            drdc = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
            dr, dc = drdc[event.keysym]
            self.active_cell = ((r + dr) % n, (c + dc) % n)
            self.redraw()

    def _set_value(self, r: int, c: int, v: int):
        if not (0 <= r < len(self.grid_data) and 0 <= c < len(self.grid_data)):
            return
        old = self.grid_data[r][c]
        self.grid_data[r][c] = v
        conflicts = self._find_conflicts()
        if conflicts:
            self.grid_data[r][c] = old
            self.status_var.set("Нарушение правил")
            messagebox.showwarning("Правила", "Такое значение нарушает правила выбранной версии")
        else:
            self.status_var.set("Готово")
        self.redraw()

    def _find_conflicts(self):
        n = len(self.grid_data)
        conflicts = set()
        sqrt_n = int(n ** 0.5)
        has_square = sqrt_n * sqrt_n == n

        def dupes(cells):
            seen = {}
            for rr, cc in cells:
                v = self.grid_data[rr][cc]
                if v == 0:
                    continue
                if v in seen:
                    conflicts.add((rr, cc))
                    conflicts.add(seen[v])
                else:
                    seen[v] = (rr, cc)

        for i in range(n):
            dupes([(i, c) for c in range(n)])
            dupes([(r, i) for r in range(n)])

        if self.use_subgrid_var.get() and has_square:
            for br in range(0, n, sqrt_n):
                for bc in range(0, n, sqrt_n):
                    dupes([(r, c) for r in range(br, br + sqrt_n) for c in range(bc, bc + sqrt_n)])

        if self.diag_var.get():
            dupes([(i, i) for i in range(n)])
            dupes([(i, n - 1 - i) for i in range(n)])

        if self.hyper_var.get() and n >= 9:
            s = n // 3
            o = n // 6
            for br, bc in [(o, o), (o, o + s), (o + s, o), (o + s, o + s)]:
                dupes([(r, c) for r in range(br, br + s) for c in range(bc, bc + s)])

        if self.killer_var.get() and self.cages:
            for cage in self.cages:
                vals = []
                used = set()
                for r, c in cage.cells:
                    if not (0 <= r < n and 0 <= c < n):
                        conflicts.add((0, 0))
                        continue
                    v = self.grid_data[r][c]
                    if v == 0:
                        continue
                    vals.append(v)
                    if v in used:
                        conflicts.update(cage.cells)
                    used.add(v)
                if sum(vals) > cage.total:
                    conflicts.update(cage.cells)
                if len(vals) == len(cage.cells) and sum(vals) != cage.total:
                    conflicts.update(cage.cells)
        return conflicts

    def redraw(self):
        self.canvas.delete("all")
        n = len(self.grid_data)
        if n == 0:
            return
        conflicts = self._find_conflicts()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cell = min(w, h) / n
        x0 = (w - cell * n) / 2
        y0 = (h - cell * n) / 2

        sqrt_n = int(n ** 0.5)
        has_square = sqrt_n * sqrt_n == n

        ar, ac = self.active_cell
        self.canvas.create_rectangle(x0 + ac * cell, y0 + ar * cell, x0 + (ac + 1) * cell, y0 + (ar + 1) * cell, fill="#EAF2FF", width=0)

        for r in range(n):
            for c in range(n):
                x1 = x0 + c * cell
                y1 = y0 + r * cell
                x2 = x1 + cell
                y2 = y1 + cell
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="#BBBBBB", width=1)
                v = self.grid_data[r][c]
                if v:
                    color = "#C62828" if (r, c) in conflicts else "#1A237E"
                    self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=SYMBOLS[v - 1], fill=color, font=("Segoe UI", max(8, int(cell * 0.38)), "bold"))

        for i in range(n + 1):
            width = 2
            if self.use_subgrid_var.get() and has_square and i % sqrt_n == 0:
                width = 3
            self.canvas.create_line(x0 + i * cell, y0, x0 + i * cell, y0 + n * cell, width=width)
            self.canvas.create_line(x0, y0 + i * cell, x0 + n * cell, y0 + i * cell, width=width)

    def solve(self):
        if self.solve_future and not self.solve_future.done():
            return
        n = len(self.grid_data)
        cfg = SolveConfig(
            size=n,
            use_subgrid=self.use_subgrid_var.get(),
            diagonal=self.diag_var.get(),
            hyper=self.hyper_var.get(),
            killer=self.killer_var.get(),
            cages=self.cages if self.killer_var.get() else (),
            timeout_sec=self.timeout_var.get(),
        )
        solver = SudokuSolver(cfg)
        grid_copy = [row[:] for row in self.grid_data]
        self.status_var.set("Решение...")
        self.solve_future = self.executor.submit(solver.solve, grid_copy)
        self._poll_solve()

    def _poll_solve(self):
        if not self.solve_future:
            return
        if not self.solve_future.done():
            self.root.after(120, self._poll_solve)
            return
        res = self.solve_future.result()
        if res.solved:
            self.grid_data = res.grid
            self.status_var.set(f"Решено за {res.elapsed_sec:.2f} сек")
        else:
            self.status_var.set(res.message or "Решение не найдено")
            messagebox.showinfo("Solver", res.message or "Решение не найдено")
        self.redraw()

    def save_image(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not path:
            return
        n = len(self.grid_data)
        size_px = max(800, n * 40)
        margin = 30
        cell = (size_px - 2 * margin) / n
        img = Image.new("RGB", (size_px, size_px), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        sqrt_n = int(n ** 0.5)
        has_square = sqrt_n * sqrt_n == n
        for i in range(n + 1):
            w = 3 if self.use_subgrid_var.get() and has_square and i % sqrt_n == 0 else 1
            x = margin + i * cell
            y = margin + i * cell
            draw.line((x, margin, x, size_px - margin), fill="black", width=w)
            draw.line((margin, y, size_px - margin, y), fill="black", width=w)

        for r in range(n):
            for c in range(n):
                v = self.grid_data[r][c]
                if not v:
                    continue
                text = SYMBOLS[v - 1]
                cx = margin + c * cell + cell / 2
                cy = margin + r * cell + cell / 2
                draw.text((cx - 4, cy - 6), text, fill="black", font=font)
        img.save(path)
        self.status_var.set(f"Сохранено: {Path(path).name}")


def main():
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
