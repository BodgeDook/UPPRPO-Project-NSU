#pragma once
#include <iostream>
#include <fstream>
#include <string>
#include <string_view>
#include <vector>

#include "videooperations.hpp"


class VideoEditor{
public:
    VideoEditor(const std::string_view inputFilePath, const std::string_view outputFilePath);

    int loadOperations(const std::string_view jsonFilePath);

    int render();

private:
    std::string inputFilePath;
    std::string outputFilePath;
    std::vector<VideoOperation*> videoOperations;
};