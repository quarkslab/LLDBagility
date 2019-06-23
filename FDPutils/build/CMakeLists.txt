project(FDP)

cmake_minimum_required(VERSION 3.14)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

include_directories("../FDP/include")

add_library(FDP SHARED "../FDP/FDP.c")
target_link_libraries(FDP Threads::Threads)
if(UNIX AND NOT APPLE)
    target_link_libraries(FDP rt)
endif()

add_executable(testFDP ../TestFDP/testFDP.c)
target_link_libraries(testFDP FDP)

add_executable(testFDPClientServer ../TestFDP/testFDPClientServer.c)
target_link_libraries(testFDPClientServer FDP)
