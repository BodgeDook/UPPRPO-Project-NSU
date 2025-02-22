#pragma once
#include <string_view>
#include <vector>
#include "videooperations.hpp"

class OperationFactory{
public:
OperationFactory::OperationFactory(std::string_view jsonFilePath);
    std::vector<VideoOperation*> createOperationsList();

private:
    std::string jsonFilePath;
};