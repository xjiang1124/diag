cmake_minimum_required (VERSION 3.5.2)
include(${CMAKE_CURRENT_SOURCE_DIR}/build/common.cmake)

project(new_project)

# setup output folder
execute_process(COMMAND mkdir ${PROJECT_SOURCE_DIR}/build/bin)
execute_process(COMMAND mkdir ${PROJECT_SOURCE_DIR}/build/bin/lib/)
set(PROJECT_BINARY_DIR ${PROJECT_SOURCE_DIR}/build/bin)

add_subdirectory(src/lib/abs)
add_subdirectory(src/lib/multi)

add_subdirectory(src/diag/math)

add_subdirectory(src/util/math_util)

ADD_CUSTOM_COMMAND(TARGET x86_64
    POST_BUILD 
    COMMAND ${CMAKE_COMMAND} -E copy CMAKE_CURRENT_SOURCE_DIR}/arch_${arch} ${PROJECT_BINARY_DIR}/.
    )

