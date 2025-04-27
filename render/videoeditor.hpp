#pragma once
#include <iostream>
#include <fstream>
#include <string>
#include <string_view>
#include <vector>

#include "videooperations.hpp"


class VideoEditor{
public:
    VideoEditor(const std::string_view inputFilePath, const std::string_view outputFilePath, std::string_view outputCodec, int dst_width, int dst_height);

    int loadOperations(const std::string_view jsonFilePath);

    int render();

private:
    std::string inputFilePath;
    std::string outputFilePath;
    std::string outputCodec;
    int dst_width, dst_height;
    std::vector<std::string> videoOperations;
};