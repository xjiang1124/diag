SET (CMAKE_C_COMPILER /usr/bin/gcc)
SET (CMAKE_CXX_COMPILER /usr/bin/gcc)

set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_COLOR_MAKEFILE   ON)

# init arch
set (arch x86_64)

# Create target if not already created
if (TARGET x86_64)
    set (arch x86_xx)
else()
    add_custom_target(x86_64)
endif()

if( ${CURRENT_MAKE_TARGET} MATCHES "x86_64" )
    message("x86_64 target")
    set (arch x86_64)
endif()

# Enable flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")

# Setup output folder
set (bin_dir ${CMAKE_CURRENT_SOURCE_DIR}/arch_${arch})
execute_process(COMMAND mkdir ${bin_dir})
set(LIBRARY_OUTPUT_PATH ${bin_dir})
set(EXECUTABLE_OUTPUT_PATH ${bin_dir})

#message ("CMAKE_CURRENT_SOURCE_DIR " ${CMAKE_CURRENT_SOURCE_DIR})
#    # Copy binaries to output folder
#    ADD_CUSTOM_COMMAND(TARGET x86_64
#        POST_BUILD
#        #COMMAND cp ${CMAKE_CURRENT_SOURCE_DIR}/arch_${arch}/*so ${PROJECT_BINARY_DIR}
#        COMMAND ${CMAKE_COMMAND} -E copy CMAKE_CURRENT_SOURCE_DIR}/arch_${arch} ${PROJECT_BINARY_DIR}/.
#    )


# Clean-all includes cmake files
if (TARGET clean-all)
else()
    add_custom_target(clean-all
        COMMAND make clean
        COMMAND rm cmake_install.cmake
        COMMAND rm CMakeCache.txt
        COMMAND rm -rf CMakeFiles
        COMMAND rm Makefile
        # TODO: rm src/ directory under build/
        #COMMAND rm -rf ${PROJECT_SOURCE_DIR}/build/src/
    )
endif()
