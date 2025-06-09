#pragma once
#include <iostream>
#include <fstream>
#include <string>
#include <string_view>
#include <vector>

// #include "videooperations.hpp"
#include "operationfactory.hpp"

class VideoEditor{
public:
    VideoEditor(const std::string_view jsonFilePath);

    int parseJSON();

    int render(std::string src);

private:
    std::string jsonFilePath;

    OperationFactory factory;
    Settings settings;
    std::vector<Track> tracks;
};