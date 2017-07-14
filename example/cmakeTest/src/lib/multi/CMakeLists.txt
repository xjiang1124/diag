cmake_minimum_required (VERSION 3.5.2)

# shared libraries need PIC
set_property(TARGET ${objlib} PROPERTY POSITION_INDEPENDENT_CODE 1) 

project (multi) 
include (${CMAKE_CURRENT_SOURCE_DIR}/../../../build/common.cmake)

set(libsrc multi.cpp)

# Include header files
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../include) 

add_library(multi SHARED ${libsrc})
add_library(multi_static STATIC ${libsrc}) 

set_target_properties(multi_static PROPERTIES OUTPUT_NAME multi) 
