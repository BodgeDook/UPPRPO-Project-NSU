# To use ffmpeg add the following to your CMake project:

# find_package(FFMPEG REQUIRED)
# target_include_directories(main PRIVATE ${FFMPEG_INCLUDE_DIRS})
# target_link_directories(main PRIVATE ${FFMPEG_LIBRARY_DIRS})
# target_link_libraries(main PRIVATE ${FFMPEG_LIBRARIES})

cmake_minimum_required(VERSION 3.20)
project(Test_FFmpeg)

set(CMAKE_CXX_STANDARD 17)

add_compile_definitions(DEBUG)

set(FFMPEG_DIR "${CMAKE_SOURCE_DIR}/ffmpeg")
set(FFMPEG_INCLUDE_DIRS "${FFMPEG_DIR}/include")
set(FFMPEG_LIBRARIES "${FFMPEG_DIR}/lib/avcodec.lib" "${FFMPEG_DIR}/lib/avformat.lib" "${FFMPEG_DIR}/lib/avutil.lib" "${FFMPEG_DIR}/lib/swscale.lib")

add_executable(Test_FFmpeg main.cpp ffmpegwrapper.cpp)

target_include_directories(Test_FFmpeg PRIVATE ${FFMPEG_INCLUDE_DIRS})

target_link_libraries(Test_FFmpeg PRIVATE ${FFMPEG_LIBRARIES})

# add_subdirectory(${CMAKE_SOURCE_DIR}/rapidjson)
# target_link_libraries(Test_FFmpeg RapidJSON rapidjson)

add_custom_command(TARGET Test_FFmpeg POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    "${CMAKE_SOURCE_DIR}/ffmpeg/bin" "${CMAKE_BINARY_DIR}")