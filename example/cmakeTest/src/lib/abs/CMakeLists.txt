cmake_minimum_required (VERSION 3.5.2)

# shared libraries need PIC
set_property(TARGET ${objlib} PROPERTY POSITION_INDEPENDENT_CODE 1) 

project (abs) 
include (${CMAKE_CURRENT_SOURCE_DIR}/../../../build/common.cmake)

set(libsrc abs.cpp)

# Include header files
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../include) 

add_library(abs SHARED ${libsrc})
add_library(abs_static STATIC ${libsrc}) 

set_target_properties(abs_static PROPERTIES OUTPUT_NAME abs) 
