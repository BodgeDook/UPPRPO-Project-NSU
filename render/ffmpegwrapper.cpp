#include "ffmpegwrapper.hpp"
#include <sstream>
#include <string>
#include <iostream>

//  Constructor, gets inputFilename and outputFilename.
FFmpegWrapper::FFmpegWrapper(Settings settings, std::vector<Track> tracks): settings(settings), tracks(tracks){};

// type: "video" | "audio"
void FFmpegWrapper::configureTimeline(std::string type){
    std::vector<std::pair<int, int>> time_markers; 
    for(auto& track: tracks){
        if(track.type == type){
            for(auto& item: track.items)
                time_markers.push_back({item.startFrame, item.endFrame});
        }
    }

    if(type == std::string("audio"))
        this->audio_time_markers = time_markers;
    else if(type == std::string("video"))
        this->video_time_markers = time_markers;
}

int FFmpegWrapper::extractAudio(std::string& input_file, double from_sec, double to_sec){
    int err;
    std::string output_file = "tmp/tmp_audio.wav";

    AVFormatContext *input_fmt_ctx = avformat_alloc_context(), *output_fmt_ctx = avformat_alloc_context();
    AVCodecContext *decode_ctx, *encode_ctx; 
    AVRational time_base;
    SwrContext* swr_ctx = nullptr;
    int audio_stream_index = -1;

    #ifdef DEBUG
        std::cout << "Allocated context\n";
    #endif

    // Open input file
    if((err = avformat_open_input(&input_fmt_ctx, input_file.c_str(), nullptr, nullptr)) < 0){
        std::cerr << "Unable to open " << input_file << ". Error code: " << err << "\n";
        return 1;
    }

    // Find streams info
    if(avformat_find_stream_info(input_fmt_ctx, nullptr) < 0){
        std::cerr << "Unable to find stream info\n";
        return 1;
    }


    // Find audio stream
    for(int i = 0; i < input_fmt_ctx->nb_streams; i++){
        if(input_fmt_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_AUDIO){
            audio_stream_index = i;
            time_base = input_fmt_ctx->streams[i]->time_base;

            #ifdef DEBUG
                std::cout << "Audio stream index: " << audio_stream_index << ". Time base: " << time_base.num << " / " << time_base.den << "\n";
            #endif

            break;
        }
    }

    // Check if we found anything
    if(audio_stream_index == -1){
        // skip this and fill with zeros or smth
    }
    
    // Rescaling timestamps "from" and "to" to pts
    long long from_pts = av_rescale_q(static_cast<long long>(from_sec * AV_TIME_BASE), AV_TIME_BASE_Q, time_base);
    long long to_pts = av_rescale_q(static_cast<long long>(to_sec * AV_TIME_BASE), AV_TIME_BASE_Q, time_base);
    long long output_pts = 0;

    #ifdef DEBUG
        std::cout << "Cutting audio " << input_file << " from " << from_pts << " to " << to_pts << "\n";
    #endif

    // Decoder setup
    const AVCodec* decoder = avcodec_find_decoder(input_fmt_ctx->streams[audio_stream_index]->codecpar->codec_id);
    decode_ctx = avcodec_alloc_context3(decoder);
    avcodec_parameters_to_context(decode_ctx, input_fmt_ctx->streams[audio_stream_index]->codecpar);
    avcodec_open2(decode_ctx, decoder, nullptr);

    #ifdef DEBUG
        std::cout << "Decoded setted up\n";
    #endif

    // Encoder setup
    const AVCodec* encoder = avcodec_find_encoder_by_name("pcm_s16le"); // libmp3lame | pcm_s32le | pcm_s16le
    encode_ctx = avcodec_alloc_context3(encoder);
    encode_ctx->sample_rate = decode_ctx->sample_rate;
    encode_ctx->ch_layout = decode_ctx->ch_layout;
    encode_ctx->sample_fmt = encoder->sample_fmts[0];
    std::cout << "Sample format: " << encode_ctx->sample_fmt;
    encode_ctx->bit_rate = decode_ctx->bit_rate;
    // encode_ctx->time_base = time_base;
    encode_ctx->time_base = {1, encode_ctx->sample_rate};
    avcodec_open2(encode_ctx, encoder, nullptr);

    // Set up swresample to convert samples format
    if(swr_alloc_set_opts2(&swr_ctx, &encode_ctx->ch_layout, encode_ctx->sample_fmt, encode_ctx->sample_rate,
                           &decode_ctx->ch_layout, decode_ctx->sample_fmt, decode_ctx->sample_rate, 0, nullptr) < 0){
        std::cerr << "Unable to initialize swresample\n";
        return 1;
    }

    if (swr_init(swr_ctx) < 0) {
        std::cerr << "Failed to initialize SWR context\n";
        return 1;
    }

    #ifdef DEBUG
        std::cout << "Encoder setted up\n";
    #endif
    
    // Create output temporary file
    avformat_alloc_output_context2(&output_fmt_ctx, nullptr, nullptr, output_file.c_str());
    AVStream* out_stream = avformat_new_stream(output_fmt_ctx, nullptr);
    avcodec_parameters_from_context(out_stream->codecpar, encode_ctx);
    out_stream->time_base = encode_ctx->time_base;

    #ifdef DEBUG
        std::cout << "Output temp file created\n";
    #endif

    if(!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)){
        avio_open(&output_fmt_ctx->pb, output_file.c_str(), AVIO_FLAG_WRITE);
    }

    #ifdef DEBUG
        std::cout << "Output temp file opened\n";
    #endif


    // Write header to the output file
    avformat_write_header(output_fmt_ctx, nullptr);

    #ifdef DEBUG
        std::cout << "Header was written\n";
    #endif


    // Packets processing
    AVPacket pkt;
    AVFrame* frame = av_frame_alloc();
    AVFrame* converted_frame = av_frame_alloc();
    av_init_packet(&pkt);

    #ifdef DEBUG
        std::cout << "Starting processing packets\n";
    #endif

    while(av_read_frame(input_fmt_ctx, &pkt) >= 0){
        #ifdef DEBUG
            std::cout << "Packet PTS: " << pkt.pts << " | DTS: " << pkt.dts << "\n";
        #endif


        if(pkt.stream_index == audio_stream_index){
            int send_ret = avcodec_send_packet(decode_ctx, &pkt);
            if (send_ret < 0) {
                std::cerr << "Error sending packet to decoder: " << send_ret << "\n";
                continue;
            }
            while(true){
                int ret = avcodec_receive_frame(decode_ctx, frame);
                if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
                if (ret < 0) {
                    std::cerr << "Error receiving frame: " << ret << "\n";
                    break;
                }

                if (frame->pts == AV_NOPTS_VALUE) {
                    std::cerr << "Frame PTS is not set, skipping\n";
                    continue;
                }

                #ifdef DEBUG
                    std::cout << "Frame PTS: " << frame->pts << " | nb_samples: " << frame->nb_samples << "\n";
                #endif

                if(frame->pts != AV_NOPTS_VALUE){
                    long long frame_pts = frame->pts;
                    long long frame_end_pts = frame_pts + frame->nb_samples;

                    if(frame_end_pts > from_pts && frame_pts < to_pts){ // 
                        int start_sample = (frame_pts < from_pts) ? (from_pts - frame_pts) : 0;
                        int end_sample = (frame_end_pts > to_pts) ? (to_pts - frame_pts) : frame->nb_samples;
                        int sample_count = end_sample - start_sample; // frame->nb_samples

                        if (sample_count <= 0) {
                            #ifdef DEBUG
                                std::cout << "Invalid sample count: " << sample_count << ", skipping\n";
                            #endif
                            continue;
                        }

                        #ifdef DEBUG
                            std::cout << "Start sample: " << start_sample << ", end sample: " << end_sample << ", sample count: " << sample_count << "\n";
                        #endif

                        // Set up converted frame
                        converted_frame->format = encode_ctx->sample_fmt;
                        converted_frame->ch_layout = decode_ctx->ch_layout;
                        converted_frame->sample_rate = decode_ctx->sample_rate;
                        converted_frame->nb_samples = sample_count;

                        std::cout << "debug1\n";

                        // Alloc buffer for converted frame
                        if (av_frame_get_buffer(converted_frame, 0) < 0) {
                            std::cerr << "Could not allocate converted frame buffer\n";
                            return 1;
                        }
                        
                        // Conver samples
                        uint8_t** src_data = new uint8_t*[frame->ch_layout.nb_channels];
                        for(int i = 0; i < frame->ch_layout.nb_channels; i++){
                            int bytes_per_sample = av_get_bytes_per_sample(decode_ctx->sample_fmt);
                            if(bytes_per_sample == 0){
                                std::cerr << "Bytes per sample == 0\n";
                                return 1;
                            }
                            src_data[i] = frame->data[i] + start_sample * bytes_per_sample;
                        }

                        std::cout << "debug2\n";

                        int conv_samples = swr_convert(swr_ctx, converted_frame->data, sample_count,
                                                       (const uint8_t**)src_data, sample_count);

                        std::cout << "debug3\n";

                        delete[] src_data;

                        if (conv_samples < 0) {
                            std::cerr << "Error converting audio\n";
                            return 1;
                        }

                        converted_frame->pts = output_pts;
                        output_pts += sample_count;
                        
                        // Send converted frame to the encoder
                        if(avcodec_send_frame(encode_ctx, converted_frame) < 0){
                            std::cerr << "Error while sending frame\n";
                            return 1;
                        }

                        std::cout << "debug4\n";

                        AVPacket enc_pkt;
                        av_init_packet(&enc_pkt);

                        while(avcodec_receive_packet(encode_ctx, &enc_pkt) == 0){
                            enc_pkt.stream_index = 0;
                            av_packet_rescale_ts(&enc_pkt, encode_ctx->time_base, out_stream->time_base);
                            if(av_interleaved_write_frame(output_fmt_ctx, &enc_pkt) < 0){
                                std::cerr << "Error while writing packet\n";
                                return 1;
                            }
                            av_packet_unref(&enc_pkt);
                        }

                        std::cout << "debug5\n";
                    }
                }
            }
        }
        av_packet_unref(&pkt);
        std::cout << "debug6\n";
    }

    // Encoder reset
    avcodec_send_frame(encode_ctx, nullptr);
    AVPacket enc_pkt;
    av_init_packet(&enc_pkt);
    
    while(avcodec_receive_packet(encode_ctx, &enc_pkt) == 0){
        enc_pkt.stream_index = 0;
        av_packet_rescale_ts(&enc_pkt, encode_ctx->time_base, out_stream->time_base);
        av_interleaved_write_frame(output_fmt_ctx, &enc_pkt);
        av_packet_unref(&enc_pkt);
    }

    av_write_trailer(output_fmt_ctx);
    av_frame_free(&frame);
    av_frame_free(&converted_frame);

    if(input_fmt_ctx) avformat_close_input(&input_fmt_ctx);
    if(output_fmt_ctx && !(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) avio_closep(&output_fmt_ctx->pb);
    if(output_fmt_ctx) avformat_free_context(output_fmt_ctx);
    if(decode_ctx) avcodec_free_context(&decode_ctx);
    if(encode_ctx) avcodec_free_context(&encode_ctx);
    return 0;
}

int mergePairAudio(){

}

int mergePairVideo(){

}

int mergeFullAudio(){

}

int mergeFullVideo(){

}


void FFmpegWrapper::process(std::string src){
    this->configureTimeline(std::string("audio"));
    this->configureTimeline(std::string("video"));

    #ifdef DEBUG
        std::cout << "Done configurng timeline\n";
    #endif

    extractAudio(src, 10, 20);
}