#pragma once

#include <string>
#include <vector>

#include "item.hpp"

struct Track{
    std::string name;
    std::string type; // e.g., "video", "audio"
    std::vector<Item> items;
};