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
    if(argc == 1)
        std::cerr << "No parameters specified";
    else if(cmdOptionExists(argv, argv + argc, "-config") && cmdOptionExists(argv, argv + argc, "-src")){
        std::string config_file(getCmdOption(argv, argv + argc, "-config"));
        std::string src(getCmdOption(argv, argv + argc, "-src"));
        
        VideoEditor editor(config_file);

        editor.parseJSON();
        editor.render(src);
    }

    return 0;
}