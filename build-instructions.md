# Подробные инструкции по компиляции Sudoku Solver с FLTK 1.4.3

## Содержание
1. [Windows](#windows)
2. [Linux](#linux)
3. [macOS](#macos)
4. [Устранение неполадок](#устранение-неполадок)

## Windows

### Метод 1: MSYS2 (Рекомендуется для разработчиков)

#### Шаг 1: Установка MSYS2
1. Скачайте MSYS2 с официального сайта: https://www.msys2.org/
2. Запустите установщик и следуйте инструкциям
3. После установки откройте **MSYS2 MINGW64** терминал

#### Шаг 2: Обновление системы
```bash
pacman -Syu
# Если потребуется перезапуск терминала, сделайте это
pacman -Su
```

#### Шаг 3: Установка зависимостей
```bash
pacman -S mingw-w64-x86_64-gcc \
          mingw-w64-x86_64-fltk \
          mingw-w64-x86_64-cmake \
          mingw-w64-x86_64-make \
          mingw-w64-x86_64-pkg-config
```

#### Шаг 4: Компиляция
```bash
# Перейдите в папку с проектом
cd /path/to/your/project

# Компиляция через Makefile
make

# Или через CMake
mkdir build && cd build
cmake .. -G "MinGW Makefiles"
make
```

### Метод 2: Visual Studio + vcpkg

#### Шаг 1: Установка vcpkg
```cmd
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
```

#### Шаг 2: Установка FLTK
```cmd
.\vcpkg install fltk:x64-windows
```

#### Шаг 3: Компиляция
```cmd
mkdir build && cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:\path\to\vcpkg\scripts\buildsystems\vcpkg.cmake
cmake --build . --config Release
```

### Метод 3: Сборка FLTK из исходников

#### Шаг 1: Скачивание FLTK
1. Скачайте FLTK 1.4.3 с https://www.fltk.org/software.php
2. Распакуйте в `C:\fltk-1.4.3`

#### Шаг 2: Сборка FLTK
```cmd
cd C:\fltk-1.4.3
mkdir build && cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_INSTALL_PREFIX=C:\fltk-1.4.3\install
mingw32-make
mingw32-make install
```

#### Шаг 3: Компиляция проекта
```cmd
g++ -std=c++17 -O2 ^
    -IC:\fltk-1.4.3\install\include ^
    -o SudokuSolver.exe main.cpp ^
    -LC:\fltk-1.4.3\install\lib ^
    -lfltk -lole32 -luuid -lcomctl32 -lwsock32 -mwindows
```

## Linux

### Ubuntu/Debian

#### Установка из репозитория (если доступно)
```bash
sudo apt update
sudo apt install libfltk1.4-dev g++ make cmake pkg-config
```

#### Если FLTK 1.4 недоступен, сборка из исходников:
```bash
# Установка зависимостей для сборки
sudo apt install build-essential cmake libx11-dev libxext-dev \
                 libxft-dev libxinerama-dev libgl1-mesa-dev \
                 libglu1-mesa-dev libasound2-dev

# Скачивание и сборка FLTK
wget https://www.fltk.org/pub/fltk/1.4.3/fltk-1.4.3-source.tar.gz
tar -xzf fltk-1.4.3-source.tar.gz
cd fltk-1.4.3

mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local \
         -DOPTION_BUILD_SHARED_LIBS=ON
make -j$(nproc)
sudo make install
sudo ldconfig

# Возврат в папку проекта
cd ../../
```

#### Компиляция проекта
```bash
make
# или
mkdir build && cd build
cmake ..
make
```

### Fedora/CentOS/RHEL

#### Fedora
```bash
sudo dnf install fltk-devel gcc-c++ make cmake pkg-config
```

#### CentOS/RHEL (с EPEL)
```bash
sudo yum install epel-release
sudo yum install fltk-devel gcc-c++ make cmake pkg-config
```

#### Если пакет недоступен, сборка из исходников:
```bash
# Установка зависимостей
sudo dnf install gcc-c++ cmake libX11-devel libXext-devel \
                 libXft-devel libXinerama-devel mesa-libGL-devel \
                 mesa-libGLU-devel alsa-lib-devel

# Сборка FLTK (аналогично Ubuntu)
```

### Arch Linux

```bash
sudo pacman -S fltk gcc make cmake pkg-config
make
```

### openSUSE

```bash
sudo zypper install fltk-devel gcc-c++ make cmake pkg-config
make
```

## macOS

### Homebrew (Рекомендуется)

```bash
# Установка Homebrew (если не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка зависимостей
brew install fltk cmake pkg-config

# Компиляция
make
```

### MacPorts

```bash
sudo port install fltk cmake pkgconfig
make
```

### Сборка FLTK из исходников на macOS

```bash
# Установка Xcode Command Line Tools
xcode-select --install

# Скачивание и сборка FLTK
curl -O https://www.fltk.org/pub/fltk/1.4.3/fltk-1.4.3-source.tar.gz
tar -xzf fltk-1.4.3-source.tar.gz
cd fltk-1.4.3

mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local \
         -DCMAKE_OSX_DEPLOYMENT_TARGET=10.15
make -j$(sysctl -n hw.ncpu)
sudo make install

cd ../../
make
```

## Устранение неполадок

### Общие проблемы

#### 1. "fl_open_uri not found"
```bash
# Проверьте версию FLTK
fltk-config --version
# Должна быть 1.4.0 или выше

# Если версия старая, соберите из исходников
```

#### 2. "fltk-config not found"
```bash
# Linux: установите dev пакет
sudo apt install libfltk1.4-dev  # Ubuntu/Debian
sudo dnf install fltk-devel      # Fedora
sudo pacman -S fltk              # Arch

# macOS: проверьте PATH
echo $PATH | grep -o '/usr/local/bin'
```

#### 3. Ошибки линковки
```bash
# Проверьте установленные библиотеки
ldconfig -p | grep fltk  # Linux
ls /usr/local/lib/libfltk*  # macOS/Linux
```

### Специфичные для Windows

#### 1. "g++ not found"
- Убедитесь, что используете MSYS2 MINGW64 терминал
- Проверьте установку: `pacman -Q mingw-w64-x86_64-gcc`

#### 2. Проблемы с путями
```cmd
# Используйте полные пути в Windows
set PATH=C:\msys64\mingw64\bin;%PATH%
```

### Специфичные для Linux

#### 1. Отсутствуют X11 заголовки
```bash
# Ubuntu/Debian
sudo apt install libx11-dev libxext-dev libxft-dev

# Fedora
sudo dnf install libX11-devel libXext-devel libXft-devel
```

#### 2. Проблемы с OpenGL
```bash
# Ubuntu/Debian
sudo apt install libgl1-mesa-dev libglu1-mesa-dev

# Fedora
sudo dnf install mesa-libGL-devel mesa-libGLU-devel
```

### Тестирование установки

#### Проверка FLTK
```bash
# Создайте тестовый файл test.cpp
cat > test.cpp << 'EOF'
#include <FL/Fl.H>
#include <FL/Fl_Window.H>
#include <FL/Fl_Button.H>
#include <FL/fl_open_uri.H>
int main() {
    Fl_Window window(300, 200, "Test");
    Fl_Button button(100, 80, 100, 40, "Test");
    window.show();
    return 0;
}
EOF

# Компиляция теста
g++ -std=c++17 `fltk-config --cxxflags` -o test test.cpp `fltk-config --ldflags`

# Если компиляция прошла успешно, FLTK установлен правильно
./test
rm test test.cpp
```

## Оптимизация сборки

### Параллельная сборка
```bash
# Linux/macOS
make -j$(nproc)  # Linux
make -j$(sysctl -n hw.ncpu)  # macOS

# Windows (MSYS2)
make -j$(nproc)
```

### Release сборка
```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

### Статическая линковка (для распространения)
```bash
# CMake
cmake .. -DCMAKE_BUILD_TYPE=Release -DFLTK_BUILD_SHARED_LIBS=OFF

# Прямая компиляция
g++ -std=c++17 -O2 -static-libgcc -static-libstdc++ \
    `fltk-config --cxxflags` -o SudokuSolver main.cpp \
    `fltk-config --ldstaticflags`
```