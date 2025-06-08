#include "ffmpegwrapper.hpp"
#include <sstream>
#include <string>
#include <iostream>

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

int FFmpegWrapper::extractAudio(std::string& input_file, double from_sec, double to_sec) {
    int ret = 0;
    std::string output_file = "tmp/tmp_audio.wav";

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
    const AVCodec* encoder = avcodec_find_encoder_by_name("pcm_s16le"); // WAV без сжатия, 16-bit
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

    encode_ctx->sample_rate = decode_ctx->sample_rate;
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
    if (av_seek_frame(input_fmt_ctx, audio_stream_index, from_pts, AVSEEK_FLAG_BACKWARD) < 0) {
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

    std::cout << "Done configuring timeline\n";

    extractAudio(src, 10, 20);
}
