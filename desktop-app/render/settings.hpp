#pragma once

#include <string>

struct Settings{
    std::string outputFilePath;
    std::string codec;
    int dst_width;
    int dst_height;
    int framerate;
};