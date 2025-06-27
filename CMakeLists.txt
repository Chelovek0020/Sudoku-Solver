cmake_minimum_required(VERSION 3.15)
project(SudokuSolver)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Найти FLTK
find_package(PkgConfig REQUIRED)
pkg_check_modules(FLTK REQUIRED fltk)

# Создать исполняемый файл
add_executable(SudokuSolver main.cpp)

# Добавить флаги компиляции и линковки FLTK
target_compile_options(SudokuSolver PRIVATE ${FLTK_CFLAGS})
target_link_libraries(SudokuSolver ${FLTK_LIBRARIES})

# Для Windows
if(WIN32)
    target_link_libraries(SudokuSolver comctl32 wsock32 ole32 uuid)
    # Убираем консольное окно в Release сборке
    set_target_properties(SudokuSolver PROPERTIES
        WIN32_EXECUTABLE TRUE
        LINK_FLAGS_RELEASE "/SUBSYSTEM:WINDOWS"
    )
endif()

# Для macOS
if(APPLE)
    target_link_libraries(SudokuSolver "-framework Cocoa")
endif()