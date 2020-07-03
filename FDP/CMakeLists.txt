cmake_minimum_required(VERSION 3.14)
cmake_policy(SET CMP0048 NEW)

project(FDP VERSION 20.1)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

include_directories("FDP/include")

ADD_LIBRARY(FDP-shared SHARED "FDP/FDP.c")
SET_TARGET_PROPERTIES(FDP-shared PROPERTIES
   OUTPUT_NAME FDP CLEAN_DIRECT_OUTPUT 1)
target_link_libraries(FDP-shared Threads::Threads)
if(UNIX AND NOT APPLE)
    target_link_libraries(FDP-shared rt)
endif()

ADD_LIBRARY(FDP-static STATIC "FDP/FDP.c")
SET_TARGET_PROPERTIES(FDP-static PROPERTIES
   OUTPUT_NAME FDP CLEAN_DIRECT_OUTPUT 1)
target_link_libraries(FDP-static Threads::Threads)
if(UNIX AND NOT APPLE)
    target_link_libraries(FDP-static rt)
endif()

add_executable(testFDP TestFDP/testFDP.c)
target_link_libraries(testFDP FDP-static)

add_executable(testFDPClientServer TestFDP/testFDPClientServer.c)
target_link_libraries(testFDPClientServer FDP-static)
