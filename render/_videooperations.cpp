#include "videooperations.hpp"


VideoOperation::~VideoOperation() = default;
std::string VideoOperation::getFilterString() const {
    return "test123";
}


/*
    ScaleOperation class, child of abstarct VideoOperation class
    Has methods:
    1. getFilterString method that returns string representation of the operation
*/

// Consturtor, gets new width and height of the video
ScaleOperation::ScaleOperation(int width, int height): width(width), height(height){};

// getFilterString method that returns string representation of the operation
std::string ScaleOperation::getFilterString() const{
    return "scale=" + std::to_string(width) + ":" + std::to_string(height);
}


/*
    CropOperation class, child of abstarct VideoOperation class
    Has methods:
    1. getFilterString method that returns string representation of the operation
*/

// Consturtor, gets 4 borders of the cropped video
CropOperation::CropOperation(int x, int y, int w, int h): 
    x(x), y(y), w(w), h(h){};

// getFilterString method that returns string representation of the operation
std::string CropOperation::getFilterString() const{
    return "crop=" + std::to_string(this->x) + ":" + std::to_string(this->y) + ":" + std::to_string(this->w) + ":" + std::to_string(this->h);
}