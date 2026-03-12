# Makefile для компиляции с FLTK 1.4.3
CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra
FLTK_CXXFLAGS = `fltk-config --cxxflags`
FLTK_LDFLAGS = `fltk-config --ldflags`

TARGET = SudokuSolver
SOURCE = main.cpp

all: $(TARGET)
	@if [ -f "icon.png" ]; then \
		echo "Icon found: icon.png detected for application icon"; \
	else \
		echo "No icon.png found - application will use default icon"; \
	fi

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) $(FLTK_CXXFLAGS) -o $(TARGET) $(SOURCE) $(FLTK_LDFLAGS)

clean:
	rm -f $(TARGET) $(TARGET).exe

# Установка зависимостей для различных дистрибутивов
install-deps-ubuntu:
	sudo apt-get update
	sudo apt-get install libfltk1.4-dev g++ make cmake

install-deps-debian:
	sudo apt-get update
	sudo apt-get install libfltk1.4-dev g++ make cmake

install-deps-fedora:
	sudo dnf install fltk-devel gcc-c++ make cmake

install-deps-centos:
	sudo yum install fltk-devel gcc-c++ make cmake

install-deps-arch:
	sudo pacman -S fltk gcc make cmake

install-deps-opensuse:
	sudo zypper install fltk-devel gcc-c++ make cmake

install-deps-alpine:
	sudo apk add fltk-dev g++ make cmake

# Сборка из исходников FLTK (если пакет недоступен)
build-fltk-from-source:
	@echo "Downloading and building FLTK 1.4.3 from source..."
	wget https://www.fltk.org/pub/fltk/1.4.3/fltk-1.4.3-source.tar.gz
	tar -xzf fltk-1.4.3-source.tar.gz
	cd fltk-1.4.3 && ./configure --prefix=/usr/local --enable-shared && make && sudo make install
	rm -rf fltk-1.4.3 fltk-1.4.3-source.tar.gz

.PHONY: all clean install-deps-ubuntu install-deps-debian install-deps-fedora install-deps-centos install-deps-arch install-deps-opensuse install-deps-alpine build-fltk-from-source