
#include <iostream>


extern "C" {
    #include <libavformat/avformat.h>
}

#include <rapidjson/allocators.h>

int main(int argc, const char** argv) {


    if(argc < 2){
        std::cout << "Enter filename\n";
        return -1;
    }
        
    AVFormatContext* fmt_ctx = NULL;

    if (avformat_open_input(&fmt_ctx, argv[1], NULL, NULL) != 0) {
        std::cerr << "Error while opening a file!\n";
        return -1;
    }

    av_dump_format(fmt_ctx, 0, argv[1], 0);
    avformat_close_input(&fmt_ctx);

    std::cout << "Done!\n";
    return 0;
}
