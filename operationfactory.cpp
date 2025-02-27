#include "operationfactory.hpp"
#include <rapidjson/document.h>
#include <rapidjson/filereadstream.h>

/*
    OperationFactory class, creates an std::vector<VideoOperation*> from JSON configuration file.
    Has methods:
    1. createOperationList method that creates std::vector<VideoOperation*> of the operations
*/

// Constructor, gets path to JSON configuration file
OperationFactory::OperationFactory(const char* jsonFilePath): jsonFilePath(jsonFilePath){};

// createOperationList method that creates std::vector<VideoOperation*> of the operations
std::vector<VideoOperation*> OperationFactory::createOperationsList(){
    FILE* fp = fopen(this->jsonFilePath, "rb");

    if(!fp){
        std::cerr << "Error: unable to open operation_queue.json" << std::endl;
        exit(EXIT_FAILURE);
    }

    char readBuffer[65536];
    rapidjson::FileReadStream is(fp, readBuffer, sizeof(readBuffer));

    rapidjson::Document doc;
    doc.ParseStream(is);

    if(doc.HasParseError()){
        std::cerr << "Error: failed to parse operation_queue.json" << std::endl;
        fclose(fp);
        exit(EXIT_FAILURE);
    }

    fclose(fp);

    if(doc.HasMember("Operations") && doc["Operations"].IsArray()){
        auto operations = doc["Operations"].GetArray();
        // for(auto operation: operations){
        //     operation
        // }
        #ifdef DEBUG
            std::cout << operations;
        #endif
    }
}