#pragma once
#include <fstream>
#include <string_view>
#include <vector>

class FFmpegWrapper{
public:
    FFmpegWrapper(std::string_view inputFilename, std::string_view outputFilename);

    int openInput();
    int openOutput();
    void addFilter(const std::string_view filter);
    int process();

private:
    std::ifstream inputFile;
    std::ofstream outputFile;
    std::string inputFilename;
    std::string outputFilename;
    std::vector<std::string> filters;
};