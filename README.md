# Sudoku Solver (Classic / Killer / Hyper / Diagonal)

Кроссплатформенное desktop-приложение на Python + Tkinter для решения судоку с удобным GUI.

## Возможности

- Размер поля от **3x3** до **30x30**.
- Поддержка режимов:
  - Classic (строки, столбцы, классические блоки при квадратном размере);
  - Diagonal Sudoku;
  - Hyper Sudoku;
  - Killer Sudoku (ввод клеток-кейджей и суммы).
- Проверка правил во время ввода.
- Решение в отдельном потоке (UI не зависает).
- Сохранение результата в PNG.
- Кнопка «Поддержать автора» с переходом на DonationAlerts.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Сборка в один файл (локально)

```bash
pip install pyinstaller -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --name SudokuSolver --icon assets/app.ico src/main.py
```

Готовый файл будет в `dist/`.

## Killer-формат клеток

Формат:

```text
15:r1c1,r1c2;10:r2c1,r3c1
```

Где `15` и `10` — суммы для клеток, `rXcY` — координаты (с 1).
