cmake_minimum_required (VERSION 3.5.2) 

include (${CMAKE_CURRENT_SOURCE_DIR}/../../../build/common.cmake)  

include_directories("${CMAKE_CURRENT_SOURCE_DIR}/../../include/") 

add_library( libabs SHARED IMPORTED )
set_target_properties( libabs PROPERTIES IMPORTED_LOCATION ${CMAKE_CURRENT_SOURCE_DIR}/../../lib/abs/arch_${arch}/libabs.so )

add_executable (my_math my_math.cpp)
target_link_libraries (my_math libabs)
add_dependencies(my_math libabs)
