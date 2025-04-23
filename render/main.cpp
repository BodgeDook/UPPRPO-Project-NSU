#include "videoeditor.hpp"

#include <iostream>
#include <cstring>
#include <string>
#include <algorithm>
#include <regex>

char* getCmdOption(char ** begin, char ** end, const std::string & option){
    char ** itr = std::find(begin, end, option);
    if (itr != end && ++itr != end)
    {
        return *itr;
    }
    return 0;
}

bool cmdOptionExists(char** begin, char** end, const std::string& option){
    return std::find(begin, end, option) != end;
}

int main(int argc, char** argv){
    std::regex resolution_regex("(\\d+)x(\\d+)");
    std::smatch resolution_match;
    int dst_width, dst_height; 


    if(argc == 1)
        std::cerr << "No parameters specified";

    else if(cmdOptionExists(argv, argv + argc, "-help")){
        std::cout << "Usage: -input <input filename> -output <output filename> -codec <Codec to encode> -res <output resolution>\n";
        std::cout << "<input filename>, <output filename>:\n\tSupported formats:\n\t\t.mp4\n";
        std::cout << "<Codec to encode>:\n\tSupported codecs:\n\t\tH.264\n";
        std::cout << "<output resolution>, e.g. 1920x1080\n";
    }
    else{
        if(cmdOptionExists(argv, argv + argc, "-input") && 
        cmdOptionExists(argv, argv + argc, "-output") && 
        cmdOptionExists(argv, argv + argc, "-codec") && 
        cmdOptionExists(argv, argv + argc, "-res")){
            #ifdef DEBUG
            std::cout << "Running DEBUG\n";
            #endif

            std::string inputFilename(getCmdOption(argv, argv + argc, "-input"));
            std::string outputFilename(getCmdOption(argv, argv + argc, "-output"));
            std::string codec(getCmdOption(argv, argv + argc, "-codec"));
            std::string res(getCmdOption(argv, argv + argc, "-res"));
            if(std::regex_match(res, resolution_regex)){
                std::regex_search(res, resolution_match, resolution_regex);
                dst_width = atoi(resolution_match[1].str().c_str());
                dst_height = atoi(resolution_match[2].str().c_str());
            }
            else{
                std::cerr << "Wrong resolution format!\n";
                return -1;
            }
                

            #ifdef DEBUG
            std::cout << "Input: " << inputFilename << ". Output: " << 
            outputFilename << ". Codec: " << codec << ". Resolution: " << res << std::endl;
            #endif

            VideoEditor editorMain(inputFilename, outputFilename, codec, dst_width, dst_height);

            editorMain.loadOperations("../operation_queue.json");
            std::cout << "123\n";
            #ifdef DEBUG
                std::cout << "Operations loaded!" << std::endl;
            #endif

            editorMain.render();
            
            #ifdef DEBUG
                std::cout << "Done!\n";
            #endif
        }
        else{
            std::cerr << "Not all parameters specified!\n";
        }
        
    }
    return 0;
}