#pragma once
#include <string_view>
#include <vector>
#include <string>
#include <vector>
#include <iostream>

#include <rapidjson/document.h>

// #include "videooperations.hpp"
#include "track.hpp"
#include "settings.hpp"

class OperationFactory{
public:
    OperationFactory();
    OperationFactory(std::string_view jsonFilePath);

    int parseSettings();

    int parseTracks();

    void testParse() const;

    Settings getSettings() const;

    std::vector<Track> getTracks() const;

private:
    char readBuffer[65536];

    int status;

    rapidjson::Document doc;
    
    std::string jsonFilePath;

    Settings settings;
    std::vector<Track> tracks;
};