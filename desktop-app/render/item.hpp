#pragma once

#include <string>
#include <vector>

#include "effect.hpp"

struct Item{
    std::string name;
    std::string type;
    std::string source;
    int startFrame;
    int endFrame;
    std::vector<Effect> effects;
};