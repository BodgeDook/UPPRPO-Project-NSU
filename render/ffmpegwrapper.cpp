#include "ffmpegwrapper.hpp"
#include <sstream>
#include <string>
#include <iostream>

FFmpegWrapper::FFmpegWrapper(Settings settings, std::vector<Track> tracks): settings(settings), tracks(tracks){};

// type: "video" | "audio"
void FFmpegWrapper::configureTimeline(std::string type){
    std::vector<std::pair<double, double>> time_markers;
    for(auto& track: tracks){
        if(track.type == type){
            for(auto& item: track.items)
                time_markers.push_back({item.begin, item.end});
        }
    }

    if(type == std::string("audio"))
        this->audio_time_markers = time_markers;
    else if(type == std::string("video"))
        this->video_time_markers = time_markers;
}

int FFmpegWrapper::extractAudio(std::string& input_file, std::string& output_file, double from_sec, double to_sec) {
    int ret = 0;

    AVFormatContext *input_fmt_ctx = nullptr;
    AVFormatContext *output_fmt_ctx = nullptr;
    AVCodecContext *decode_ctx = nullptr;
    AVCodecContext *encode_ctx = nullptr;
    SwrContext* swr_ctx = nullptr;
    AVPacket *pkt = nullptr;
    AVPacket *enc_pkt = nullptr;
    AVFrame *frame = nullptr;
    AVFrame *converted_frame = nullptr;
    AVChannelLayout dec_ch_layout{};

    int audio_stream_index = -1;

    av_log_set_level(AV_LOG_DEBUG);

    // Open input file
    if ((ret = avformat_open_input(&input_fmt_ctx, input_file.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Unable to open %s. Error code: %s\n", input_file.c_str(), ret);
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }

    // Find streams info
    if ((ret = avformat_find_stream_info(input_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Unable to find stream info. Error code: %s\n", ret);
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }

    // Find audio stream
    audio_stream_index = av_find_best_stream(input_fmt_ctx, AVMEDIA_TYPE_AUDIO, -1, -1, nullptr, 0);
    if (audio_stream_index < 0) {
        av_log(NULL, AV_LOG_ERROR, "Unable to find audio stream in %s\n", input_file.c_str());
        ret = AVERROR_STREAM_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }
    AVStream* audio_stream = input_fmt_ctx->streams[audio_stream_index];
    AVRational time_base = audio_stream->time_base;

    // Rescaling timestamps "from" and "to" from seconds to pts (Presentation Timestamps)
    long long from_pts = av_rescale_q(static_cast<long long>(from_sec * AV_TIME_BASE), AV_TIME_BASE_Q, time_base);
    if(to_sec == -1)
        to_sec = av_q2d(audio_stream->time_base) * audio_stream->duration;
    long long to_pts = av_rescale_q(static_cast<long long>(to_sec * AV_TIME_BASE), AV_TIME_BASE_Q, time_base);
    long long output_pts = 0;

    // Decoder setup
    const AVCodec* decoder = avcodec_find_decoder(audio_stream->codecpar->codec_id);
    if (!decoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find decoder\n");
        ret = AVERROR_DECODER_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }
    decode_ctx = avcodec_alloc_context3(decoder);
    if (!decode_ctx) {
        ret = AVERROR(ENOMEM);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }
    avcodec_parameters_to_context(decode_ctx, audio_stream->codecpar);
    if ((ret = avcodec_open2(decode_ctx, decoder, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Failed to open decoder. Error code: %s\n", ret);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }

    // Encoder setup
    const AVCodec* encoder = avcodec_find_encoder_by_name("pcm_s32le"); // WAV без сжатия, 16-bit
    if (!encoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find pcm_s16le encoder\n");
        ret = AVERROR_ENCODER_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }
    encode_ctx = avcodec_alloc_context3(encoder);
    if (!encode_ctx) {
        ret = AVERROR(ENOMEM);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        return ret;
    }

    // Channel layout setup
    if (av_channel_layout_copy(&dec_ch_layout, &decode_ctx->ch_layout) < 0 || dec_ch_layout.nb_channels == 0) {
        av_channel_layout_default(&dec_ch_layout, decode_ctx->ch_layout.nb_channels);
    }
    av_channel_layout_copy(&encode_ctx->ch_layout, &dec_ch_layout);

    // encode_ctx->sample_rate = decode_ctx->sample_rate;
    encode_ctx->sample_rate = this->settings.sample_rate;
    encode_ctx->sample_fmt = encoder->sample_fmts[0];
    encode_ctx->time_base = {1, encode_ctx->sample_rate};

    if ((ret = avcodec_open2(encode_ctx, encoder, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Failed to open encoder. Error code: %s\n", ret);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        av_channel_layout_uninit(&dec_ch_layout);
        return ret;
    }

    // Set up swresample to convert samples format
    if (swr_alloc_set_opts2(&swr_ctx, &encode_ctx->ch_layout, encode_ctx->sample_fmt, encode_ctx->sample_rate,
                           &dec_ch_layout, decode_ctx->sample_fmt, decode_ctx->sample_rate, 0, nullptr) < 0) {
        ret = AVERROR(ENOMEM);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        av_channel_layout_uninit(&dec_ch_layout);
        swr_free(&swr_ctx);
        return ret;
    }
    if ((ret = swr_init(swr_ctx)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Failed to initialize SWR context. Error code: %s\n", ret);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        av_channel_layout_uninit(&dec_ch_layout);
        swr_free(&swr_ctx);
        return ret;
    }
    
    // Create output temporary file
    avformat_alloc_output_context2(&output_fmt_ctx, nullptr, nullptr, output_file.c_str());
    if (!output_fmt_ctx) {
        ret = AVERROR(ENOMEM);
        avformat_close_input(&input_fmt_ctx);
        avformat_close_input(&output_fmt_ctx);
        avio_closep(&output_fmt_ctx->pb);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        av_channel_layout_uninit(&dec_ch_layout);
        swr_free(&swr_ctx);
        return ret;
    }
    AVStream* out_stream = avformat_new_stream(output_fmt_ctx, nullptr);
    if (!out_stream) {
        ret = AVERROR(ENOMEM);
        avformat_close_input(&input_fmt_ctx);
        avformat_close_input(&output_fmt_ctx);
        avio_closep(&output_fmt_ctx->pb);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        av_channel_layout_uninit(&dec_ch_layout);
        swr_free(&swr_ctx);
        return ret;
    }
    avcodec_parameters_from_context(out_stream->codecpar, encode_ctx);
    out_stream->time_base = encode_ctx->time_base;

    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        if ((ret = avio_open(&output_fmt_ctx->pb, output_file.c_str(), AVIO_FLAG_WRITE)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not open output file '%s'. Error: %s\n", output_file.c_str(), ret);
            avformat_close_input(&input_fmt_ctx);
            avformat_close_input(&output_fmt_ctx);
            avio_closep(&output_fmt_ctx->pb);
            avcodec_free_context(&decode_ctx);
            avcodec_free_context(&encode_ctx);
            av_channel_layout_uninit(&dec_ch_layout);
            swr_free(&swr_ctx);
            return ret;
        }
    }

    if ((ret = avformat_write_header(output_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Error occurred when writing header. Error: %s\n", ret);
        avformat_close_input(&input_fmt_ctx);
        avformat_close_input(&output_fmt_ctx);
        avio_closep(&output_fmt_ctx->pb);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        av_channel_layout_uninit(&dec_ch_layout);
        swr_free(&swr_ctx);
        return ret;
    }

    // Use av_seek_frame to jump to starter point
    if ((ret = av_seek_frame(input_fmt_ctx, audio_stream_index, from_pts, AVSEEK_FLAG_BACKWARD)) < 0) {
        av_log(NULL, AV_LOG_WARNING, "Could not seek to position %f\n", from_sec);
        avformat_close_input(&input_fmt_ctx);
        avformat_close_input(&output_fmt_ctx);
        avio_closep(&output_fmt_ctx->pb);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        av_channel_layout_uninit(&dec_ch_layout);
        swr_free(&swr_ctx);
        return ret;
    }
    avcodec_flush_buffers(decode_ctx);

    // Allocate memory for packets and frames
    pkt = av_packet_alloc();
    enc_pkt = av_packet_alloc();
    frame = av_frame_alloc();
    converted_frame = av_frame_alloc();
    if (!pkt || !enc_pkt || !frame || !converted_frame) {
        ret = AVERROR(ENOMEM);
        avformat_close_input(&input_fmt_ctx);
        avformat_close_input(&output_fmt_ctx);
        avio_closep(&output_fmt_ctx->pb);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        av_channel_layout_uninit(&dec_ch_layout);
        swr_free(&swr_ctx);
        av_packet_free(&pkt);
        av_packet_free(&enc_pkt);
        av_frame_free(&frame);
        av_frame_free(&converted_frame);
        return ret;
    }

    // Main loop
    while (av_read_frame(input_fmt_ctx, pkt) >= 0) {
        if (pkt->stream_index != audio_stream_index) {
            av_packet_unref(pkt);
            continue;
        }

        // Exit condition
        if (pkt->pts > to_pts && pkt->pts != AV_NOPTS_VALUE) {
            av_packet_unref(pkt);
            break;
        }

        if ((ret = avcodec_send_packet(decode_ctx, pkt)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Error sending packet to decoder\n");
            avformat_close_input(&input_fmt_ctx);
            avformat_close_input(&output_fmt_ctx);
            avio_closep(&output_fmt_ctx->pb);
            avcodec_free_context(&decode_ctx);
            avcodec_free_context(&encode_ctx);
            av_channel_layout_uninit(&dec_ch_layout);
            swr_free(&swr_ctx);
            av_packet_free(&pkt);
            av_packet_free(&enc_pkt);
            av_frame_free(&frame);
            av_frame_free(&converted_frame);
            return ret;
        }

        while (ret >= 0) {
            ret = avcodec_receive_frame(decode_ctx, frame);
            if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
            if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "Error receiving frame from decoder\n");
                avformat_close_input(&input_fmt_ctx);
                avformat_close_input(&output_fmt_ctx);
                avio_closep(&output_fmt_ctx->pb);
                avcodec_free_context(&decode_ctx);
                avcodec_free_context(&encode_ctx);
                av_channel_layout_uninit(&dec_ch_layout);
                swr_free(&swr_ctx);
                av_packet_free(&pkt);
                av_packet_free(&enc_pkt);
                av_frame_free(&frame);
                av_frame_free(&converted_frame);
                return ret;
            }

            long long frame_pts = frame->pts;
            if (frame_pts == AV_NOPTS_VALUE) {
                av_frame_unref(frame);
                continue;
            }
            long long frame_end_pts = frame_pts + frame->nb_samples;

            if (frame_end_pts > from_pts && frame_pts < to_pts) {
                int start_sample = (frame_pts < from_pts) ? (from_pts - frame_pts) : 0;
                int end_sample = (frame_end_pts > to_pts) ? (to_pts - frame_pts) : frame->nb_samples;
                int sample_count = end_sample - start_sample;

                if (sample_count <= 0) continue;
                av_frame_unref(converted_frame);

                converted_frame->nb_samples = sample_count;
                converted_frame->ch_layout = encode_ctx->ch_layout;
                converted_frame->format = encode_ctx->sample_fmt;
                converted_frame->sample_rate = encode_ctx->sample_rate;

                if (av_frame_get_buffer(converted_frame, 0) < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Could not allocate converted frame buffer\n");
                    ret = AVERROR(ENOMEM);
                    avformat_close_input(&input_fmt_ctx);
                    avformat_close_input(&output_fmt_ctx);
                    avio_closep(&output_fmt_ctx->pb);
                    avcodec_free_context(&decode_ctx);
                    avcodec_free_context(&encode_ctx);
                    av_channel_layout_uninit(&dec_ch_layout);
                    swr_free(&swr_ctx);
                    av_packet_free(&pkt);
                    av_packet_free(&enc_pkt);
                    av_frame_free(&frame);
                    av_frame_free(&converted_frame);
                    return ret;
                }
                
                const uint8_t** src_data = (const uint8_t**)frame->data;
                if (start_sample > 0) {
                    int plane_size;
                    int line_size;
                    av_samples_get_buffer_size(&plane_size, decode_ctx->ch_layout.nb_channels, frame->nb_samples, decode_ctx->sample_fmt, 1);
                    av_samples_get_buffer_size(&line_size, 1, frame->nb_samples, decode_ctx->sample_fmt, 1);
                    
                    if (av_sample_fmt_is_planar(decode_ctx->sample_fmt)) {
                        for (int i = 0; i < decode_ctx->ch_layout.nb_channels; i++) {
                           if(frame->data[i]) frame->data[i] += line_size / frame->nb_samples * start_sample;
                        }
                    } else {
                        if(frame->data[0]) frame->data[0] += plane_size / frame->nb_samples * start_sample;
                    }
                }

                int conv_samples = swr_convert(swr_ctx, converted_frame->data, sample_count, src_data, sample_count);
                if (conv_samples < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Error converting audio\n");
                    avformat_close_input(&input_fmt_ctx);
                    avformat_close_input(&output_fmt_ctx);
                    avio_closep(&output_fmt_ctx->pb);
                    avcodec_free_context(&decode_ctx);
                    avcodec_free_context(&encode_ctx);
                    av_channel_layout_uninit(&dec_ch_layout);
                    swr_free(&swr_ctx);
                    av_packet_free(&pkt);
                    av_packet_free(&enc_pkt);
                    av_frame_free(&frame);
                    av_frame_free(&converted_frame);
                    return ret;
                }

                converted_frame->pts = output_pts;
                output_pts += conv_samples;

                if (avcodec_send_frame(encode_ctx, converted_frame) >= 0) {
                    while (avcodec_receive_packet(encode_ctx, enc_pkt) == 0) {
                        enc_pkt->stream_index = 0;
                        av_packet_rescale_ts(enc_pkt, encode_ctx->time_base, out_stream->time_base);
                        av_interleaved_write_frame(output_fmt_ctx, enc_pkt);
                        av_packet_unref(enc_pkt);
                    }
                }
            }
            av_frame_unref(frame);
        }
        av_packet_unref(pkt);
    }

    // Flush encoder buffers
    avcodec_send_frame(encode_ctx, nullptr);
    while (avcodec_receive_packet(encode_ctx, enc_pkt) == 0) {
        enc_pkt->stream_index = 0;
        av_packet_rescale_ts(enc_pkt, encode_ctx->time_base, out_stream->time_base);
        av_interleaved_write_frame(output_fmt_ctx, enc_pkt);
        av_packet_unref(enc_pkt);
    }

    av_write_trailer(output_fmt_ctx);

    if (input_fmt_ctx) avformat_close_input(&input_fmt_ctx);
    if (output_fmt_ctx && !(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) avio_closep(&output_fmt_ctx->pb);
    if (output_fmt_ctx) avformat_free_context(output_fmt_ctx);
    if (decode_ctx) avcodec_free_context(&decode_ctx);
    if (encode_ctx) avcodec_free_context(&encode_ctx);
    if (swr_ctx) swr_free(&swr_ctx);
    if (pkt) av_packet_free(&pkt);
    if (enc_pkt) av_packet_free(&enc_pkt);
    if (frame) av_frame_free(&frame);
    if (converted_frame) av_frame_free(&converted_frame);
    av_channel_layout_uninit(&dec_ch_layout);

    return ret < 0 ? 1 : 0;
}

int FFmpegWrapper::extractVideo(std::string& input_file, std::string& output_file, double from_sec, double to_sec){
    int ret = 0;

    AVFormatContext *input_fmt_ctx = nullptr;
    AVFormatContext *output_fmt_ctx = nullptr;
    AVCodecContext *decode_ctx = nullptr;
    AVCodecContext *encode_ctx = nullptr;
    SwrContext* swr_ctx = nullptr;
    AVPacket *pkt = nullptr;
    AVPacket *enc_pkt = nullptr;
    AVFrame *frame = nullptr;
    AVFrame *converted_frame = nullptr;
    AVChannelLayout dec_ch_layout{};

    int video_stream_index = -1;

    if ((ret = avformat_open_input(&input_fmt_ctx, input_file.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Unable to open %s. Error code: %s\n", input_file.c_str(), ret);
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }

    // Find streams info
    if ((ret = avformat_find_stream_info(input_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Unable to find stream info. Error code: %s\n", ret);
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }

    // Find video stream
    video_stream_index = av_find_best_stream(input_fmt_ctx, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (video_stream_index < 0) {
        av_log(NULL, AV_LOG_ERROR, "Unable to find audio stream in %s\n", input_file.c_str());
        ret = AVERROR_STREAM_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }
    AVStream* video_stream = input_fmt_ctx->streams[video_stream_index];
    AVRational time_base = video_stream->time_base;

    // Rescaling timestamps "from" and "to" from seconds to pts (Presentation Timestamps)
    long long from_pts = av_rescale_q(static_cast<long long>(from_sec * AV_TIME_BASE), AV_TIME_BASE_Q, time_base);
    if(to_sec == -1)
        to_sec = av_q2d(video_stream->time_base) * video_stream->duration;
    long long to_pts = av_rescale_q(static_cast<long long>(to_sec * AV_TIME_BASE), AV_TIME_BASE_Q, time_base);
    long long output_pts = 0;

    // Decoder setup
    const AVCodec* decoder = avcodec_find_decoder(video_stream->codecpar->codec_id);
    if (!decoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find decoder\n");
        ret = AVERROR_DECODER_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }
    decode_ctx = avcodec_alloc_context3(decoder);
    if (!decode_ctx) {
        ret = AVERROR(ENOMEM);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }
    avcodec_parameters_to_context(decode_ctx, video_stream->codecpar);
    if ((ret = avcodec_open2(decode_ctx, decoder, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Failed to open decoder. Error code: %s\n", ret);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }

    // Encoder setup
    const AVCodec* encoder = avcodec_find_encoder_by_name("libx264");
    if (!encoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find libx264 encoder\n");
        ret = AVERROR_ENCODER_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }
    encode_ctx = avcodec_alloc_context3(encoder);
    if (!encode_ctx) {
        ret = AVERROR(ENOMEM);
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        return ret;
    }

    
}

int FFmpegWrapper::createAudioVoid(std::string& filename, double duration, int channels){
    int ret;

    AVFormatContext* fmt_ctx = nullptr;

    

    if((ret = avformat_alloc_output_context2(&fmt_ctx, nullptr, nullptr, filename.c_str())) < 0){
        av_log(NULL, AV_LOG_ERROR, "Could not allocate output context\n");
        return ret;
    }

    AVStream* stream = avformat_new_stream(fmt_ctx, nullptr);
    if(!stream){
        ret = AVERROR_UNKNOWN;
        av_log(NULL, AV_LOG_ERROR, "Could not create new audio stream\n");
        return ret;
    }

    const AVCodec* codec = avcodec_find_encoder_by_name("pcm_s32le");
    if(!codec){
        ret = AVERROR_ENCODER_NOT_FOUND;
        av_log(NULL, AV_LOG_ERROR, "Could not create encoder\n");
        return ret;
    }

    AVCodecContext* codec_ctx = avcodec_alloc_context3(codec);
    codec_ctx->sample_rate = this->settings.sample_rate;
    codec_ctx->time_base = {1, this->settings.sample_rate};
    codec_ctx->sample_fmt = AV_SAMPLE_FMT_S32;

    av_channel_layout_default(&codec_ctx->ch_layout, channels);

    stream->time_base = codec_ctx->time_base;
    stream->codecpar->codec_type = codec_ctx->codec_type;
    stream->codecpar->codec_id = codec_ctx->codec_id;
    stream->codecpar->format = codec_ctx->sample_fmt;
    stream->codecpar->sample_rate = codec_ctx->sample_rate;
    stream->codecpar->ch_layout.nb_channels = codec_ctx->ch_layout.nb_channels;
    stream->codecpar->ch_layout = codec_ctx->ch_layout;

    std::cout << "Num channels: " << stream->codecpar->ch_layout.nb_channels << "\n";
    
    
    if((ret = avcodec_open2(codec_ctx, codec, nullptr)) < 0){
        av_log(NULL, AV_LOG_ERROR, "Could not open codec\n");
        return ret;
    }

    if(!(fmt_ctx->oformat->flags & AVFMT_NOFILE)){
        if((ret = avio_open(&fmt_ctx->pb, filename.c_str(), AVIO_FLAG_WRITE)) < 0){
            av_log(NULL, AV_LOG_ERROR, "avio_open error\n");
            return ret;
        }
    }

    if((ret = avformat_write_header(fmt_ctx, nullptr)) < 0){
        av_log(NULL, AV_LOG_ERROR, "Error while writing header\n");
        return ret;
    }

    AVFrame* frame = av_frame_alloc();
    if(!frame){
        ret = AVERROR_UNKNOWN;
        av_log(NULL, AV_LOG_ERROR, "Could not allocate memory for frame\n");
        return ret;
    }

    int nb_samples = codec_ctx->frame_size;
    if (nb_samples <= 0) {
        nb_samples = 1024;
    }
    frame->nb_samples = nb_samples;

    frame->format = codec_ctx->sample_fmt;
    frame->sample_rate = this->settings.sample_rate;
    av_channel_layout_copy(&frame->ch_layout, &codec_ctx->ch_layout);
    if((ret = av_frame_get_buffer(frame, 0)) < 0){
        av_log(NULL, AV_LOG_ERROR, "Could not get buffer for frame (%d)\n", ret);
        return ret;
    }

    int64_t total_samples   = static_cast<int64_t>(duration * this->settings.sample_rate);
    int64_t written_samples = 0;
    while (written_samples < total_samples) {
        // при необходимости подгоняем последний пакет под остаток
        int ns = frame->nb_samples;
        if (written_samples + ns > total_samples) {
            ns = total_samples - written_samples;
            frame->nb_samples = ns;
            av_frame_make_writable(frame);
        }

        // Fill with zeros
        memset(frame->data[0], 0, ns * codec_ctx->ch_layout.nb_channels * av_get_bytes_per_sample(codec_ctx->sample_fmt));

        frame->pts = written_samples;
        
        if((ret = avcodec_send_frame(codec_ctx, frame)) < 0){
            av_log(NULL, AV_LOG_ERROR, "Error while sending frame\n");
            break;
        }

        while(ret >= 0) {
            AVPacket pkt;
            av_init_packet(&pkt);
            pkt.data = nullptr;
            pkt.size = 0;
            ret = avcodec_receive_packet(codec_ctx, &pkt);
            if(ret == AVERROR(EAGAIN) || ret == AVERROR_EOF){
                av_packet_unref(&pkt);
                break;
            } 
            else if(ret < 0){
                av_log(NULL, AV_LOG_ERROR, "Could not recieve packet\n");
                av_packet_unref(&pkt);
                break;
            }

            pkt.stream_index = stream->index;

            // Scale timestamps
            av_packet_rescale_ts(&pkt, codec_ctx->time_base, stream->time_base);
            av_interleaved_write_frame(fmt_ctx, &pkt);
            av_packet_unref(&pkt);
        }
        written_samples += ns;
    }

    avcodec_send_frame(codec_ctx, nullptr);
    while (true) {
        AVPacket pkt;
        av_init_packet(&pkt);
        pkt.data = nullptr; pkt.size = 0;
        ret = avcodec_receive_packet(codec_ctx, &pkt);
        if(ret == AVERROR(EAGAIN) || ret == AVERROR_EOF){
            av_packet_unref(&pkt);
            break;
        } 
        else if(ret < 0){
            av_log(NULL, AV_LOG_ERROR, "Error while flushing\n");
            av_packet_unref(&pkt);
            break;
        }

        pkt.stream_index = stream->index;
        av_packet_rescale_ts(&pkt, codec_ctx->time_base, stream->time_base);
        av_interleaved_write_frame(fmt_ctx, &pkt);
        av_packet_unref(&pkt);
    }

    av_write_trailer(fmt_ctx);
    if (!(fmt_ctx->oformat->flags & AVFMT_NOFILE))
        avio_closep(&fmt_ctx->pb);
    av_frame_free(&frame);
    avcodec_free_context(&codec_ctx);
    avformat_free_context(fmt_ctx);

    return 0;
}
int createVideoVoid();

int FFmpegWrapper::mergeAudioSourcePair(std::string& src1, std::string& src2, std::string& output_filename){
    AVFormatContext *input_format_context1 = nullptr;
    AVFormatContext *input_format_context2 = nullptr;

    int ret = avformat_open_input(&input_format_context1, src1.c_str(), nullptr, nullptr);
    if (ret < 0) {
    av_log(NULL, AV_LOG_ERROR, "Could not open input 1\n");
    return ret;
    }

    ret = avformat_open_input(&input_format_context2, src2.c_str(), nullptr, nullptr);
    if (ret < 0) {
    av_log(NULL, AV_LOG_ERROR, "Could not open input 2\n");
    avformat_close_input(&input_format_context1);
    return ret;
    }

    ret = avformat_find_stream_info(input_format_context1, nullptr);
    if (ret < 0) {
    av_log(NULL, AV_LOG_ERROR, "Could not find stream 1 info\n");
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);
    return ret;
    }

    ret = avformat_find_stream_info(input_format_context2, nullptr);
    if (ret < 0) {
    av_log(NULL, AV_LOG_ERROR, "Could not find stream 2 info\n");
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);
    return ret;
    }

    AVFormatContext *output_format_context = nullptr;
    ret = avformat_alloc_output_context2(&output_format_context, nullptr, nullptr, output_filename.c_str());
    if (!output_format_context) {
    av_log(NULL, AV_LOG_ERROR, "Could not allocate output context\n");
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);
    return ret;
    }

    AVStream *output_stream = avformat_new_stream(output_format_context, nullptr);
    if (!output_stream) {
    av_log(NULL, AV_LOG_ERROR, "Could not create new stream\n");
    avformat_free_context(output_format_context);
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);
    return ret;
    }

    AVCodecParameters *input_codec_params = input_format_context1->streams[0]->codecpar;
    ret = avcodec_parameters_copy(output_stream->codecpar, input_codec_params);
    if (ret < 0) {
    av_log(NULL, AV_LOG_ERROR, "Could not copy params from input 1 context\n");
    avformat_free_context(output_format_context);
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);
    return ret;
    }

    ret = avio_open(&output_format_context->pb, output_filename.c_str(), AVIO_FLAG_WRITE);
    if (ret < 0) {
    av_log(NULL, AV_LOG_ERROR, "Could not open output file\n");
    avformat_free_context(output_format_context);
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);
    return ret;
    }

    ret = avformat_write_header(output_format_context, nullptr);
    if (ret < 0) {
    av_log(NULL, AV_LOG_ERROR, "Could not write header\n");
    avio_closep(&output_format_context->pb);
    avformat_free_context(output_format_context);
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);
    return ret;
    }

    int64_t current_pts = 0;
    int64_t current_dts = 0;

    while (true) {
        AVPacket packet;
        ret = av_read_frame(input_format_context1, &packet);
        if (ret < 0) {
            break;
        }

        // Update PTS and DTS
        packet.pts = current_pts;
        packet.dts = current_dts;
        current_pts += packet.duration;
        current_dts += packet.duration;

        // Write into output file
        ret = av_interleaved_write_frame(output_format_context, &packet);
        av_packet_unref(&packet);
        if (ret < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not write 1 packet into output file\n");
            break;
        }
    }

    while (true) {
        AVPacket packet;
        ret = av_read_frame(input_format_context2, &packet);
        if (ret < 0) {
            break;
        }

        // Updata PTS and DTS
        packet.pts = current_pts;
        packet.dts = current_dts;
        current_pts += packet.duration;
        current_dts += packet.duration;

        // Write into output file
        ret = av_interleaved_write_frame(output_format_context, &packet);
        av_packet_unref(&packet);
        if (ret < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not write 2 packet into output file\n");
            break;
        }
    }

    av_write_trailer(output_format_context);
    avio_closep(&output_format_context->pb);
    avformat_free_context(output_format_context);
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);

    return 0;
}

int FFmpegWrapper::mergePairAudio(std::string& src1, std::string& src2, std::string& output_filename, double from1, double to1, double from2, double to2){
    std::string first_filename = "tmp/tmp_audio_1.wav";
    std::string second_filename = "tmp/tmp_audio_2.wav";

    int ret;

    // Extracting first audio
    if((ret = this->extractAudio(src1, first_filename, from1, to1)) < 0){
        ret = -1;
        std::cerr << "Error while extracting audio\n";
        return ret;
    }

    // Extracting second audio
    if((ret = this->extractAudio(src2, second_filename, from2, to2)) < 0){
        ret = -1;
        std::cerr << "Error while extracting audio\n";
        return ret;
    }

    this->mergeAudioSourcePair(first_filename, second_filename, output_filename);
    
    // Clean tmp
    // remove(first_filename.c_str());
    // remove(second_filename.c_str());

    return 0;
}

int mergePairVideo();

int FFmpegWrapper::mergeTrackAudio(Track track){
    int ret;
    std::vector<std::string> sources;
    std::vector<std::pair<double, double>> time_markers;
    std::string filename = track.name;
    std::string merge_1_filename = "tmp/tmp_merged_pair_1.wav";
    std::string merge_2_filename = "tmp/tmp_merged_pair_2.wav";

    for(auto& item: track.items){
        if(item.type == "void_audio"){
            if((ret = this->createAudioVoid(item.source, item.end - item.begin, 2)) < 0){
                ret = -1;
                std::cerr << "Error while creating void audio\n";
                return ret;
            }
        }
        if(item.type == "audio" || item.type == "void_audio"){
            sources.push_back(item.source);
            time_markers.push_back({item.begin, item.end});
        }
    }

    if(sources.size() == 1){
        if((ret = this->extractAudio(sources[0], merge_1_filename, time_markers[0].first, time_markers[1].second)) < 0){
            ret = -1;
            std::cerr << "Error while extracting audio\n";
            return ret;
        }

        return 0;
    }

    for(int i = 0; i < sources.size(); i++){
        if(i == 0){
            if((ret = this->mergePairAudio(sources[i], sources[i + 1], merge_1_filename, 
                                           time_markers[i].first, time_markers[i].second, 
                                           time_markers[i + 1].first, time_markers[i + 1].second)) < 0){
                std::cerr << "Error while merging audios: " << sources[i] << ", " << sources[i + 1] << "\n";
                return ret;
            }
            i++;
        }
        else{
            if((ret = this->mergePairAudio(merge_1_filename, sources[i], merge_2_filename, 
                                           0, -1, 
                                           time_markers[i].first, time_markers[i].second))){
                std::cerr << "Error while merging audios: " << merge_2_filename << ", " << sources[i] << "\n";
                return ret;
            }
            
            remove(merge_1_filename.c_str());
            std::rename(merge_2_filename.c_str(), merge_1_filename.c_str());
        }
    }

    std::rename(merge_1_filename.c_str(), (std::string("tmp/") + track.name + ".wav").c_str());
    this->track_sources.push_back(std::string("tmp/") + track.name + ".wav");

    return 0;
}

int mergeTrackVideo();

int FFmpegWrapper::mergePairAudioTracks(std::string& src1, std::string& src2, std::string& output_filename){
    AVFormatContext *input_format_context1 = nullptr;
    AVFormatContext *input_format_context2 = nullptr;

    int ret = avformat_open_input(&input_format_context1, src1.c_str(), nullptr, nullptr);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open input 1\n");
        return ret;
    }

    ret = avformat_open_input(&input_format_context2, src2.c_str(), nullptr, nullptr);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open input 2\n");
        avformat_close_input(&input_format_context1);
        return ret;
    }

    ret = avformat_find_stream_info(input_format_context1, nullptr);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream 1 info\n");
        avformat_close_input(&input_format_context1);
        avformat_close_input(&input_format_context2);
        return ret;
    }

    ret = avformat_find_stream_info(input_format_context2, nullptr);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream 2 info\n");
        avformat_close_input(&input_format_context1);
        avformat_close_input(&input_format_context2);
        return ret;
    }

    AVFormatContext *output_format_context = nullptr;
    ret = avformat_alloc_output_context2(&output_format_context, nullptr, nullptr, output_filename.c_str());
    if (!output_format_context) {
        av_log(NULL, AV_LOG_ERROR, "Could not allocate output context\n");
        avformat_close_input(&input_format_context1);
        avformat_close_input(&input_format_context2);
        return ret;
    }

    AVStream *output_stream = avformat_new_stream(output_format_context, nullptr);
    if (!output_stream) {
        av_log(NULL, AV_LOG_ERROR, "Could not create new stream\n");
        avformat_free_context(output_format_context);
        avformat_close_input(&input_format_context1);
        avformat_close_input(&input_format_context2);
        return ret;
    }

    // Copy param from input stream
    AVCodecParameters *input_codec_params = input_format_context1->streams[0]->codecpar;
    ret = avcodec_parameters_copy(output_stream->codecpar, input_codec_params);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not findcopy parameters from input stream\n");
        avformat_free_context(output_format_context);
        avformat_close_input(&input_format_context1);
        avformat_close_input(&input_format_context2);
        return ret;
    }

    ret = avio_open(&output_format_context->pb, output_filename.c_str(), AVIO_FLAG_WRITE);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open output file\n");
        avformat_free_context(output_format_context);
        avformat_close_input(&input_format_context1);
        avformat_close_input(&input_format_context2);
        return ret;
    }

    ret = avformat_write_header(output_format_context, nullptr);
    if (ret < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not write header into output file\n");
        avio_closep(&output_format_context->pb);
        avformat_free_context(output_format_context);
        avformat_close_input(&input_format_context1);
        avformat_close_input(&input_format_context2);
        return ret;
    }

    while (true) {
        AVPacket packet1, packet2;
        ret = av_read_frame(input_format_context1, &packet1);
        ret = av_read_frame(input_format_context2, &packet2);

        if (ret < 0) {
            break;
        }

        // Muxing packets
        int size = std::min(packet1.size, packet2.size);
        for (int i = 0; i < size; i += 4) { // PCM 32 bit
            float sample1 = *(float*)(packet1.data + i);
            float sample2 = *(float*)(packet2.data + i);
            // Calculating mean
            float mixed_sample = (sample1 + sample2) / 2.0f;
            *(float*)(packet1.data + i) = mixed_sample;
        }

        // Write muxed packet into output file
        ret = av_interleaved_write_frame(output_format_context, &packet1);
        av_packet_unref(&packet1);
        av_packet_unref(&packet2);
        if (ret < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not write packet into output file\n");
            break;
        }
    }

    av_write_trailer(output_format_context);
    avio_closep(&output_format_context->pb);
    avformat_free_context(output_format_context);
    avformat_close_input(&input_format_context1);
    avformat_close_input(&input_format_context2);

    return 0;
}

int FFmpegWrapper::mergeAudioTracks(){
    int ret;
    std::string merge_1_filename = "tmp/tmp_merged_pair_1.wav";
    std::string merge_2_filename = "tmp/tmp_merged_pair_2.wav";
    std::string final_track_name = "tmp/final-audio-track.wav";

    std::cout << "Num tracks: " << this->track_sources.size() << "\n";

    if(this->track_sources.size() == 1){
        std::rename(std::string("tmp/audio-track-1.wav").c_str(), final_track_name.c_str());
        return 0;
    }
    else{
        for(int i = 0; i < this->track_sources.size(); i++){
            if(i == 0){
                if((ret = this->mergePairAudioTracks(this->track_sources[i], this->track_sources[i + 1], merge_1_filename)) < 0){
                    std::cerr << "Cannot merge tracks into final track\n";
                    return ret;
                }
                i++;
            }
            else{
                if((ret = this->mergePairAudioTracks(merge_1_filename, this->track_sources[i], merge_2_filename)) < 0){
                    std::cerr << "Cannot merge tracks into final track\n";
                    return ret;
                }
                remove(merge_1_filename.c_str());
                std::rename(merge_2_filename.c_str(), merge_1_filename.c_str());
            }
        }

        std::rename(merge_1_filename.c_str(), (final_track_name).c_str());
    }

    // Clean tmp
    remove(merge_1_filename.c_str());

    // for(auto& source: this->track_sources)
    //     remove(source.c_str());

    return 0;
}

int mergeVideoTracks();

int applyVideoTransform(std::string& src);

int FFmpegWrapper::applyAudioTransform(std::string& src){

}

int applyAllVideoTransforms();

int applyAllAudioTransforms();



int FFmpegWrapper::process(){
    int ret;
    this->configureTimeline(std::string("audio"));
    this->configureTimeline(std::string("video"));

    std::cout << "Done configuring timeline\n";

    for(auto& track: this->tracks){
        if(track.type == "audio"){
            if((ret = this->mergeTrackAudio(track)) < 0){
                std::cerr << "Error while merging track \"" << track.name << "\"\n";
                return ret;
            }
        }
    }

    this->mergeAudioTracks();
}
