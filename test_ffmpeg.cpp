#include <iostream>
extern "C" {
    #include <libavformat/avformat.h>
}

int main() {
    av_register_all();
    std::cout << "FFmpeg успешно подключен!" << std::endl;
    return 0;
}
