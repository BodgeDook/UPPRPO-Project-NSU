#pragma once
#include <string_view>
#include <vector>
#include "videooperations.hpp"

class OperationFactory{
public:
OperationFactory(const char* jsonFilePath);
std::vector<VideoOperation*> createOperationsList();

private:
    const char* jsonFilePath;
    std::vector<VideoOperation*> video_operations;

};