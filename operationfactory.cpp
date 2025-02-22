#include "operationfactory.hpp"
// #include <rapidjson>

/*
    OperationFactory class, creates an std::vector<VideoOperation*> from JSON configuration file.
    Has methods:
    1. createOperationList method that creates std::vector<VideoOperation*> of the operations
*/

// Constructor, gets path to JSON configuration file
OperationFactory::OperationFactory(const std::string_view jsonFilePath): jsonFilePath(std::string{jsonFilePath}){};

// createOperationList method that creates std::vector<VideoOperation*> of the operations
std::vector<VideoOperation*> OperationFactory::createOperationsList(){

}