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
    inputFilename(inputFilename), outputFilename(outputFilename), outputCodecStr(outputCodec), dst_width(dst_width), dst_height(dst_height), allFiltersStr(""){};

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

    AVRational stream_time_base = this->fmt_ctx->streams[this->video_stream_index]->time_base;
    if (stream_time_base.num > 0 && stream_time_base.den > 0) {
        this->codec_ctx->time_base = stream_time_base;
    } else if (this->codec_ctx->framerate.num > 0 && this->codec_ctx->framerate.den > 0) {
        this->codec_ctx->time_base = AVRational{this->codec_ctx->framerate.den, this->codec_ctx->framerate.num};
    } else {
        this->codec_ctx->time_base = AVRational{1, 60}; // Запасное значение для 60 FPS
    }

    this->src_pix_fmt = this->codec_ctx->pix_fmt;

    #ifdef DEBUG
    std::cout << "Input time_base: " << this->codec_ctx->time_base.num << "/" << this->codec_ctx->time_base.den << "\n";
    std::cout << "Input framerate: " << this->codec_ctx->framerate.num << "/" << this->codec_ctx->framerate.den << "\n";
    #endif
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

    this->output_codec = avcodec_find_encoder_by_name(this->outputCodecStr.c_str());
    if (!this->output_codec) {
        std::cerr << "Encoder not found for " << this->outputCodecStr << "!\n";
        avcodec_free_context(&this->codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }

    this->out_codec_ctx = avcodec_alloc_context3(this->output_codec);
    if(!this->out_codec_ctx){
        std::cerr << "Cannot create output codec context!\n";
        avcodec_free_context(&this->codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        return -1;
    }
    this->out_codec_ctx->width = this->dst_width;
    this->out_codec_ctx->height = this->dst_height;
    this->out_codec_ctx->pix_fmt = AV_PIX_FMT_YUV420P;
    this->out_codec_ctx->framerate = this->codec_ctx->framerate;
    this->out_codec_ctx->time_base = this->codec_ctx->time_base;
    // this->out_codec_ctx->bit_rate = this->codec_ctx->bit_rate;

    this->out_stream->time_base = this->out_codec_ctx->time_base;
    #ifdef DEBUG
    std::cout << "dst_width = " << this->out_codec_ctx->width << ", dst_height = " << this->out_codec_ctx->height << ", timebase = " << 
    this->out_codec_ctx->time_base.num << " / " << this->out_codec_ctx->time_base.den << ", pix_fmt = " << this->out_codec_ctx->pix_fmt << ", framerate = " << 
    this->out_codec_ctx->framerate.num << " / " << this->out_codec_ctx->framerate.den << ", bit_rate = " << this->out_codec_ctx->bit_rate << "\n";
    #endif

    AVDictionary* opts = NULL;
    av_dict_set(&opts, "crf", "23", 0); // Quality
    av_dict_set(&opts, "preset", "medium", 0); // Preset
    if(avcodec_open2(this->out_codec_ctx, this->output_codec, &opts)){
        std::cerr << "Cannot open codec for output!\n";
        avcodec_free_context(&this->codec_ctx);
        avcodec_free_context(&this->out_codec_ctx);
        avformat_close_input(&this->fmt_ctx);
        av_dict_free(&opts);
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

    this->dst_pix_fmt = this->out_codec_ctx->pix_fmt;
    
    #ifdef DEBUG
    std::cout << "Dst pix fmt = " << this->dst_pix_fmt << "\n";
    #endif
    return 0;
}

// addFilter, adds string representation of filter into std::vector<std::string> filters
void FFmpegWrapper::addFilter(const std::string_view filter){
    this->filters.push_back(std::string(filter));
    this->allFiltersStr += std::string(filter);

}

int FFmpegWrapper::initFilters(){
    this->filter_graph = avfilter_graph_alloc();
    if(!this->filter_graph){
        std::cerr << "Cannot create filter graph!\n";
        return -1;
    }

    const AVFilter* buffersrc = avfilter_get_by_name("buffer");
    std::ostringstream src_args;
    src_args << "video_size=" << this->codec_ctx->width << "x" << this->codec_ctx->height
             << ":pix_fmt=" << this->src_pix_fmt
             << ":time_base=" << this->fmt_ctx->streams[this->video_stream_index]->time_base.num << "/"
             << this->fmt_ctx->streams[this->video_stream_index]->time_base.den;
    
    if(avfilter_graph_create_filter(&this->buffer_src_ctx, buffersrc, "in", src_args.str().c_str(), NULL, this->filter_graph) < 0){
        std::cerr << "Cannot create buffer source!\n";
        avfilter_graph_free(&this->filter_graph);
        return -1;
    }

    const AVFilter* buffersink = avfilter_get_by_name("buffersink");
    if(avfilter_graph_create_filter(&this->buffer_sink_ctx, buffersink, "out", NULL, NULL, this->filter_graph) < 0){
        std::cerr << "Cannot create buffer sink!\n";
        avfilter_graph_free(&this->filter_graph);
        return -1;
    }

    std::string filter_desc;
    for(const auto& filter: this->filters){
        if(!filter_desc.empty())
            filter_desc += ",";
        filter_desc += filter;
        #ifdef DEBUG
        std::cout << "Filter: " << filter << "\n";
        #endif
    }
    if(filter_desc.empty())
        filter_desc = "null";

    AVFilterInOut* outputs = avfilter_inout_alloc();
    AVFilterInOut* inputs = avfilter_inout_alloc();
    outputs->name = av_strdup("in");
    outputs->filter_ctx = this->buffer_src_ctx;
    outputs->pad_idx = 0;
    outputs->next = NULL;
    inputs->name = av_strdup("out");
    inputs->filter_ctx = this->buffer_sink_ctx;
    inputs->pad_idx = 0;
    inputs->next = NULL;

    if(avfilter_graph_parse_ptr(filter_graph, filter_desc.c_str(), &inputs, &outputs, NULL) < 0){
        std::cerr << "Cannot parse filter graph!\n";
        avfilter_inout_free(&inputs);
        avfilter_inout_free(&outputs);
        avfilter_graph_free(&this->filter_graph);
        return -1;
    }
    avfilter_inout_free(&inputs);
    avfilter_inout_free(&outputs);

    if(avfilter_graph_config(filter_graph, NULL) < 0){
        std::cerr << "Cannot configure filter graph!\n";
        avfilter_graph_free(&this->filter_graph);
        return -1;
    }

    return 0;
}

// process, applies all filters
int FFmpegWrapper::process(){
    #ifdef DEBUG
    std::cout << "called process method\n";
    #endif

    this->openInput();
    if(this->initFilters()){
        std::cerr << "Error while initializing filters!\n";
        return -1;
    }    
    this->openOutput();

    #ifdef DEBUG
    std::cout << "Input duration: " << this->fmt_ctx->duration / AV_TIME_BASE << " seconds\n";
    std::cout << "Input framerate: " << this->codec_ctx->framerate.num << "/" << this->codec_ctx->framerate.den << "\n";
    std::cout << "Input time_base: " << this->codec_ctx->time_base.num << "/" << this->codec_ctx->time_base.den << "\n";
    // std::cout << "Input PTS: " << frame->pts << ", Output PTS: " << frame_rgb->pts << "\n";
    //         << ", Output time_base: " << this->out_codec_ctx->time_base.num << "/" << this->out_codec_ctx->time_base.den << "\n";
    #endif

    AVPacket* packet = av_packet_alloc();
    AVFrame* frame = av_frame_alloc();
    AVFrame* frame_rgb = av_frame_alloc();
    
    int num_bytes = av_image_get_buffer_size(this->dst_pix_fmt, this->dst_width, this->dst_height, 1);
    uint8_t* buffer = (uint8_t*)av_malloc(num_bytes * sizeof(uint8_t));
    if (!buffer) {
        std::cerr << "Cannot allocate buffer for frame_rgb.\n";
        return -1;
    }
    #ifdef DEBUG
    std::cout << "alloceted data\n";
    #endif
    av_image_fill_arrays(frame_rgb->data, frame_rgb->linesize, buffer, this->dst_pix_fmt, this->dst_width, this->dst_height, 1);
    frame_rgb->width  = this->dst_width;
    frame_rgb->height = this->dst_height;
    frame_rgb->format = this->dst_pix_fmt;
    #ifdef DEBUG
    std::cout << "av_image_fill_arrays done\n";
    #endif
    #ifdef DEBUG
    std::cout << "opened input and output\n";
    #endif

    int src_width = this->codecpar->width;
    int src_height = this->codecpar->height;
    
    #ifdef DEBUG
    std::cout << "params set\n";
    #endif
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
                    if (av_buffersrc_write_frame(buffer_src_ctx, frame) < 0) {
                        std::cerr << "Ошибка при отправке кадра в граф фильтров!\n";
                        break;
                    }
                    
                    while (av_buffersink_get_frame(buffer_sink_ctx, frame_rgb) >= 0) {
                        frame_rgb->pts = av_rescale_q(frame->pts, this->codec_ctx->time_base, this->out_codec_ctx->time_base);

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
                        av_packet_free(&pkt);
                        av_frame_unref(frame);
                    }
                    av_frame_unref(frame_rgb);
                }
            }
        }
        av_packet_unref(packet);
    }

    avcodec_send_frame(this->out_codec_ctx, NULL);
    AVPacket* pkt = av_packet_alloc();
    while (avcodec_receive_packet(this->out_codec_ctx, pkt) == 0) {
        pkt->stream_index = this->out_stream->index;
        av_packet_rescale_ts(pkt, this->out_codec_ctx->time_base, this->out_stream->time_base);
        av_interleaved_write_frame(this->out_fmt_ctx, pkt);
        av_packet_unref(pkt);
    }
    av_packet_free(&pkt);

    av_write_trailer(this->out_fmt_ctx);

    av_frame_free(&frame);
    av_frame_free(&frame_rgb);
    av_packet_free(&packet);
    avcodec_free_context(&this->codec_ctx);
    avcodec_free_context(&this->out_codec_ctx);
    avformat_close_input(&this->fmt_ctx);
    av_free(buffer);
    sws_freeContext(sws_ctx);
    if (!(this->out_fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        avio_closep(&this->out_fmt_ctx->pb);
    }
    avformat_free_context(this->out_fmt_ctx);

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