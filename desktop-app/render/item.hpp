#pragma once

#include <string>
#include <vector>

#include "effect.hpp"

struct Item{
    std::string name;
    std::string type;
    std::string source;
    double begin;
    double end;
    std::vector<Effect> effects;
};