#include "ffmpegwrapper.hpp"
#include <sstream>
#include <string>
#include <iostream>


/*
    FFmpegWrapper class, wraps interaction with FFmpeg API into custom interface
    Has methods:
    1. openInput method opend input file stream
    2. openOutput method opens output file stream
    3. addFilter method adds string representation of filter into vector of string representations of filters
    4. process method applies all filters from std::vector<std::string> filters
*/

//  Constructor, gets inputFilename and outputFilename
FFmpegWrapper::FFmpegWrapper(std::string_view inputFilename, std::string_view outputFilename): 
    inputFilename(inputFilename), outputFilename(outputFilename){};

// openInput, opens ifstream
int FFmpegWrapper::openInput(){
    // inputFile.open(std::string{this->inputFile}, std::ios::in);
    return 0;
}


// openOutput, opens ofstream
int FFmpegWrapper::openOutput(){
    
    return 0;
}

// addFilter, adds string representation of filter into std::vector<std::string> filters
void FFmpegWrapper::addFilter(const std::string_view filter){
    this->filters.push_back(std::string(filter));
}


// process, applies all filters
int FFmpegWrapper::process(){
    std::stringstream parseFilterSS;
    std::string parameter;
    std::string operation;
    for(std::string filter:filters){
        std::vector<std::string> parameters;
        parseFilterSS << filter;

        parseFilterSS >> operation;
        
        while(parseFilterSS >> parameter)
            parameters.push_back(parameter);

        #ifdef DEBUG
            std::cout << operation << " ";
            for(std::string parameter: parameters)
                std::cout << parameter << " ";
            std::cout << std::endl;
            std::stringstream().swap(parseFilterSS);
        #endif
    }

    return 0;
}