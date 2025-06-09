#pragma once

#include <string>
#include <map>

struct Effect{
    std::string name;
    std::map<std::string, float> parameters;
    std::vector<int> keyframes;
};