cmake_minimum_required(VERSION 3.10)
project(elmore_cpp)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# 设置头文件目录
include_directories(inc)

# 查找源文件
# file(GLOB SOURCES "src/*.cpp")

add_executable(elmore_cpp src/main.cpp src/Parser.cpp src/RCTree.cpp)
