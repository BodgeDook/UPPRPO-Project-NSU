# To use ffmpeg add the following to your CMake project:

# find_package(FFMPEG REQUIRED)
# target_include_directories(main PRIVATE ${FFMPEG_INCLUDE_DIRS})
# target_link_directories(main PRIVATE ${FFMPEG_LIBRARY_DIRS})
# target_link_libraries(main PRIVATE ${FFMPEG_LIBRARIES})

cmake_minimum_required(VERSION 3.20)
project(render)

set(CMAKE_CXX_STANDARD 17)

add_compile_definitions(DEBUG)

if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    set(FFMPEG_INCLUDE_DIRS "/opt/homebrew/include")
    set(FFMPEG_LIBRARY_DIRS "/opt/homebrew/lib")
    set(FFMPEG_LIBRARIES
        avformat
        avcodec
        avutil
        swscale
    )
elseif (${CMAKE_SYSTEM_NAME} MATCHES "Linux")
    message("Running on Linux")
elseif (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
    set(FFMPEG_DIR "${CMAKE_SOURCE_DIR}/ffmpeg")
    set(FFMPEG_INCLUDE_DIRS "${FFMPEG_DIR}/include")
    set(FFMPEG_LIBRARY_DIRS "${FFMPEG_DIR}/lib")
    set(FFMPEG_LIBRARIES
        "${FFMPEG_DIR}/lib/avcodec.lib"
        "${FFMPEG_DIR}/lib/avformat.lib"
        "${FFMPEG_DIR}/lib/avutil.lib"
        "${FFMPEG_DIR}/lib/swscale.lib"
    )
endif()

add_executable(render main.cpp ffmpegwrapper.cpp operationfactory.cpp videoeditor.cpp videooperations.cpp)

target_include_directories(render PRIVATE ${FFMPEG_INCLUDE_DIRS})
target_link_directories(render PRIVATE ${FFMPEG_LIBRARY_DIRS})

target_link_libraries(render PRIVATE ${FFMPEG_LIBRARIES})

target_include_directories(render PRIVATE ${CMAKE_SOURCE_DIR}/rapidjson/include)

add_custom_command(TARGET render POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    "${CMAKE_SOURCE_DIR}/ffmpeg/bin" "${CMAKE_BINARY_DIR}")
    
# target_link_directories(render PRIVATE ${FFMPEG_LIBRARY_DIRS})