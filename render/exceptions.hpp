#pragma once
#include <string>

class Exception: public std::exception{
public:
    char* what();
private:
    
    std::string message;
};

class 