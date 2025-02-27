#include "videoeditor.hpp"
#include "operationfactory.hpp"
#include "ffmpegwrapper.hpp"

VideoEditor::VideoEditor(const std::string_view inputFilePath, const std::string_view outputFilePath): inputFilePath(inputFilePath), outputFilePath(outputFilePath){}


int VideoEditor::loadOperations(const std::string_view jsonFilePath){

    #ifdef DEBUG
        std::cout << "Opening " << std::string(jsonFilePath).c_str() << std::endl;
    #endif

    std::string jsonFilePath_str = std::string(jsonFilePath);

    OperationFactory factory(jsonFilePath_str.c_str());
    factory.createOperationsList();
    this->videoOperations = factory.getOperationList();

    #ifdef DEBUG
        std::cout << "Done loading operations" << std::endl;
    #endif

    return 0;
}

int VideoEditor::render(){
    #ifdef DEBUG
        std::cout << "Rendering..." << std::endl;
    #endif
    FFmpegWrapper wrapper(this->inputFilePath, this->outputFilePath);
    for(VideoOperation* filter: this->videoOperations)
        wrapper.addFilter(filter->getFilterString());

    wrapper.openInput();
    wrapper.openOutput();
    wrapper.process();

    return 0;
}