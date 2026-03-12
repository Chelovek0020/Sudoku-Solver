#include <FL/Fl.H>
#include <FL/Fl_Window.H>
#include <FL/Fl_Button.H>
#include <FL/Fl_Input.H>
#include <FL/Fl_Box.H>
#include <FL/fl_ask.H>
#include <FL/Fl_Group.H>
#include <FL/Fl_Round_Button.H>
#include <FL/fl_draw.H>
#include <vector>
#include <string>
#include <cstring>
#include <iostream>
#include <cmath>
#include <fstream>

#ifdef _WIN32
#include <windows.h>
#include "resource.h" // Для иконки
#endif

// Кроссплатформенная функция для открытия URL
void open_url(const char* url) {
#ifdef _WIN32
    system(("start " + std::string(url)).c_str());
#elif __APPLE__
    system(("open " + std::string(url)).c_str());
#else
    system(("xdg-open " + std::string(url)).c_str());
#endif
}

// Языковые строки
struct Language {
    const char* title;
    const char* solve;
    const char* clear;
    const char* support_author;
    const char* success_message;
    const char* error_message;
    const char* language;
    const char* clear_cell;
};

Language russian = {
    "Решатель Судоку",
    "Решить",
    "Очистить",
    "Поддержать автора",
    "Судоку успешно решено!",
    "Эта головоломка не имеет решения!",
    "Язык",
    "Очистить"
};

Language english = {
    "Sudoku Solver",
    "Solve",
    "Clear",
    "Support Author",
    "Sudoku solved successfully!",
    "This puzzle has no solution!",
    "Language",
    "Clear"
};

// Класс для решения судоку
class SudokuSolverLogic {
public:
    // Решает судоку на месте. Возвращает true, если решение найдено.
    bool solve(std::vector<std::vector<int>>& board) {
        return backtrack(board);
    }

private:
    bool backtrack(std::vector<std::vector<int>>& board) {
        for (int row = 0; row < 9; ++row) {
            for (int col = 0; col < 9; ++col) {
                if (board[row][col] == 0) {
                    for (int num = 1; num <= 9; ++num) {
                        if (isValid(board, row, col, num)) {
                            board[row][col] = num;
                            if (backtrack(board))
                                return true;
                            board[row][col] = 0;
                        }
                    }
                    return false; // Нет допустимого числа
                }
            }
        }
        return true; // Всё заполнено корректно
    }

    bool isValid(const std::vector<std::vector<int>>& board, int row, int col, int num) {
        // Проверка строки
        for (int i = 0; i < 9; ++i) {
            if (board[row][i] == num)
                return false;
        }
        
        // Проверка столбца
        for (int i = 0; i < 9; ++i) {
            if (board[i][col] == num)
                return false;
        }

        // Проверка 3x3 блока
        int startRow = (row / 3) * 3;
        int startCol = (col / 3) * 3;
        for (int i = 0; i < 3; ++i) {
            for (int j = 0; j < 3; ++j) {
                if (board[startRow + i][startCol + j] == num)
                    return false;
            }
        }

        return true;
    }
};

// Анимированная кнопка
class AnimatedButton : public Fl_Button {
private:
    double scale_factor;
    bool is_hovered;
    bool animating;
    
public:
    AnimatedButton(int x, int y, int w, int h, const char* label = 0) 
        : Fl_Button(x, y, w, h, label), scale_factor(1.0), is_hovered(false), animating(false) {
        box(FL_ROUND_UP_BOX);
        labelsize(14);
        labelfont(FL_HELVETICA_BOLD);
    }
    
    void draw() override {
        if (animating) {
            int new_w = (int)(w() * scale_factor);
            int new_h = (int)(h() * scale_factor);
            int new_x = x() + (w() - new_w) / 2;
            int new_y = y() + (h() - new_h) / 2;
            
            // Рисуем с масштабированием
            fl_push_clip(x() - 5, y() - 5, w() + 10, h() + 10);
            
            // Сохраняем оригинальные размеры
            int orig_x = x(), orig_y = y(), orig_w = w(), orig_h = h();
            
            // Временно изменяем размеры для отрисовки
            resize(new_x, new_y, new_w, new_h);
            Fl_Button::draw();
            resize(orig_x, orig_y, orig_w, orig_h);
            
            fl_pop_clip();
        } else {
            Fl_Button::draw();
        }
    }
    
    int handle(int event) override {
        switch(event) {
            case FL_ENTER:
                if (!is_hovered) {
                    is_hovered = true;
                    animate_to(1.05);
                }
                return 1;
            case FL_LEAVE:
                if (is_hovered) {
                    is_hovered = false;
                    animate_to(1.0);
                }
                return 1;
            default:
                return Fl_Button::handle(event);
        }
    }
    
private:
    void animate_to(double target) {
        if (fabs(scale_factor - target) < 0.01) {
            animating = false;
            return;
        }
        
        animating = true;
        scale_factor += (target - scale_factor) * 0.4;
        redraw();
        
        if (fabs(scale_factor - target) > 0.01) {
            Fl::add_timeout(0.02, animate_callback, this);
        } else {
            animating = false;
        }
    }
    
    static void animate_callback(void* data) {
        AnimatedButton* btn = (AnimatedButton*)data;
        double target = btn->is_hovered ? 1.05 : 1.0;
        btn->animate_to(target);
    }
};

// Улучшенная ячейка судоку
class SudokuCell : public Fl_Box {
private:
    int row, col;
    int cell_value;
    bool is_conflict;
    bool is_selected;
    bool is_readonly;
    char label_buffer[2]; // КРИТИЧНО: каждая ячейка имеет свой буфер!
    
public:
    SudokuCell(int x, int y, int w, int h, int r, int c) 
        : Fl_Box(x, y, w, h), row(r), col(c), cell_value(0), 
          is_conflict(false), is_selected(false), is_readonly(false) {
        box(FL_FLAT_BOX);
        labelfont(FL_HELVETICA_BOLD);
        labelsize(20);
        align(FL_ALIGN_CENTER);
        label_buffer[0] = '\0';
        label_buffer[1] = '\0';
    }
    
    void draw() override {
        // Цвет фона
        if (is_selected) {
            color(fl_rgb_color(144, 238, 144)); // Светло-зеленый
        } else if (is_conflict) {
            color(fl_rgb_color(255, 182, 193)); // Светло-красный
        } else if (is_readonly) {
            color(fl_rgb_color(240, 240, 240)); // Серый для предустановленных
        } else {
            color(FL_WHITE);
        }
        
        Fl_Box::draw();
        
        // Рисуем обычные границы
        fl_color(FL_BLACK);
        fl_line_style(FL_SOLID, 1);
        fl_rect(x(), y(), w(), h());
        
        // Рисуем ТОЛСТЫЕ границы для 3x3 блоков
        fl_line_style(FL_SOLID, 3);
        
        // Верхняя граница блока
        if (row % 3 == 0) {
            fl_line(x(), y(), x() + w(), y());
        }
        
        // Левая граница блока
        if (col % 3 == 0) {
            fl_line(x(), y(), x(), y() + h());
        }
        
        // Нижняя граница последнего ряда
        if (row == 8) {
            fl_line(x(), y() + h() - 1, x() + w(), y() + h() - 1);
        }
        
        // Правая граница последнего столбца
        if (col == 8) {
            fl_line(x() + w() - 1, y(), x() + w() - 1, y() + h());
        }
        
        // Правая граница блока (каждый 3-й столбец)
        if ((col + 1) % 3 == 0 && col < 8) {
            fl_line(x() + w() - 1, y(), x() + w() - 1, y() + h());
        }
        
        // Нижняя граница блока (каждый 3-й ряд)
        if ((row + 1) % 3 == 0 && row < 8) {
            fl_line(x(), y() + h() - 1, x() + w(), y() + h() - 1);
        }
        
        fl_line_style(FL_SOLID, 1); // Возвращаем обычную толщину
    }
    
    int handle(int event) override {
        if (event == FL_PUSH) {
            do_callback();
            return 1;
        }
        return Fl_Box::handle(event);
    }
    
    void set_conflict(bool conflict) {
        if (is_conflict != conflict) {
            is_conflict = conflict;
            damage(FL_DAMAGE_ALL); // Плавное обновление
        }
    }
    
    void set_selected(bool selected) {
        if (is_selected != selected) {
            is_selected = selected;
            damage(FL_DAMAGE_ALL); // Плавное обновление
        }
    }
    
    void set_readonly(bool readonly) {
        if (is_readonly != readonly) {
            is_readonly = readonly;
            damage(FL_DAMAGE_ALL); // Плавное обновление
        }
    }
    
    bool get_readonly() const {
        return is_readonly;
    }
    
    int get_value() const {
        return cell_value;
    }
    
    void set_value(int v) {
        if (cell_value != v) {
            cell_value = v;
            if (v == 0) {
                label_buffer[0] = '\0';
                label("");
            } else {
                sprintf(label_buffer, "%d", v);
                label(label_buffer); // Используем собственный буфер!
            }
            damage(FL_DAMAGE_ALL); // Плавное обновление
        }
    }
    
    int get_row() const { return row; }
    int get_col() const { return col; }
};

// Окно с градиентным фоном
class GradientWindow : public Fl_Window {
public:
    GradientWindow(int w, int h, const char* title) : Fl_Window(w, h, title) {
        color(fl_rgb_color(245, 245, 250));
        
#ifdef _WIN32
        // Устанавливаем иконку для Windows
        HICON icon = LoadIcon(GetModuleHandle(NULL), MAKEINTRESOURCE(IDI_ICON1));
        if (icon) {
            this->icon((char*)icon);
        }
#endif
    }
    
    void draw() override {
        // Рисуем градиентный фон
        for (int y = 0; y < h(); y++) {
            double ratio = (double)y / h();
            int r = (int)(240 + ratio * 15);  // От 240 до 255
            int g = (int)(240 + ratio * 15);  // От 240 до 255
            int b = (int)(245 + ratio * 10);  // От 245 до 255
            
            fl_color(fl_rgb_color(r, g, b));
            fl_line(0, y, w(), y);
        }
        
        // Рисуем дочерние элементы
        Fl_Window::draw();
    }
};

class SudokuSolver : public GradientWindow {
private:
    SudokuCell* cells[9][9];
    AnimatedButton* solve_btn;
    AnimatedButton* clear_btn;
    AnimatedButton* support_btn;
    AnimatedButton* number_btns[10]; // 1-9 и 0 для очистки
    Fl_Round_Button* lang_ru;
    Fl_Round_Button* lang_en;
    
    Language* current_lang;
    bool is_russian;
    SudokuCell* selected_cell;
    SudokuSolverLogic solver_logic;
    
    // Проверка конфликтов при попытке ввода
    bool would_create_conflict(int row, int col, int num) {
        if (num == 0) return false; // Очистка не создает конфликтов
        
        // Проверка строки
        for (int x = 0; x < 9; x++) {
            if (x != col && cells[row][x]->get_value() == num) {
                return true;
            }
        }
        
        // Проверка столбца
        for (int x = 0; x < 9; x++) {
            if (x != row && cells[x][col]->get_value() == num) {
                return true;
            }
        }
        
        // Проверка 3x3 квадрата
        int start_row = row - row % 3;
        int start_col = col - col % 3;
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                int check_row = i + start_row;
                int check_col = j + start_col;
                if ((check_row != row || check_col != col) && 
                    cells[check_row][check_col]->get_value() == num) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    void highlight_conflicts(int row, int col, int num) {
        // Сбрасываем все конфликты
        for (int i = 0; i < 9; i++) {
            for (int j = 0; j < 9; j++) {
                cells[i][j]->set_conflict(false);
            }
        }
        
        if (num == 0) return; // Нет конфликтов при очистке
        
        // Подсвечиваем конфликтующие ячейки красным
        bool has_conflicts = false;
        
        // Проверка строки
        for (int x = 0; x < 9; x++) {
            if (x != col && cells[row][x]->get_value() == num) {
                cells[row][x]->set_conflict(true);
                has_conflicts = true;
            }
        }
        
        // Проверка столбца
        for (int x = 0; x < 9; x++) {
            if (x != row && cells[x][col]->get_value() == num) {
                cells[x][col]->set_conflict(true);
                has_conflicts = true;
            }
        }
        
        // Проверка 3x3 квадрата
        int start_row = row - row % 3;
        int start_col = col - col % 3;
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                int check_row = i + start_row;
                int check_col = j + start_col;
                if ((check_row != row || check_col != col) && 
                    cells[check_row][check_col]->get_value() == num) {
                    cells[check_row][check_col]->set_conflict(true);
                    has_conflicts = true;
                }
            }
        }
        
        // Подсвечиваем целевую ячейку, если есть конфликты
        if (has_conflicts) {
            cells[row][col]->set_conflict(true);
        }
    }
    
    void validate_grid() {
        // Сбрасываем все конфликты
        for (int i = 0; i < 9; i++) {
            for (int j = 0; j < 9; j++) {
                cells[i][j]->set_conflict(false);
            }
        }
    }
    
    static void solve_cb(Fl_Widget*, void* data) {
        SudokuSolver* solver = (SudokuSolver*)data;
        solver->solve();
    }
    
    static void clear_cb(Fl_Widget*, void* data) {
        SudokuSolver* solver = (SudokuSolver*)data;
        solver->clear_grid();
    }
    
    static void support_cb(Fl_Widget*, void*) {
        open_url("https://www.donationalerts.com/r/supermine_");
    }
    
    static void number_cb(Fl_Widget* w, void* data) {
        SudokuSolver* solver = (SudokuSolver*)data;
        AnimatedButton* btn = (AnimatedButton*)w;
        int number = 0;
        if (btn->label() && strlen(btn->label()) > 0) {
            if (strcmp(btn->label(), "Очистить") == 0 || strcmp(btn->label(), "Clear") == 0) {
                number = 0;
            } else {
                number = atoi(btn->label());
            }
        }
        solver->input_number(number);
    }
    
    static void cell_cb(Fl_Widget* w, void* data) {
        SudokuSolver* solver = (SudokuSolver*)data;
        SudokuCell* cell = (SudokuCell*)w;
        solver->select_cell(cell);
    }
    
    static void lang_cb(Fl_Widget*, void* data) {
        SudokuSolver* solver = (SudokuSolver*)data;
        solver->switch_language();
    }
    
public:
    SudokuSolver() : GradientWindow(800, 600, "Sudoku Solver"), 
                     is_russian(true), selected_cell(nullptr) {
        current_lang = &russian;
        
        // Создаем сетку судоку
        int grid_start_x = 50;
        int grid_start_y = 80;
        int cell_size = 40;
        
        for (int i = 0; i < 9; i++) {
            for (int j = 0; j < 9; j++) {
                int x = grid_start_x + j * cell_size;
                int y = grid_start_y + i * cell_size;
                cells[i][j] = new SudokuCell(x, y, cell_size, cell_size, i, j);
                cells[i][j]->callback(cell_cb, this);
            }
        }
        
        // Кнопки управления (сделал шире)
        int btn_x = 450;
        solve_btn = new AnimatedButton(btn_x, 120, 140, 45, current_lang->solve);
        solve_btn->callback(solve_cb, this);
        solve_btn->color(fl_rgb_color(76, 175, 80));
        solve_btn->labelcolor(FL_WHITE);
        
        clear_btn = new AnimatedButton(btn_x, 180, 140, 45, current_lang->clear);
        clear_btn->callback(clear_cb, this);
        clear_btn->color(fl_rgb_color(244, 67, 54));
        clear_btn->labelcolor(FL_WHITE);
        
        // Кнопки с цифрами (исправил - теперь от 1 до 9)
        int num_start_x = btn_x;
        int num_start_y = 260;
        int num_btn_size = 35;
        int num_spacing = 40;
        
        // Создаем статические строки для меток кнопок
        static char* button_labels[10];
        for (int i = 1; i <= 9; i++) {
            button_labels[i] = new char[2];
            sprintf(button_labels[i], "%d", i);
        }
        
        for (int i = 1; i <= 9; i++) {
            int row = (i - 1) / 3;
            int col = (i - 1) % 3;
            int x = num_start_x + col * num_spacing;
            int y = num_start_y + row * num_spacing;
            
            number_btns[i] = new AnimatedButton(x, y, num_btn_size, num_btn_size, button_labels[i]);
            number_btns[i]->callback(number_cb, this);
            number_btns[i]->color(fl_rgb_color(63, 81, 181));
            number_btns[i]->labelcolor(FL_WHITE);
            number_btns[i]->labelsize(16);
        }
        
        // Кнопка очистки ячейки (сделал шире)
        number_btns[0] = new AnimatedButton(btn_x, 400, 140, 35, current_lang->clear_cell);
        number_btns[0]->callback(number_cb, this);
        number_btns[0]->color(fl_rgb_color(158, 158, 158));
        number_btns[0]->labelcolor(FL_WHITE);
        
        // Кнопка поддержки автора (сделал шире)
        support_btn = new AnimatedButton(btn_x, 520, 140, 35, current_lang->support_author);
        support_btn->callback(support_cb, this);
        support_btn->color(fl_rgb_color(255, 193, 7));
        support_btn->labelcolor(FL_BLACK);
        support_btn->labelsize(12);
        
        // Переключатели языка
        lang_ru = new Fl_Round_Button(btn_x, 50, 50, 25, "RU");
        lang_ru->type(FL_RADIO_BUTTON);
        lang_ru->value(1);
        lang_ru->callback(lang_cb, this);
        lang_ru->labelsize(12);
        
        lang_en = new Fl_Round_Button(btn_x + 60, 50, 50, 25, "EN");
        lang_en->type(FL_RADIO_BUTTON);
        lang_en->callback(lang_cb, this);
        lang_en->labelsize(12);
        
        end();
        
        // Устанавливаем фокус на окно для обработки клавиатуры
        when(FL_WHEN_CHANGED);
    }
    
    int handle(int event) override {
        if (event == FL_KEYDOWN && selected_cell) {
            int key = Fl::event_key();
            if (key >= '1' && key <= '9') {
                input_number(key - '0');
                return 1;
            } else if (key == FL_Delete || key == FL_BackSpace || key == '0') {
                input_number(0);
                return 1;
            }
        }
        return GradientWindow::handle(event);
    }
    
    void select_cell(SudokuCell* cell) {
        // Убираем выделение с других ячеек
        for (int i = 0; i < 9; i++) {
            for (int j = 0; j < 9; j++) {
                cells[i][j]->set_selected(false);
            }
        }
        
        // Выделяем выбранную ячейку
        cell->set_selected(true);
        selected_cell = cell;
        validate_grid();
    }
    
    void solve() {
        // Создаем двумерный массив для алгоритма
        std::vector<std::vector<int>> board(9, std::vector<int>(9, 0));
        
        // Заполняем массив текущими значениями
        for (int i = 0; i < 9; i++) {
            for (int j = 0; j < 9; j++) {
                board[i][j] = cells[i][j]->get_value();
            }
        }
        
        // Решаем судоку
        if (solver_logic.solve(board)) {
            // Заполняем решение в интерфейс
            for (int i = 0; i < 9; i++) {
                for (int j = 0; j < 9; j++) {
                    cells[i][j]->set_value(board[i][j]);
                    if (board[i][j] != 0) {
                        cells[i][j]->set_readonly(true);
                    }
                }
            }
            fl_message("%s", current_lang->success_message);
        } else {
            fl_alert("%s", current_lang->error_message);
        }
        validate_grid();
    }
    
    void clear_grid() {
        for (int i = 0; i < 9; i++) {
            for (int j = 0; j < 9; j++) {
                cells[i][j]->set_value(0);
                cells[i][j]->set_conflict(false);
                cells[i][j]->set_selected(false);
                cells[i][j]->set_readonly(false);
            }
        }
        selected_cell = nullptr;
    }
    
    void input_number(int number) {
        if (selected_cell && !selected_cell->get_readonly()) {
            int row = selected_cell->get_row();
            int col = selected_cell->get_col();
            
            // Проверяем, создаст ли это конфликт
            if (would_create_conflict(row, col, number)) {
                // Подсвечиваем конфликтующие ячейки красным
                highlight_conflicts(row, col, number);
                // НЕ устанавливаем значение
                return;
            }
            
            // Если конфликта нет, устанавливаем значение
            selected_cell->set_value(number);
            validate_grid();
        }
    }
    
    void switch_language() {
        is_russian = lang_ru->value();
        current_lang = is_russian ? &russian : &english;
        
        // Обновляем текст кнопок
        solve_btn->label(current_lang->solve);
        clear_btn->label(current_lang->clear);
        support_btn->label(current_lang->support_author);
        number_btns[0]->label(current_lang->clear_cell);
        
        label(current_lang->title);
        redraw();
    }
};

int main() {
    Fl::scheme("gtk+");
    SudokuSolver* solver = new SudokuSolver();
    solver->show();
    return Fl::run();
}