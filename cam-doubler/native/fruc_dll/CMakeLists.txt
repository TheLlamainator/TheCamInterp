cmake_minimum_required(VERSION 3.20)
project(fruc_dll LANGUAGES CXX)
add_library(fruc SHARED fruc.cpp fruc.h)
target_compile_features(fruc PRIVATE cxx_std_17)
