#pragma once
#include <iostream>
#include <string>


class VideoOperation{
public:
    virtual ~VideoOperation();
    virtual std::string getFilterString() const;
};


class ScaleOperation: public VideoOperation{
public:
    ScaleOperation(const int width, const int height);
    std::string getFilterString() const override;

private:
    int width, height;
};


class CropOperation: public VideoOperation{
public:
    CropOperation(const int x, const int y, const int w, const int h);
    std::string getFilterString() const override;

private:
    int x, y, w, h;
};