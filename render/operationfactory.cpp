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
            if(operationName == "scale"){
                int width = operation["width"].GetInt();
                int height = operation["height"].GetInt();

                this->videoOperations.push_back("scale=" + std::to_string(width) + ":" + std::to_string(height));
            }
            else if(operationName == "crop"){
                int x = operation["x"].GetInt();
                int y = operation["y"].GetInt();
                int w = operation["w"].GetInt();
                int h = operation["h"].GetInt();

                this->videoOperations.push_back("crop=" + std::to_string(x) + ":" + std::to_string(y) + ":" + std::to_string(w) + ":" + std::to_string(h));

            }
            else if(operationName == "rotate"){
                int angle = operation["angle"].GetFloat();
                this->videoOperations.push_back("rotate=" + std::to_string(angle));
            }
            else if(operationName == "boxblur"){
                int x = operation["x"].GetInt();
                int y = operation["y"].GetInt();
                this->videoOperations.push_back("boxblur=" + std::to_string(x) + ":" + std::to_string(y));
            }
            else if(operationName == "hflip"){
                this->videoOperations.push_back("hflip");
            }
            else if(operationName == "vflip"){
                this->videoOperations.push_back("vflip");
            }
            else if(operationName == "drawtext"){
                std::string text = operation["text"].GetString();
                int x = operation["x"].GetInt();
                int y = operation["y"].GetInt();
                int fontSize = operation["fontsize"].GetInt();
                std::string fontColor = operation["fontcolor"].GetString();
                this->videoOperations.push_back("drawtext=text='" + text + "':x=" + std::to_string(x) + ":y=" + std::to_string(y) + ":fontsize=" + std::to_string(fontSize) + ":fontcolor=" + fontColor);
            }
            else if(operationName == "setpts"){
                std::string pts = operation["speed"].GetString();
                this->videoOperations.push_back("setpts=" + pts);
            }
            else{
                std::cerr << "Error: unknown operation type " << operationName << std::endl;
            }
        }
    }
    #ifdef DEBUG
        std::cout << "Operations loaded" << std::endl;
    #endif
}

std::vector<std::string> OperationFactory::getOperationList(){
    return this->videoOperations;
}