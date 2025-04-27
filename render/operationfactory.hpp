#pragma once
#include <string_view>
#include <vector>
#include <string>
#include "videooperations.hpp"

class OperationFactory{
public:
    OperationFactory(std::string_view jsonFilePath);
    void createOperationsList();
    std::vector<std::string> getOperationList();
    std::vector<std::string> videoOperations;

private:
    std::string jsonFilePath;
    

};