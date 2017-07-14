cmake_minimum_required (VERSION 3.5.2) 

project(util_math)

include (${CMAKE_CURRENT_SOURCE_DIR}/../../../build/common.cmake)  

include_directories("${CMAKE_CURRENT_SOURCE_DIR}/../../include/") 

add_library( libabs SHARED IMPORTED )
set_target_properties( libabs PROPERTIES IMPORTED_LOCATION ${CMAKE_CURRENT_SOURCE_DIR}/../../lib/abs/arch_${arch}/libabs.so )

add_library( libmulti STATIC IMPORTED )
set_target_properties( libmulti PROPERTIES IMPORTED_LOCATION ${CMAKE_CURRENT_SOURCE_DIR}/../../lib/multi/arch_${arch}/libmulti.a )

#ADD_CUSTOM_COMMAND(TARGET x86_64
#    POST_BUILD 
#    COMMAND ${CMAKE_COMMAND} -E copy CMAKE_CURRENT_SOURCE_DIR}/arch_${arch} ${PROJECT_BINARY_DIR}/.
#    )

add_executable (util_math util_math.cpp)
target_link_libraries (util_math libabs libmulti)
add_dependencies(util_math libabs libmulti)
