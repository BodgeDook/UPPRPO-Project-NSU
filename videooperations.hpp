#pragma once
#include <iostream>
#include <string>


class VideoOperation{
public:
    virtual ~VideoOperation();
    virtual std::string getFilterString() const;
};


class ResizeOperation: public VideoOperation{
public:
    ResizeOperation(const int width, const int height);
    std::string getFilterString() const override;

private:
    int width, height;
};


class CropOperation: public VideoOperation{
public:
    CropOperation(const int width_left, const int width_right, const int height_top, const int height_bottom);
    std::string getFilterString() const override;

private:
    int width_left, width_right, height_top, height_bottom;
};