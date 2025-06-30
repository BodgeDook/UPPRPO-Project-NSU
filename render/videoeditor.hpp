#pragma once
#include <iostream>
#include <fstream>
#include <string>
#include <string_view>
#include <vector>

#include "operationfactory.hpp"
#include "render_export.hpp"

class VideoEditor{
public:
    VideoEditor(const std::string_view jsonFilePath);

    int parseJSON();

    int render();

private:
    std::string jsonFilePath;

    OperationFactory factory;
    Settings settings;
    std::vector<Track> tracks;
};