#include "videooperations.hpp"


/*
    ResizeOperation class, child of abstarct VideoOperation class
    Has methods:
    1. getFilterString method that returns string representation of the operation
*/

// Consturtor, gets new width and height of the video
ResizeOperation::ResizeOperation(const int width, const int height): width(width), height(height){};

// getFilterString method that returns string representation of the operation
std::string ResizeOperation::getFilterString() const{
    return "resize " + std::to_string(width) + " " + std::to_string(height);
}


/*
    CropOperation class, child of abstarct VideoOperation class
    Has methods:
    1. getFilterString method that returns string representation of the operation
*/

// Consturtor, gets 4 borders of the cropped video
CropOperation::CropOperation(const int width_left, const int width_right, const int height_top, const int height_bottom): 
    width_left(width_left), width_right(width_right), height_top(height_top), height_bottom(height_bottom){};

// getFilterString method that returns string representation of the operation
std::string CropOperation::getFilterString() const{
    return "crop " + std::to_string(width_left) + " " + std::to_string(width_right) + " " + std::to_string(height_top) + " " + std::to_string(height_bottom);
}
