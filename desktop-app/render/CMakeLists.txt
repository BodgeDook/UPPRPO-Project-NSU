# To use ffmpeg add the following to your CMake project:

# find_package(FFMPEG REQUIRED)
# target_include_directories(main PRIVATE ${FFMPEG_INCLUDE_DIRS})
# target_link_directories(main PRIVATE ${FFMPEG_LIBRARY_DIRS})
# target_link_libraries(main PRIVATE ${FFMPEG_LIBRARIES})

cmake_minimum_required(VERSION 3.25)
project(render)

set(CMAKE_CXX_STANDARD 17)

set(FFMPEG_DIR "${CMAKE_SOURCE_DIR}/ffmpeg")
set(FFMPEG_INCLUDE_DIRS "${FFMPEG_DIR}/include")
set(FFMPEG_LIBRARIES 
    "${FFMPEG_DIR}/lib/avfilter.lib"
    "${FFMPEG_DIR}/lib/avformat.lib"
    "${FFMPEG_DIR}/lib/avcodec.lib"
    "${FFMPEG_DIR}/lib/swscale.lib"
    "${FFMPEG_DIR}/lib/avutil.lib"
    "${FFMPEG_DIR}/lib/swresample.lib"
)

foreach(lib ${FFMPEG_LIBRARIES})
    if(NOT EXISTS ${lib})
        message(FATAL_ERROR "Library not found: ${lib}")
    endif()
endforeach()

option(BUILD_SHARED_LIB "Build shared or executable" OFF)

option(BUILD_DEBUG "Build debug/release version" ON)

if(BUILD_DEBUG)
    add_compile_definitions(DEBUG)
endif()

if(BUILD_SHARED_LIB)
    add_library(render SHARED
        operationfactory.cpp
        videoeditor.cpp
        ffmpegwrapper.cpp
    )

    if(WIN32)
        target_compile_definitions(render PRIVATE RENDER_BUILD_DLL)
    endif()

    if(UNIX)
        target_compile_options(render PRIVATE -fvisibility=hidden)
    endif()

else()
    add_executable(render 
        main.cpp 
        operationfactory.cpp 
        videoeditor.cpp 
        ffmpegwrapper.cpp
    )
endif()

target_include_directories(render PRIVATE
    ${FFMPEG_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/rapidjson/include
    ${CMAKE_SOURCE_DIR}
)

target_include_directories(render
  PUBLIC
    
)

target_link_libraries(render PRIVATE ${FFMPEG_LIBRARIES})

add_custom_command(TARGET render POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    "${CMAKE_SOURCE_DIR}/ffmpeg/bin" "${CMAKE_BINARY_DIR}")
