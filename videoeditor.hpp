#pragma once
#include <iostream>
#include <fstream>
#include <string>
#include <string_view>


class VideoEditor{
public:
    VideoEditor(const std::string_view inputFilePath, const std::string_view outputFilePath);

    int loadOperations(const std::string_view jsonFilePath);

    int render();

private:
    std::ifstream input_file;
    std::ofstream output_file;
};