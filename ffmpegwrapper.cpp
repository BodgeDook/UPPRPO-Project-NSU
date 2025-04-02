#include "ffmpegwrapper.hpp"
#include <sstream>
#include <string>
#include <iostream>


/*
    FFmpegWrapper class, wraps interaction with FFmpeg API into custom interface
    Has methods:
    1. openInput method opend input file stream
    2. openOutput method opens output file stream
    3. addFilter method adds string representation of filter into vector of string representations of filters
    4. process method applies all filters from std::vector<std::string> filters
*/

//  Constructor, gets inputFilename and outputFilename.
FFmpegWrapper::FFmpegWrapper(std::string_view inputFilename, std::string_view outputFilename, std::string_view outputCodec, int dst_width, int dst_height): 
    inputFilename(inputFilename), outputFilename(outputFilename), outputCodecStr(outputCodec), dst_width(dst_width), dst_height(dst_height){};

// openInput, opens input file
int FFmpegWrapper::openInput(){
    this->fmt_ctx = avformat_alloc_context();
    if (avformat_open_input(&fmt_ctx, std::string(this->inputFilename).c_str(), NULL, NULL) < 0) {
        std::cerr << "Error while opening a file! (avformat_open_input)\n";
        avformat_close_input(&fmt_ctx);
        return -1;
    }
    if (avformat_find_stream_info(fmt_ctx, NULL) < 0) {
        std::cerr << "Error while opening a file! (avformat_find_stream_info)\n";
        avformat_close_input(&fmt_ctx);
        return -1;
    }

    this->video_stream_index = -1;
    for (unsigned int i = 0; i < this->fmt_ctx->nb_streams; i++) {
        if (this->fmt_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
            this->video_stream_index = i;
            break;
        }
    }
    if (this->video_stream_index == -1) {
        std::cerr << "Video stream not found!\n";
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }

    this->codecpar = this->fmt_ctx->streams[this->video_stream_index]->codecpar;

    #ifdef DEBUG
    std::cout << "Found Codec " << codecpar->codec_id << "\n";
    #endif
    this->codec = avcodec_find_decoder(this->codecpar->codec_id);
    if (!this->codec) {
        std::cerr << "Decoder not found!\n";
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }
    this->codec_ctx = avcodec_alloc_context3(this->codec);
    if (avcodec_parameters_to_context(this->codec_ctx, this->codecpar) < 0) {
        std::cerr << "Error while copying codec parameters!\n";
        avcodec_free_context(&this->codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }
    if (avcodec_open2(this->codec_ctx, this->codec, NULL) < 0) {
        std::cerr << "Error while opening decoder!\n";
        avcodec_free_context(&this->codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }
    return 0;
}


// openOutput, opens output file
int FFmpegWrapper::openOutput(){
    this->out_fmt_ctx = NULL;
    avformat_alloc_output_context2(&this->out_fmt_ctx, NULL, NULL, std::string(this->outputFilename).c_str());
    if(!this->out_fmt_ctx){
        std::cerr << "Cannot create output context!\n";
        avcodec_free_context(&this->codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }
    this->out_stream = avformat_new_stream(this->out_fmt_ctx, NULL);
    if(!this->out_stream){
        std::cerr << "Cannot create output video stream!\n";
        avcodec_free_context(&this->codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }

    this->out_codec_ctx = avcodec_alloc_context3(this->codec);
    if(!this->out_codec_ctx){
        std::cerr << "Cannot create output codec context!\n";
        avcodec_free_context(&this->codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }

    this->out_codec_ctx->width = this->dst_width;
    this->out_codec_ctx->height = this->dst_height;
    this->out_codec_ctx->pix_fmt = this->codec_ctx->pix_fmt;
    this->out_codec_ctx->time_base = this->codec_ctx->time_base;
    this->out_codec_ctx->framerate = this->codec_ctx->framerate;
    this->out_codec_ctx->bit_rate = this->codec_ctx->bit_rate;

    if(avcodec_open2(this->out_codec_ctx, this->codec, NULL)){
        std::cerr << "Cannot open codec for output!\n";
        avcodec_free_context(&this->codec_ctx);
        avcodec_free_context(&this->out_codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }

    if(avcodec_parameters_from_context(this->out_stream->codecpar, this->out_codec_ctx) < 0){
        std::cerr << "Cannot copy params to output stream!\n";
        avcodec_free_context(&this->codec_ctx);
        avcodec_free_context(&this->out_codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }

    if(!(out_fmt_ctx->oformat->flags & AVFMT_NOFILE)){
        if(avio_open(&this->out_fmt_ctx->pb, this->outputFilename.c_str(), AVIO_FLAG_WRITE) < 0){
            std::cerr << "Cannot open output file!\n";
            avcodec_free_context(&this->codec_ctx);
            avcodec_free_context(&this->out_codec_ctx);
            avformat_close_input(&this->fmt_ctx);
            return -1;
        }
    }

    if(avformat_write_header(this->out_fmt_ctx, NULL) < 0){
        std::cerr << "Cannot write header for output file!\n";
        avcodec_free_context(&this->codec_ctx);
        avcodec_free_context(&this->out_codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }

    return 0;
}

// addFilter, adds string representation of filter into std::vector<std::string> filters
void FFmpegWrapper::addFilter(const std::string_view filter){
    this->filters.push_back(std::string(filter));
}


// process, applies all filters
int FFmpegWrapper::process(){
    AVPacket* packet = av_packet_alloc();
    AVFrame* frame = av_frame_alloc();
    AVFrame* frame_rgb = av_frame_alloc();
    
    int num_bytes = av_image_get_buffer_size(this->out_codec_ctx->pix_fmt, this->dst_width, this->dst_height, 1);
    uint8_t* buffer = (uint8_t*)av_malloc(num_bytes * sizeof(uint8_t));
    if (!buffer) {
        std::cerr << "Cannot allocate buffer for frame_rgb.\n";
        return -1;
    }

    av_image_fill_arrays(frame_rgb->data, frame_rgb->linesize, buffer, this->out_codec_ctx->pix_fmt, this->dst_width, this->dst_height, 1);
    frame_rgb->width  = this->dst_width;
    frame_rgb->height = this->dst_height;
    frame_rgb->format = this->dst_pix_fmt;

    this->openInput();
    this->openOutput();

    int src_width = this->codecpar->width;
    int src_height = this->codecpar->height;
    this->src_pix_fmt = this->codec_ctx->pix_fmt;
    this->dst_pix_fmt = this->out_codec_ctx->pix_fmt;

    #ifdef DEBUG
    std::cout << src_width << "\n" << src_height << "\n" << this->src_pix_fmt << "\n"
    << this->dst_width << "\n" << this->dst_height << "\n" << this->dst_pix_fmt << "\n";
    #endif

    SwsContext* sws_ctx = sws_getContext(src_width, src_height, this->src_pix_fmt,
        this->dst_width, this->dst_height, this->dst_pix_fmt,
        SWS_BILINEAR, NULL, NULL, NULL);
    if (!sws_ctx) {
    std::cerr << "Error initializing swscontext!\n";
    return -1;
    }

    while(av_read_frame(this->fmt_ctx, packet) >= 0){
        if(packet->stream_index == this->video_stream_index){
            if(avcodec_send_packet(this->codec_ctx, packet) == 0){
                while(avcodec_receive_frame(this->codec_ctx, frame) == 0){
                    // Frame transforms
                    sws_scale(sws_ctx, frame->data, frame->linesize, 0, src_height,
                        frame_rgb->data, frame_rgb->linesize);
                    frame_rgb->pts = frame->pts;
                    // Sending frame
                    if(avcodec_send_frame(this->out_codec_ctx, frame_rgb) < 0){
                        std::cerr << "Cannot send frame from codec in output!\n";
                        avcodec_free_context(&this->codec_ctx);
                        avcodec_free_context(&this->out_codec_ctx);
                        avformat_close_input(&this->fmt_ctx);
                        av_frame_free(&frame);
                        av_frame_free(&frame_rgb);
                        av_packet_free(&packet);
                        return -1;
                    }

                    AVPacket* pkt = av_packet_alloc();
                    while(avcodec_receive_packet(this->out_codec_ctx, pkt) == 0){
                        pkt->stream_index = this->out_stream->index;
                        av_packet_rescale_ts(pkt, this->out_codec_ctx->time_base, this->out_stream->time_base);
                        if(av_interleaved_write_frame(this->out_fmt_ctx, pkt) < 0){
                            std::cerr << "Cannot write frame!\n";
                            avcodec_free_context(&this->codec_ctx);
                            avcodec_free_context(&this->out_codec_ctx);
                            avformat_close_input(&this->fmt_ctx);
                            av_frame_free(&frame);
                            av_frame_free(&frame_rgb);
                            av_packet_free(&pkt);
                            av_packet_free(&packet);
                            return -1;
                        }
                        av_packet_unref(pkt);
                    }   
                    av_frame_unref(frame);
                }
            }
        }
        av_packet_unref(packet);
    }

    av_frame_free(&frame);
    av_frame_free(&frame_rgb);
    av_packet_free(&packet);
    avcodec_free_context(&this->codec_ctx);
    avcodec_free_context(&this->out_codec_ctx);
    avformat_close_input(&this->fmt_ctx);

    // std::stringstream parseFilterSS;
    // std::string parameter;
    // std::string operation;
    // for(std::string filter:filters){
    //     std::vector<std::string> parameters;
    //     parseFilterSS << filter;

    //     parseFilterSS >> operation;
        
    //     while(parseFilterSS >> parameter)
    //         parameters.push_back(parameter);

    //     #ifdef DEBUG
    //         std::cout << operation << " ";
    //         for(std::string parameter: parameters)
    //             std::cout << parameter << " ";
    //         std::cout << std::endl;
    //         std::stringstream().swap(parseFilterSS);
    //     #endif
    // }

    return 0;
}