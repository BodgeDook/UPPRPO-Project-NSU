#include "videoeditor.hpp"
#include "operationfactory.hpp"
#include "ffmpegwrapper.hpp"

VideoEditor::VideoEditor(const std::string_view jsonFilePath): jsonFilePath(jsonFilePath){
    std::string jsonFilePath_str = std::string(jsonFilePath);
    this->factory = OperationFactory(jsonFilePath_str.c_str());
}


int VideoEditor::parseJSON(){
    int status = 0;

    status = this->factory.parseSettings();
    if(!status)
        status = this->factory.parseTracks();

    if(status){
        std::cerr << "Error whie parsing JSON config\n";
        return 1;
    }

    this->settings = this->factory.getSettings();
    this->tracks = this->factory.getTracks();

    return 0;
}

int VideoEditor::render(std::string src){
    #ifdef DEBUG
        std::cout << "Rendering..." << std::endl;
    #endif
    FFmpegWrapper wrapper(this->settings, this->tracks);

    wrapper.process(src);

    #ifdef DEBUG
        std::cout << "Done\n";
    #endif

    return 0;
}