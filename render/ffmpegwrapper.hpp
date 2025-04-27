#pragma once
#include <fstream>
#include <string_view>
#include <vector>

extern "C" {
    #include <libavformat/avformat.h>
    #include <libswscale/swscale.h>
    #include <libavcodec/avcodec.h>
    #include <libavutil/imgutils.h>
    #include <libavfilter/avfilter.h>
    #include <libavfilter/buffersrc.h>
    #include <libavfilter/buffersink.h>
}

class FFmpegWrapper{
public:
    FFmpegWrapper(const std::string_view inputFilename, const std::string_view outputFilename, std::string_view outputCodec, int dst_width, int dst_height);

    int openInput();
    int openOutput();
    void addFilter(const std::string_view filter);
    int process();
    int initFilters();

private:
    std::ifstream inputFile;
    std::ofstream outputFile;
    std::string inputFilename;
    std::string outputFilename;
    std::vector<std::string> filters;
    std::string allFiltersStr;
    std::string outputCodecStr;
    int dst_width, dst_height;
    AVFilterGraph* filter_graph;           // Граф фильтров
    AVFilterContext* buffer_src_ctx;       // Источник фильтров (buffersrc)
    AVFilterContext* buffer_sink_ctx;      // Приемник фильтров (buffersink)

    // FFmpeg classfields
    AVFormatContext* fmt_ctx;
    int video_stream_index;
    AVCodecParameters* codecpar;
    const AVCodec* codec;
    const AVCodec* output_codec;
    AVCodecContext* codec_ctx;
    AVPixelFormat src_pix_fmt;
    AVPixelFormat dst_pix_fmt;
    AVFormatContext* out_fmt_ctx;
    AVStream* out_stream;
    AVCodecContext* out_codec_ctx;
};