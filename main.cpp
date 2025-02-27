#include "videoeditor.hpp"

#include <iostream>


int main(){
    #ifdef DEBUG
        std::cout << "Running DEBUG\n";
    #endif

    VideoEditor editorMain("../server_review.mp4", "../server_review_modified.mp4");

    editorMain.loadOperations("../operation_queue.json");
    std::cout << "123\n";
    #ifdef DEBUG
        std::cout << "Operations loaded!" << std::endl;
    #endif

    editorMain.render();
    
    #ifdef DEBUG
        std::cout << "Done!\n";
    #endif
    return 0;
}