# Sudoku Solver - Решатель Судоку

Современный решатель Судоку с графическим интерфейсом на C++ и FLTK 1.4.3.

## Особенности

- 🎯 **Интуитивный интерфейс**: Простая и понятная сетка 9x9
- 🌍 **Двуязычность**: Русский и английский языки
- 📚 **Интерактивное обучение**: Пошаговое руководство для новых пользователей
- ✅ **Валидация в реальном времени**: Подсветка конфликтующих ячеек
- 🔢 **Удобный ввод**: Клавиатура или кнопки с цифрами
- 🎨 **Современный дизайн**: Чистый и профессиональный интерфейс
- 💝 **Поддержка автора**: Встроенная ссылка на донаты

## Требования

- **FLTK 1.4.3** или новее
- **C++17** совместимый компилятор (GCC 7+, Clang 5+, MSVC 2017+)
- **CMake 3.15+** (опционально)

## Установка и компиляция

### Windows

#### Вариант 1: Использование MSYS2 (Рекомендуется)

1. **Установите MSYS2**:
   ```bash
   # Скачайте с https://www.msys2.org/ и установите
   ```

2. **Откройте MSYS2 MINGW64 терминал и установите зависимости**:
   ```bash
   pacman -Syu
   pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-fltk mingw-w64-x86_64-cmake mingw-w64-x86_64-make
   ```

3. **Соберите проект**:
   ```bash
   # Используя Makefile
   make

   # Или используя CMake
   mkdir build && cd build
   cmake .. -G "MinGW Makefiles"
   make
   ```

#### Вариант 2: Использование vcpkg

1. **Установите vcpkg**:
   ```bash
   git clone https://github.com/Microsoft/vcpkg.git
   cd vcpkg
   .\bootstrap-vcpkg.bat
   ```

2. **Установите FLTK**:
   ```bash
   .\vcpkg install fltk:x64-windows
   ```

3. **Соберите проект с CMake**:
   ```bash
   mkdir build && cd build
   cmake .. -DCMAKE_TOOLCHAIN_FILE=path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
   cmake --build .
   ```

#### Вариант 3: Сборка FLTK из исходников

1. **Скачайте FLTK 1.4.3**:
   ```bash
   # Скачайте с https://www.fltk.org/software.php
   # Распакуйте в C:\fltk-1.4.3
   ```

2. **Соберите FLTK**:
   ```bash
   cd C:\fltk-1.4.3
   mkdir build && cd build
   cmake .. -G "MinGW Makefiles" -DCMAKE_INSTALL_PREFIX=C:\fltk-1.4.3
   make && make install
   ```

3. **Соберите проект**:
   ```bash
   # Используйте build.bat или:
   g++ -std=c++17 -O2 -IC:\fltk-1.4.3\include -o SudokuSolver.exe main.cpp -LC:\fltk-1.4.3\lib -lfltk -lole32 -luuid -lcomctl32 -lwsock32 -mwindows
   ```

### Linux

#### Ubuntu/Debian

```bash
# Установите зависимости
sudo apt-get update
sudo apt-get install libfltk1.4-dev g++ make cmake

# Если FLTK 1.4 недоступен, соберите из исходников:
make build-fltk-from-source

# Соберите проект
make

# Или используя CMake
mkdir build && cd build
cmake ..
make
```

#### Fedora/CentOS/RHEL

```bash
# Fedora
sudo dnf install fltk-devel gcc-c++ make cmake

# CentOS/RHEL
sudo yum install fltk-devel gcc-c++ make cmake

# Соберите проект
make
```

#### Arch Linux

```bash
# Установите зависимости
sudo pacman -S fltk gcc make cmake

# Соберите проект
make
```

#### openSUSE

```bash
# Установите зависимости
sudo zypper install fltk-devel gcc-c++ make cmake

# Соберите проект
make
```

#### Alpine Linux

```bash
# Установите зависимости
sudo apk add fltk-dev g++ make cmake

# Соберите проект
make
```

### macOS

#### Используя Homebrew

```bash
# Установите зависимости
brew install fltk cmake

# Соберите проект
make

# Или используя CMake
mkdir build && cd build
cmake ..
make
```

#### Используя MacPorts

```bash
# Установите зависимости
sudo port install fltk cmake

# Соберите проект
make
```

### Сборка из исходников FLTK (универсальный способ)

Если в вашем дистрибутиве нет FLTK 1.4.3:

```bash
# Скачайте и соберите FLTK
wget https://www.fltk.org/pub/fltk/1.4.3/fltk-1.4.3-source.tar.gz
tar -xzf fltk-1.4.3-source.tar.gz
cd fltk-1.4.3

# Настройте сборку
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local

# Соберите и установите
make -j$(nproc)
sudo make install

# Обновите библиотечный кэш (Linux)
sudo ldconfig

# Вернитесь в папку проекта и соберите
cd ../../
make
```

## Использование

1. **Запустите программу**: 
   - Linux/macOS: `./SudokuSolver`
   - Windows: `SudokuSolver.exe`

2. **Выберите язык**: Переключатели RU/EN в правом верхнем углу

3. **Пройдите обучение**: При первом запуске появится интерактивное руководство

4. **Введите числа**: 
   - Кликните на ячейку и введите цифру с клавиатуры (1-9)
   - Или используйте кнопки с цифрами справа
   - Для очистки ячейки нажмите Delete, Backspace или 0

5. **Решите судоку**: Нажмите кнопку "Решить" для автоматического решения

6. **Очистите сетку**: Кнопка "Очистить" сбрасывает все ячейки

## Устранение неполадок

### Ошибки компиляции

1. **"fl_open_uri not found"**: Убедитесь, что используете FLTK 1.4.0 или новее
2. **"fltk-config not found"**: Установите dev/devel пакет FLTK
3. **Ошибки линковки**: Проверьте правильность путей к библиотекам FLTK

### Проблемы с зависимостями

```bash
# Проверьте версию FLTK
fltk-config --version

# Проверьте установленные пакеты (Ubuntu/Debian)
dpkg -l | grep fltk

# Проверьте установленные пакеты (Fedora/CentOS)
rpm -qa | grep fltk

# Проверьте установленные пакеты (Arch)
pacman -Q | grep fltk
```

## Функции

### Валидация
- Конфликтующие ячейки подсвечиваются красным цветом
- Проверка правил судоку в реальном времени

### Алгоритм решения
- Использует метод backtracking (возврат с отслеживанием)
- Гарантированно находит решение, если оно существует
- Быстрая работа даже со сложными головоломками

### Интерфейс
- Толстые границы для выделения блоков 3x3
- Крупные, читаемые цифры
- Интуитивное управление
- Поддержка открытия ссылок в браузере

## Поддержка автора

Если вам понравилась программа, вы можете поддержать автора:
- Нажмите кнопку "Поддержать автора" в программе
- Или перейдите по ссылке: https://www.donationalerts.com/r/supermine_

## Технические детали

- **Язык**: C++17
- **GUI библиотека**: FLTK 1.4.3+
- **Компилятор**: GCC 7+, Clang 5+, MSVC 2017+
- **Платформы**: Windows, Linux, macOS
- **Система сборки**: Make, CMake

## Лицензия

Этот проект распространяется свободно. FLTK имеет LGPL лицензию с исключениями для статической линковки.

## Изменения в версии с FLTK 1.4.3

- ✅ Добавлена поддержка `fl_open_uri` для открытия ссылок
- ✅ Улучшена совместимость с современными системами
- ✅ Обновлены инструкции по сборке для всех платформ
- ✅ Добавлена поддержка vcpkg для Windows
- ✅ Расширены инструкции для различных дистрибутивов Linux