#pragma once
#include <string_view>
#include <vector>
#include "videooperations.hpp"

class OperationFactory{
public:
    OperationFactory(std::string_view jsonFilePath);
    void createOperationsList();
    std::vector<VideoOperation*> getOperationList();

private:
    std::string jsonFilePath;
    std::vector<VideoOperation*> videoOperations;

};