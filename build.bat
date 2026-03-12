@echo off
echo Building Sudoku Solver for Windows with FLTK...

REM Проверяем наличие MinGW
where g++ >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: g++ not found. Please install MinGW-w64 or MSYS2
    echo Download from: https://www.msys2.org/
    pause
    exit /b 1
)

REM Проверяем наличие иконки ICO
if exist "icon.ico" (
    echo Found icon.ico - will be used as application icon
    
    REM Компилируем ресурсы
    echo Compiling resources...
    windres resource.rc -o resource.o
    
    if %errorlevel% neq 0 (
        echo Error: Failed to compile resources
        pause
        exit /b 1
    )
    
    REM Компилируем основную программу с ресурсами
    echo Compiling main program with icon...
    g++ -std=c++17 -O2 -Wall -Wextra -IC:/msys64/mingw64/include -IC:/msys64/mingw64/include/FL -o SudokuSolver.exe main.cpp resource.o -LC:/msys64/mingw64/lib -lfltk -lole32 -luuid -lcomctl32 -lwsock32 -mwindows
    
    if %errorlevel% equ 0 (
        echo Build successful! SudokuSolver.exe created with embedded icon.
        echo Cleaning up temporary files...
        del resource.o 2>nul
    ) else (
        echo Build failed!
        del resource.o 2>nul
        pause
        exit /b 1
    )
) else (
    echo No icon.ico found - building without icon
    
    REM Компилируем без ресурсов
    echo Compiling main program...
    g++ -std=c++17 -O2 -Wall -Wextra -IC:/msys64/mingw64/include -IC:/msys64/mingw64/include/FL -o SudokuSolver.exe main.cpp -LC:/msys64/mingw64/lib -lfltk -lole32 -luuid -lcomctl32 -lwsock32 -mwindows
    
    if %errorlevel% equ 0 (
        echo Build successful! SudokuSolver.exe created without icon.
    ) else (
        echo Build failed!
        pause
        exit /b 1
    )
)

echo You can now run SudokuSolver.exe
pause