#include "operationfactory.hpp"
#include <rapidjson/document.h>
#include <rapidjson/filereadstream.h>

/*
    OperationFactory class, creates an std::vector<VideoOperation*> from JSON configuration file.
    Has methods:
    1. createOperationList method that creates std::vector<VideoOperation*> of the operations
*/

// Constructor, gets path to JSON configuration file
OperationFactory::OperationFactory(std::string_view jsonFilePath): jsonFilePath(std::string(jsonFilePath)){};

// createOperationList method that creates std::vector<VideoOperation*> of the operations
void OperationFactory::createOperationsList(){

    #ifdef DEBUG
        std::cout << "Opening " << this->jsonFilePath.c_str() << std::endl;
    #endif

    FILE* fp = fopen(this->jsonFilePath.c_str(), "rb");

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
        for(auto& operation: operations){
            std::string operationName = operation["type"].GetString();
            if(operationName == "resize"){
                int width = operation["width"].GetInt();
                int height = operation["height"].GetInt();

                ResizeOperation resizeOp(width, height);

                this->videoOperations.push_back(&resizeOp);
            }
            else if(operationName == "crop"){
                int left_border = operation["left"].GetInt();
                int right_border = operation["right"].GetInt();
                int top_border = operation["top"].GetInt();
                int bottom_border = operation["bottom"].GetInt();

                CropOperation cropOp(left_border, right_border, top_border, bottom_border);

                this->videoOperations.push_back(&cropOp);

            }
        }
    }
    #ifdef DEBUG
        std::cout << "Operations loaded" << std::endl;
    #endif
}

std::vector<VideoOperation*> OperationFactory::getOperationList(){
    return this->videoOperations;
}