
#include <iostream>


extern "C" {
    #include <libavformat/avformat.h>
    #include <libswscale/swscale.h>
    #include <libavcodec/avcodec.h>
}

// #include <rapidjson/allocators.h>

int main(const int argc, const char** argv) {
    if(argc < 2){
        std::cout << "Enter filename\n";
        return -1;
    }
        
    AVFormatContext* fmt_ctx = avformat_alloc_context();

    if (avformat_open_input(&fmt_ctx, argv[1], NULL, NULL) < 0) {
        std::cerr << "Error while opening a file! (avformat_open_input)\n";
        return -1;
    }
    if (avformat_find_stream_info(fmt_ctx, NULL) < 0) {
        std::cerr << "Error while opening a file! (avformat_find_stream_info)\n";
        return -1;
    }

    int video_stream_index = -1;
    for (unsigned int i = 0; i < fmt_ctx->nb_streams; i++) {
        if (fmt_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
            video_stream_index = i;
            break;
        }
    }
    if (video_stream_index == -1) {
        std::cerr << "Video stream not found!\n";
        return -1;
    }

    AVCodecParameters* codecpar = fmt_ctx->streams[video_stream_index]->codecpar;
    std::cout << "Found Codec " << codecpar->codec_id << "\n";

    const AVCodec* codec = avcodec_find_decoder(codecpar->codec_id);
    if (!codec) {
        std::cerr << "Decoder not found!\n";
        return -1;
    }
    AVCodecContext* codec_ctx = avcodec_alloc_context3(codec);
    if (avcodec_parameters_to_context(codec_ctx, codecpar) < 0) {
        std::cerr << "Error while copying codec parameters!\n";
        return -1;
    }
    if (avcodec_open2(codec_ctx, codec, NULL) < 0) {
        std::cerr << "Error while opening decoder!\n";
        return -1;
    }

    int src_width = codecpar->width;
    int src_height = codecpar->height;
    AVPixelFormat src_pix_fmt = static_cast<AVPixelFormat>(codecpar->format);
    int dst_width = 640; // Ширина целевого изображения
    int dst_height = 480; // Высота целевого изображения
    AVPixelFormat dst_pix_fmt = src_pix_fmt; // Формат пикселей целевого изображения

    // Setting up output file
    AVFormatContext* out_fmt_ctx = NULL;
    avformat_alloc_output_context2(&out_fmt_ctx, NULL, NULL, "output_video.mp4");
    if(!out_fmt_ctx){
        std::cerr << "Cannot create output context!\n";
        return -1;
    }

    AVStream* out_stream = avformat_new_stream(out_fmt_ctx, NULL);
    if(!out_stream){
        std::cerr << "Cannot create output video stream!\n";
        return -1;
    }

    AVCodecContext* out_codec_ctx = avcodec_alloc_context3(codec);
    if(!out_codec_ctx){
        std::cerr << "Cannot create output codec context!\n";
        return -1;
    }
    // Codec params
    out_codec_ctx->width = dst_width;
    out_codec_ctx->height = dst_height;
    out_codec_ctx->pix_fmt = codec_ctx->pix_fmt;
    out_codec_ctx->time_base = codec_ctx->time_base;
    out_codec_ctx->framerate = codec_ctx->framerate;
    out_codec_ctx->bit_rate = codec_ctx->bit_rate;

    if(avcodec_open2(out_codec_ctx, codec, NULL)){
        std::cerr << "Cannot open coded for output!\n";
        return -1;
    }
    
    if(avcodec_parameters_from_context(out_stream->codecpar, out_codec_ctx) < 0){
        std::cerr << "Cannot copy params to output stream!\n";
        return -1;
    }

    if(!(out_fmt_ctx->oformat->flags & AVFMT_NOFILE)){
        if(avio_open(&out_fmt_ctx->pb, "output_video.mp4", AVIO_FLAG_WRITE) < 0){
            std::cerr << "Cannot open output file!\n";
            return -1;
        }
    }

    if(avformat_write_header(out_fmt_ctx, NULL) < 0){
        std::cerr << "Cannot write header for output file!\n";
        return -1;
    }

    // Processing frames

    SwsContext* sws_ctx = sws_getContext(src_width, src_height, src_pix_fmt,
        dst_width, dst_height, dst_pix_fmt,
        SWS_BILINEAR, NULL, NULL, NULL);
    if (!sws_ctx) {
    std::cerr << "Error initializing swscontext!\n";
    return -1;
    }

    AVPacket* packet = av_packet_alloc();
    AVFrame* frame = av_frame_alloc();
    AVFrame* frame_rgb = av_frame_alloc();

    while (av_read_frame(fmt_ctx, packet) >= 0) {
        if (packet->stream_index == video_stream_index) {
            if (avcodec_send_packet(codec_ctx, packet) == 0) {
                while (avcodec_receive_frame(codec_ctx, frame) == 0) {
                    // Преобразование кадра
                    sws_scale(sws_ctx, frame->data, frame->linesize, 0, src_height,
                              frame_rgb->data, frame_rgb->linesize);
                    // Обработка преобразованного кадра
                    AVFrame* frame = av_frame_alloc();
                    // Заполните frame данными изменённого кадра

                    if (avcodec_send_frame(out_codec_ctx, frame) < 0) {
                        std::cerr << "Cannot send frame from codec in output!\n";
                        return -1;
                    }

                    AVPacket* pkt = av_packet_alloc();
                    while (avcodec_receive_packet(out_codec_ctx, pkt) == 0) {
                        pkt->stream_index = out_stream->index;
                        av_packet_rescale_ts(pkt, out_codec_ctx->time_base, out_stream->time_base);
                        if (av_interleaved_write_frame(out_fmt_ctx, pkt) < 0) {
                            std::cerr << "Cannot write frame!\n";
                            return -1;
                        }
                        av_packet_unref(pkt);
                    }

                    av_frame_free(&frame);
                    av_packet_free(&pkt);
                }
            }
        }
        av_packet_unref(packet);
    }
    
    av_dump_format(fmt_ctx, 0, argv[1], 0);

    av_frame_free(&frame);
    av_frame_free(&frame_rgb);
    av_packet_free(&packet);
    sws_freeContext(sws_ctx);
    avcodec_free_context(&codec_ctx);
    avformat_close_input(&fmt_ctx);

    std::cout << "Done!\n";
    return 0;
}
