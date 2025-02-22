#include "ffmpegwrapper.hpp"
#include <iostream>


int main(){
    #ifdef DEBUG
        std::cout << "Running DEBUG\n";
    #endif


    FFmpegWrapper wrapper("input.mp4", "output.mp4");
    wrapper.addFilter("resize 1920 1080");
    wrapper.addFilter("crop 1000 1500 1200 1400");
    wrapper.process();
    
    #ifdef DEBUG
        std::cout << "Done!\n";
    #endif
    return 0;
}