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

    // Find stream information
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

    // Rescale timestamps "from" and "to" from seconds to pts (Presentation Timestamps)
    long long from_pts = (from_sec == 0) ? 0 : av_rescale_q(static_cast<long long>(from_sec * AV_TIME_BASE), AV_TIME_BASE_Q, time_base);
    if (to_sec == -1)
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
    const AVCodec* encoder = avcodec_find_encoder_by_name("pcm_s32le"); // WAV without compression, 32-bit
    if (!encoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find pcm_s32le encoder\n");
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

    // Set up swresample to convert sample format and rate
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

    // Seek only if from_sec > 0 to avoid skipping the first frame
    if (from_sec > 0) {
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
    }

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
    bool first_frame_processed = (from_sec == 0); // Track if we've processed the first frame when starting at 0
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

            // Include the first frame when starting at 0 seconds
            if (from_sec == 0 || (frame_end_pts > from_pts && frame_pts < to_pts)) {
                int start_sample = (frame_pts < from_pts && from_sec > 0) ? (from_pts - frame_pts) : 0;
                int end_sample = (frame_end_pts > to_pts) ? (to_pts - frame_pts) : frame->nb_samples;
                int sample_count = end_sample - start_sample;

                if (sample_count <= 0) {
                    av_frame_unref(frame);
                    continue;
                }
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
                first_frame_processed = true; // Mark the first frame as processed
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

int FFmpegWrapper::createVideoVoid(std::string& filename, double duration, int width, int height) {
    int ret = 0;
    AVFormatContext* fmt_ctx = nullptr;

    // Allocate output context
    if ((ret = avformat_alloc_output_context2(&fmt_ctx, nullptr, nullptr, filename.c_str())) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not allocate output context\n");
        return ret;
    }

    AVStream* stream = avformat_new_stream(fmt_ctx, nullptr);
    if (!stream) {
        ret = AVERROR_UNKNOWN;
        av_log(NULL, AV_LOG_ERROR, "Could not create new video stream\n");
        return ret;
    }

    const AVCodec* codec = avcodec_find_encoder_by_name("libx264");
    if (!codec) {
        ret = AVERROR_ENCODER_NOT_FOUND;
        av_log(NULL, AV_LOG_ERROR, "Could not find libx264 encoder\n");
        return ret;
    }

    AVCodecContext* codec_ctx = avcodec_alloc_context3(codec);
    if (!codec_ctx) {
        ret = AVERROR(ENOMEM);
        av_log(NULL, AV_LOG_ERROR, "Could not allocate codec context\n");
        return ret;
    }

    codec_ctx->width = width;
    codec_ctx->height = height;
    codec_ctx->pix_fmt = AV_PIX_FMT_YUV420P;
    codec_ctx->time_base = {1, settings.framerate};
    codec_ctx->framerate = {settings.framerate, 1};

    if ((ret = avcodec_open2(codec_ctx, codec, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open codec\n");
        avcodec_free_context(&codec_ctx);
        return ret;
    }

    avcodec_parameters_from_context(stream->codecpar, codec_ctx);
    stream->time_base = codec_ctx->time_base;

    if (!(fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        if ((ret = avio_open(&fmt_ctx->pb, filename.c_str(), AVIO_FLAG_WRITE)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not open output file\n");
            avcodec_free_context(&codec_ctx);
            return ret;
        }
    }

    if ((ret = avformat_write_header(fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not write header\n");
        avio_closep(&fmt_ctx->pb);
        avcodec_free_context(&codec_ctx);
        return ret;
    }

    AVFrame* frame = av_frame_alloc();
    if (!frame) {
        ret = AVERROR(ENOMEM);
        av_log(NULL, AV_LOG_ERROR, "Could not allocate frame\n");
        goto cleanup;
    }

    frame->width = width;
    frame->height = height;
    frame->format = AV_PIX_FMT_YUV420P;
    if (av_frame_get_buffer(frame, 0) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not allocate frame buffer\n");
        av_frame_free(&frame);
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }

    int64_t total_frames = static_cast<int64_t>(duration * settings.framerate);
    int64_t written_frames = 0;

    while (written_frames < total_frames) {
        // Fill frame with black (Y=0, U=128, V=128 for YUV420P)
        memset(frame->data[0], 0, frame->linesize[0] * height); // Y plane
        memset(frame->data[1], 128, frame->linesize[1] * (height / 2)); // U plane
        memset(frame->data[2], 128, frame->linesize[2] * (height / 2)); // V plane

        frame->pts = written_frames;

        if ((ret = avcodec_send_frame(codec_ctx, frame)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Error sending frame to encoder\n");
            break;
        }

        AVPacket pkt;
        av_init_packet(&pkt);
        pkt.data = nullptr;
        pkt.size = 0;

        while (ret >= 0) {
            ret = avcodec_receive_packet(codec_ctx, &pkt);
            if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
                av_packet_unref(&pkt);
                break;
            } else if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "Error receiving packet\n");
                av_packet_unref(&pkt);
                break;
            }

            pkt.stream_index = stream->index;
            av_packet_rescale_ts(&pkt, codec_ctx->time_base, stream->time_base);
            av_interleaved_write_frame(fmt_ctx, &pkt);
            av_packet_unref(&pkt);
        }

        written_frames++;
    }

    avcodec_send_frame(codec_ctx, nullptr);
    while (true) {
        AVPacket pkt;
        av_init_packet(&pkt);
        pkt.data = nullptr;
        pkt.size = 0;
        ret = avcodec_receive_packet(codec_ctx, &pkt);
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            av_packet_unref(&pkt);
            break;
        } else if (ret < 0) {
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

cleanup:
    if (fmt_ctx && !(fmt_ctx->oformat->flags & AVFMT_NOFILE)) avio_closep(&fmt_ctx->pb);
    if (fmt_ctx) avformat_free_context(fmt_ctx);
    if (codec_ctx) avcodec_free_context(&codec_ctx);
    if (frame) av_frame_free(&frame);

    return ret < 0 ? 1 : 0;
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

int FFmpegWrapper::mergePairVideo(std::string& src1, std::string& src2, std::string& output_filename, double from1, double to1, double from2, double to2) {
    std::string temp1 = "tmp/temp_video_1.mp4";
    std::string temp2 = "tmp/temp_video_2.mp4";

    int ret = extractVideo(src1, temp1, from1, to1);
    if (ret < 0) {
        std::cerr << "Error extracting video 1\n";
        return ret;
    }

    ret = extractVideo(src2, temp2, from2, to2);
    if (ret < 0) {
        std::cerr << "Error extracting video 2\n";
        remove(temp1.c_str());
        return ret;
    }

    ret = mergeVideoSourcePair(temp1, temp2, output_filename);
    remove(temp1.c_str());
    remove(temp2.c_str());

    return ret;
}

int FFmpegWrapper::mergeAudioSourcePair(std::string& src1, std::string& src2, std::string& output_filename) {
    AVFormatContext *input_fmt_ctx1 = nullptr;
    AVFormatContext *input_fmt_ctx2 = nullptr;
    AVFormatContext *output_fmt_ctx = nullptr;
    int ret = 0;

    // Open first input file
    if ((ret = avformat_open_input(&input_fmt_ctx1, src1.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open input 1: %s\n", src1.c_str());
        return ret;
    }
    if ((ret = avformat_find_stream_info(input_fmt_ctx1, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream info for input 1\n");
        avformat_close_input(&input_fmt_ctx1);
        return ret;
    }

    // Open second input file
    if ((ret = avformat_open_input(&input_fmt_ctx2, src2.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open input 2: %s\n", src2.c_str());
        avformat_close_input(&input_fmt_ctx1);
        return ret;
    }
    if ((ret = avformat_find_stream_info(input_fmt_ctx2, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream info for input 2\n");
        avformat_close_input(&input_fmt_ctx1);
        avformat_close_input(&input_fmt_ctx2);
        return ret;
    }

    // Create output context
    if ((ret = avformat_alloc_output_context2(&output_fmt_ctx, nullptr, nullptr, output_filename.c_str())) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not allocate output context\n");
        avformat_close_input(&input_fmt_ctx1);
        avformat_close_input(&input_fmt_ctx2);
        return ret;
    }

    // Copy parameters from first stream for output
    AVStream *out_stream = avformat_new_stream(output_fmt_ctx, nullptr);
    if (!out_stream) {
        av_log(NULL, AV_LOG_ERROR, "Could not create output stream\n");
        avformat_free_context(output_fmt_ctx);
        avformat_close_input(&input_fmt_ctx1);
        avformat_close_input(&input_fmt_ctx2);
        return AVERROR(ENOMEM);
    }
    avcodec_parameters_copy(out_stream->codecpar, input_fmt_ctx1->streams[0]->codecpar);
    out_stream->time_base = input_fmt_ctx1->streams[0]->time_base;

    // Open output file
    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        if ((ret = avio_open(&output_fmt_ctx->pb, output_filename.c_str(), AVIO_FLAG_WRITE)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not open output file: %s\n", output_filename.c_str());
            avformat_free_context(output_fmt_ctx);
            avformat_close_input(&input_fmt_ctx1);
            avformat_close_input(&input_fmt_ctx2);
            return ret;
        }
    }

    if ((ret = avformat_write_header(output_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not write header\n");
        avio_closep(&output_fmt_ctx->pb);
        avformat_free_context(output_fmt_ctx);
        avformat_close_input(&input_fmt_ctx1);
        avformat_close_input(&input_fmt_ctx2);
        return ret;
    }

    int64_t current_pts = 0;
    int64_t current_dts = 0;

    // Read and write packets from first file
    AVPacket pkt;
    while (av_read_frame(input_fmt_ctx1, &pkt) >= 0) {
        if (pkt.stream_index == 0) { // Assume audio is the first stream
            pkt.pts = current_pts;
            pkt.dts = current_dts;
            current_pts += pkt.duration;
            current_dts += pkt.duration;
            av_packet_rescale_ts(&pkt, input_fmt_ctx1->streams[0]->time_base, out_stream->time_base);
            ret = av_interleaved_write_frame(output_fmt_ctx, &pkt);
            if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "Could not write packet from input 1\n");
                av_packet_unref(&pkt);
                break;
            }
        }
        av_packet_unref(&pkt);
    }

    // Read and write packets from second file
    while (av_read_frame(input_fmt_ctx2, &pkt) >= 0) {
        if (pkt.stream_index == 0) {
            pkt.pts = current_pts;
            pkt.dts = current_dts;
            current_pts += pkt.duration;
            current_dts += pkt.duration;
            av_packet_rescale_ts(&pkt, input_fmt_ctx2->streams[0]->time_base, out_stream->time_base);
            ret = av_interleaved_write_frame(output_fmt_ctx, &pkt);
            if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "Could not write packet from input 2\n");
                av_packet_unref(&pkt);
                break;
            }
        }
        av_packet_unref(&pkt);
    }

    av_write_trailer(output_fmt_ctx);
    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) avio_closep(&output_fmt_ctx->pb);
    avformat_free_context(output_fmt_ctx);
    avformat_close_input(&input_fmt_ctx1);
    avformat_close_input(&input_fmt_ctx2);

    return ret < 0 ? 1 : 0;
}

int FFmpegWrapper::mergeVideoSourcePair(std::string& src1, std::string& src2, std::string& output_filename) {
    AVFormatContext *input_fmt_ctx1 = nullptr;
    AVFormatContext *input_fmt_ctx2 = nullptr;
    AVFormatContext *output_fmt_ctx = nullptr;
    int ret = 0;

    // Open first input file
    if ((ret = avformat_open_input(&input_fmt_ctx1, src1.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open input 1: %s\n", src1.c_str());
        return ret;
    }
    if ((ret = avformat_find_stream_info(input_fmt_ctx1, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream info for input 1\n");
        avformat_close_input(&input_fmt_ctx1);
        return ret;
    }

    // Open second input file
    if ((ret = avformat_open_input(&input_fmt_ctx2, src2.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open input 2: %s\n", src2.c_str());
        avformat_close_input(&input_fmt_ctx1);
        return ret;
    }
    if ((ret = avformat_find_stream_info(input_fmt_ctx2, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream info for input 2\n");
        avformat_close_input(&input_fmt_ctx1);
        avformat_close_input(&input_fmt_ctx2);
        return ret;
    }

    // Create output context
    if ((ret = avformat_alloc_output_context2(&output_fmt_ctx, nullptr, nullptr, output_filename.c_str())) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not allocate output context\n");
        avformat_close_input(&input_fmt_ctx1);
        avformat_close_input(&input_fmt_ctx2);
        return ret;
    }

    // Copy parameters from first stream for output
    AVStream *out_stream = avformat_new_stream(output_fmt_ctx, nullptr);
    if (!out_stream) {
        av_log(NULL, AV_LOG_ERROR, "Could not create output stream\n");
        avformat_free_context(output_fmt_ctx);
        avformat_close_input(&input_fmt_ctx1);
        avformat_close_input(&input_fmt_ctx2);
        return AVERROR(ENOMEM);
    }
    avcodec_parameters_copy(out_stream->codecpar, input_fmt_ctx1->streams[0]->codecpar);
    out_stream->time_base = input_fmt_ctx1->streams[0]->time_base;

    // Open output file
    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        if ((ret = avio_open(&output_fmt_ctx->pb, output_filename.c_str(), AVIO_FLAG_WRITE)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not open output file: %s\n", output_filename.c_str());
            avformat_free_context(output_fmt_ctx);
            avformat_close_input(&input_fmt_ctx1);
            avformat_close_input(&input_fmt_ctx2);
            return ret;
        }
    }

    if ((ret = avformat_write_header(output_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not write header\n");
        avio_closep(&output_fmt_ctx->pb);
        avformat_free_context(output_fmt_ctx);
        avformat_close_input(&input_fmt_ctx1);
        avformat_close_input(&input_fmt_ctx2);
        return ret;
    }

    int64_t current_pts = 0;
    int64_t current_dts = 0;

    // Read and write packets from first file
    AVPacket pkt;
    while (av_read_frame(input_fmt_ctx1, &pkt) >= 0) {
        if (pkt.stream_index == 0) { // Assume video is the first stream
            pkt.pts = current_pts;
            pkt.dts = current_dts;
            current_pts += pkt.duration;
            current_dts += pkt.duration;
            av_packet_rescale_ts(&pkt, input_fmt_ctx1->streams[0]->time_base, out_stream->time_base);
            ret = av_interleaved_write_frame(output_fmt_ctx, &pkt);
            if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "Could not write packet from input 1\n");
                av_packet_unref(&pkt);
                break;
            }
        }
        av_packet_unref(&pkt);
    }

    // Read and write packets from second file
    while (av_read_frame(input_fmt_ctx2, &pkt) >= 0) {
        if (pkt.stream_index == 0) {
            pkt.pts = current_pts;
            pkt.dts = current_dts;
            current_pts += pkt.duration;
            current_dts += pkt.duration;
            av_packet_rescale_ts(&pkt, input_fmt_ctx2->streams[0]->time_base, out_stream->time_base);
            ret = av_interleaved_write_frame(output_fmt_ctx, &pkt);
            if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "Could not write packet from input 2\n");
                av_packet_unref(&pkt);
                break;
            }
        }
        av_packet_unref(&pkt);
    }

    av_write_trailer(output_fmt_ctx);
    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) avio_closep(&output_fmt_ctx->pb);
    avformat_free_context(output_fmt_ctx);
    avformat_close_input(&input_fmt_ctx1);
    avformat_close_input(&input_fmt_ctx2);

    return ret < 0 ? 1 : 0;
}

int FFmpegWrapper::applyVideoTransform(std::string& src) {
    int ret = 0;
    AVFormatContext *input_fmt_ctx = nullptr;
    AVFormatContext *output_fmt_ctx = nullptr;
    AVCodecContext *decode_ctx = nullptr;
    AVCodecContext *encode_ctx = nullptr;
    SwsContext *sws_ctx = nullptr;
    AVPacket *pkt = nullptr;
    AVPacket *enc_pkt = nullptr;
    AVFrame *frame = nullptr;
    AVFrame *converted_frame = nullptr;

    int video_stream_index = -1;

    if ((ret = avformat_open_input(&input_fmt_ctx, src.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open input file %s\n", src.c_str());
        return ret;
    }
    if ((ret = avformat_find_stream_info(input_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream info\n");
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }

    video_stream_index = av_find_best_stream(input_fmt_ctx, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (video_stream_index < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find video stream\n");
        ret = AVERROR_STREAM_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }

    const AVCodec* decoder = avcodec_find_decoder(input_fmt_ctx->streams[video_stream_index]->codecpar->codec_id);
    if (!decoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find decoder\n");
        ret = AVERROR_DECODER_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }
    decode_ctx = avcodec_alloc_context3(decoder);
    avcodec_parameters_to_context(decode_ctx, input_fmt_ctx->streams[video_stream_index]->codecpar);
    if ((ret = avcodec_open2(decode_ctx, decoder, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open decoder\n");
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }

    const AVCodec* encoder = avcodec_find_encoder_by_name("libx264");
    if (!encoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find libx264 encoder\n");
        ret = AVERROR_ENCODER_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }
    encode_ctx = avcodec_alloc_context3(encoder);
    encode_ctx->width = this->settings.dst_width;
    encode_ctx->height = this->settings.dst_height;
    encode_ctx->pix_fmt = AV_PIX_FMT_YUV420P;
    encode_ctx->time_base = {1, settings.framerate};
    encode_ctx->framerate = {settings.framerate, 1};
    if ((ret = avcodec_open2(encode_ctx, encoder, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open encoder\n");
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        return ret;
    }

    avformat_alloc_output_context2(&output_fmt_ctx, nullptr, nullptr, (src + ".transformed.mp4").c_str());
    if (!output_fmt_ctx) {
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }
    AVStream* out_stream = avformat_new_stream(output_fmt_ctx, nullptr);
    avcodec_parameters_from_context(out_stream->codecpar, encode_ctx);
    out_stream->time_base = encode_ctx->time_base;

    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        if ((ret = avio_open(&output_fmt_ctx->pb, (src + ".transformed.mp4").c_str(), AVIO_FLAG_WRITE)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not open output file\n");
            goto cleanup;
        }
    }

    if ((ret = avformat_write_header(output_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not write header\n");
        goto cleanup;
    }

    sws_ctx = sws_getContext(decode_ctx->width, decode_ctx->height, decode_ctx->pix_fmt,
                             encode_ctx->width, encode_ctx->height, AV_PIX_FMT_YUV420P,
                             SWS_BILINEAR, nullptr, nullptr, nullptr);
    if (!sws_ctx) {
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }

    pkt = av_packet_alloc();
    enc_pkt = av_packet_alloc();
    frame = av_frame_alloc();
    converted_frame = av_frame_alloc();
    if (!pkt || !enc_pkt || !frame || !converted_frame) {
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }

    int64_t output_pts = 0;
    while (av_read_frame(input_fmt_ctx, pkt) >= 0) {
        if (pkt->stream_index == video_stream_index) {
            if ((ret = avcodec_send_packet(decode_ctx, pkt)) < 0) {
                av_log(NULL, AV_LOG_ERROR, "Error sending packet to decoder\n");
                av_packet_unref(pkt);
                goto cleanup;
            }

            while (ret >= 0) {
                ret = avcodec_receive_frame(decode_ctx, frame);
                if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
                if (ret < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Error receiving frame from decoder\n");
                    goto cleanup;
                }

                av_frame_unref(converted_frame);
                converted_frame->format = AV_PIX_FMT_YUV420P;
                converted_frame->width = encode_ctx->width;
                converted_frame->height = encode_ctx->height;
                if (av_frame_get_buffer(converted_frame, 0) < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Could not allocate converted frame buffer\n");
                    ret = AVERROR(ENOMEM);
                    goto cleanup;
                }

                sws_scale(sws_ctx, frame->data, frame->linesize, 0, decode_ctx->height,
                          converted_frame->data, converted_frame->linesize);

                converted_frame->pts = output_pts++;
                if (avcodec_send_frame(encode_ctx, converted_frame) < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Error sending frame to encoder\n");
                    goto cleanup;
                }

                while (avcodec_receive_packet(encode_ctx, enc_pkt) == 0) {
                    enc_pkt->stream_index = 0;
                    av_packet_rescale_ts(enc_pkt, encode_ctx->time_base, out_stream->time_base);
                    av_interleaved_write_frame(output_fmt_ctx, enc_pkt);
                    av_packet_unref(enc_pkt);
                }
                av_frame_unref(frame);
            }
        }
        av_packet_unref(pkt);
    }

    avcodec_send_frame(encode_ctx, nullptr);
    while (avcodec_receive_packet(encode_ctx, enc_pkt) == 0) {
        enc_pkt->stream_index = 0;
        av_packet_rescale_ts(enc_pkt, encode_ctx->time_base, out_stream->time_base);
        av_interleaved_write_frame(output_fmt_ctx, enc_pkt);
        av_packet_unref(enc_pkt);
    }

    av_write_trailer(output_fmt_ctx);

cleanup:
    if (input_fmt_ctx) avformat_close_input(&input_fmt_ctx);
    if (output_fmt_ctx && !(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) avio_closep(&output_fmt_ctx->pb);
    if (output_fmt_ctx) avformat_free_context(output_fmt_ctx);
    if (decode_ctx) avcodec_free_context(&decode_ctx);
    if (encode_ctx) avcodec_free_context(&encode_ctx);
    if (sws_ctx) sws_freeContext(sws_ctx);
    if (pkt) av_packet_free(&pkt);
    if (enc_pkt) av_packet_free(&enc_pkt);
    if (frame) av_frame_free(&frame);
    if (converted_frame) av_frame_free(&converted_frame);

    return ret < 0 ? 1 : 0;
}

int FFmpegWrapper::applyAudioTransform(std::string& src) {
    int ret = 0;
    AVFormatContext *input_fmt_ctx = nullptr;
    AVFormatContext *output_fmt_ctx = nullptr;
    AVCodecContext *decode_ctx = nullptr;
    AVCodecContext *encode_ctx = nullptr;
    SwrContext *swr_ctx = nullptr;
    AVPacket *pkt = nullptr;
    AVPacket *enc_pkt = nullptr;
    AVFrame *frame = nullptr;
    AVFrame *converted_frame = nullptr;
    AVChannelLayout dec_ch_layout{};

    int audio_stream_index = -1;

    if ((ret = avformat_open_input(&input_fmt_ctx, src.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open input file %s\n", src.c_str());
        return ret;
    }
    if ((ret = avformat_find_stream_info(input_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream info\n");
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }

    audio_stream_index = av_find_best_stream(input_fmt_ctx, AVMEDIA_TYPE_AUDIO, -1, -1, nullptr, 0);
    if (audio_stream_index < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find audio stream\n");
        ret = AVERROR_STREAM_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }

    const AVCodec* decoder = avcodec_find_decoder(input_fmt_ctx->streams[audio_stream_index]->codecpar->codec_id);
    if (!decoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find decoder\n");
        ret = AVERROR_DECODER_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        return ret;
    }
    decode_ctx = avcodec_alloc_context3(decoder);
    avcodec_parameters_to_context(decode_ctx, input_fmt_ctx->streams[audio_stream_index]->codecpar);
    if ((ret = avcodec_open2(decode_ctx, decoder, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open decoder\n");
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }

    const AVCodec* encoder = avcodec_find_encoder_by_name("pcm_s32le");
    if (!encoder) {
        av_log(NULL, AV_LOG_ERROR, "Failed to find pcm_s32le encoder\n");
        ret = AVERROR_ENCODER_NOT_FOUND;
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        return ret;
    }
    encode_ctx = avcodec_alloc_context3(encoder);
    av_channel_layout_copy(&encode_ctx->ch_layout, &decode_ctx->ch_layout);
    encode_ctx->sample_rate = this->settings.sample_rate / 2; // Example: halve the sample rate
    encode_ctx->sample_fmt = AV_SAMPLE_FMT_S32;
    encode_ctx->time_base = {1, encode_ctx->sample_rate};
    if ((ret = avcodec_open2(encode_ctx, encoder, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open encoder\n");
        avformat_close_input(&input_fmt_ctx);
        avcodec_free_context(&decode_ctx);
        avcodec_free_context(&encode_ctx);
        return ret;
    }

    avformat_alloc_output_context2(&output_fmt_ctx, nullptr, nullptr, (src + ".transformed.wav").c_str());
    if (!output_fmt_ctx) {
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }
    AVStream* out_stream = avformat_new_stream(output_fmt_ctx, nullptr);
    avcodec_parameters_from_context(out_stream->codecpar, encode_ctx);
    out_stream->time_base = encode_ctx->time_base;

    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        if ((ret = avio_open(&output_fmt_ctx->pb, (src + ".transformed.wav").c_str(), AVIO_FLAG_WRITE)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not open output file\n");
            goto cleanup;
        }
    }

    if ((ret = avformat_write_header(output_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not write header\n");
        goto cleanup;
    }

    if (swr_alloc_set_opts2(&swr_ctx, &encode_ctx->ch_layout, encode_ctx->sample_fmt, encode_ctx->sample_rate,
                           &decode_ctx->ch_layout, decode_ctx->sample_fmt, decode_ctx->sample_rate, 0, nullptr) < 0) {
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }
    if ((ret = swr_init(swr_ctx)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not initialize SWR context\n");
        goto cleanup;
    }

    pkt = av_packet_alloc();
    enc_pkt = av_packet_alloc();
    frame = av_frame_alloc();
    converted_frame = av_frame_alloc();
    if (!pkt || !enc_pkt || !frame || !converted_frame) {
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }

    int64_t output_pts = 0;
    while (av_read_frame(input_fmt_ctx, pkt) >= 0) {
        if (pkt->stream_index == audio_stream_index) {
            if ((ret = avcodec_send_packet(decode_ctx, pkt)) < 0) {
                av_log(NULL, AV_LOG_ERROR, "Error sending packet to decoder\n");
                av_packet_unref(pkt);
                goto cleanup;
            }

            while (ret >= 0) {
                ret = avcodec_receive_frame(decode_ctx, frame);
                if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
                if (ret < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Error receiving frame from decoder\n");
                    goto cleanup;
                }

                av_frame_unref(converted_frame);
                converted_frame->nb_samples = swr_get_out_samples(swr_ctx, frame->nb_samples);
                converted_frame->ch_layout = encode_ctx->ch_layout;
                converted_frame->format = encode_ctx->sample_fmt;
                converted_frame->sample_rate = encode_ctx->sample_rate;
                if (av_frame_get_buffer(converted_frame, 0) < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Could not allocate converted frame buffer\n");
                    ret = AVERROR(ENOMEM);
                    goto cleanup;
                }

                int conv_samples = swr_convert(swr_ctx, converted_frame->data, converted_frame->nb_samples,
                                              (const uint8_t**)frame->data, frame->nb_samples);
                if (conv_samples < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Error converting audio\n");
                    goto cleanup;
                }

                converted_frame->pts = output_pts;
                output_pts += conv_samples;
                if (avcodec_send_frame(encode_ctx, converted_frame) < 0) {
                    av_log(NULL, AV_LOG_ERROR, "Error sending frame to encoder\n");
                    goto cleanup;
                }

                while (avcodec_receive_packet(encode_ctx, enc_pkt) == 0) {
                    enc_pkt->stream_index = 0;
                    av_packet_rescale_ts(enc_pkt, encode_ctx->time_base, out_stream->time_base);
                    av_interleaved_write_frame(output_fmt_ctx, enc_pkt);
                    av_packet_unref(enc_pkt);
                }
                av_frame_unref(frame);
            }
        }
        av_packet_unref(pkt);
    }

    avcodec_send_frame(encode_ctx, nullptr);
    while (avcodec_receive_packet(encode_ctx, enc_pkt) == 0) {
        enc_pkt->stream_index = 0;
        av_packet_rescale_ts(enc_pkt, encode_ctx->time_base, out_stream->time_base);
        av_interleaved_write_frame(output_fmt_ctx, enc_pkt);
        av_packet_unref(enc_pkt);
    }

    av_write_trailer(output_fmt_ctx);

cleanup:
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

int FFmpegWrapper::mergeAudioVideo(std::string& audio_file, std::string& video_file, std::string& output_filename) {
    AVFormatContext *audio_fmt_ctx = nullptr;
    AVFormatContext *video_fmt_ctx = nullptr;
    AVFormatContext *output_fmt_ctx = nullptr;
    int ret = 0;

    // Open audio file
    if ((ret = avformat_open_input(&audio_fmt_ctx, audio_file.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open audio input file %s\n", audio_file.c_str());
        return ret;
    }
    if ((ret = avformat_find_stream_info(audio_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream info for audio input\n");
        avformat_close_input(&audio_fmt_ctx);
        return ret;
    }

    // Open video file
    if ((ret = avformat_open_input(&video_fmt_ctx, video_file.c_str(), nullptr, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not open video input file %s\n", video_file.c_str());
        avformat_close_input(&audio_fmt_ctx);
        return ret;
    }
    if ((ret = avformat_find_stream_info(video_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find stream info for video input\n");
        avformat_close_input(&audio_fmt_ctx);
        avformat_close_input(&video_fmt_ctx);
        return ret;
    }

    // Create output context
    if ((ret = avformat_alloc_output_context2(&output_fmt_ctx, nullptr, nullptr, output_filename.c_str())) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not allocate output context\n");
        avformat_close_input(&audio_fmt_ctx);
        avformat_close_input(&video_fmt_ctx);
        return ret;
    }

    // Find audio and video streams
    int audio_stream_index = av_find_best_stream(audio_fmt_ctx, AVMEDIA_TYPE_AUDIO, -1, -1, nullptr, 0);
    int video_stream_index = av_find_best_stream(video_fmt_ctx, AVMEDIA_TYPE_VIDEO, -1, -1, nullptr, 0);
    if (audio_stream_index < 0 || video_stream_index < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not find audio or video stream\n");
        ret = AVERROR_STREAM_NOT_FOUND;
        goto cleanup;
    }

    // Add video stream to output
    AVStream *video_out_stream = avformat_new_stream(output_fmt_ctx, nullptr);
    if (!video_out_stream) {
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }
    avcodec_parameters_copy(video_out_stream->codecpar, video_fmt_ctx->streams[video_stream_index]->codecpar);
    video_out_stream->time_base = video_fmt_ctx->streams[video_stream_index]->time_base;

    // Add audio stream to output
    AVStream *audio_out_stream = avformat_new_stream(output_fmt_ctx, nullptr);
    if (!audio_out_stream) {
        ret = AVERROR(ENOMEM);
        goto cleanup;
    }
    avcodec_parameters_copy(audio_out_stream->codecpar, audio_fmt_ctx->streams[audio_stream_index]->codecpar);
    audio_out_stream->time_base = audio_fmt_ctx->streams[audio_stream_index]->time_base;

    // Open output file
    if (!(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) {
        if ((ret = avio_open(&output_fmt_ctx->pb, output_filename.c_str(), AVIO_FLAG_WRITE)) < 0) {
            av_log(NULL, AV_LOG_ERROR, "Could not open output file %s\n", output_filename.c_str());
            goto cleanup;
        }
    }

    if ((ret = avformat_write_header(output_fmt_ctx, nullptr)) < 0) {
        av_log(NULL, AV_LOG_ERROR, "Could not write header\n");
        goto cleanup;
    }

    AVPacket pkt;
    // Copy video packets
    while (av_read_frame(video_fmt_ctx, &pkt) >= 0) {
        if (pkt.stream_index == video_stream_index) {
            pkt.stream_index = video_out_stream->index;
            av_packet_rescale_ts(&pkt, video_fmt_ctx->streams[video_stream_index]->time_base, video_out_stream->time_base);
            ret = av_interleaved_write_frame(output_fmt_ctx, &pkt);
            if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "Error writing video packet\n");
                av_packet_unref(&pkt);
                break;
            }
        }
        av_packet_unref(&pkt);
    }

    // Copy audio packets
    while (av_read_frame(audio_fmt_ctx, &pkt) >= 0) {
        if (pkt.stream_index == audio_stream_index) {
            pkt.stream_index = audio_out_stream->index;
            av_packet_rescale_ts(&pkt, audio_fmt_ctx->streams[audio_stream_index]->time_base, audio_out_stream->time_base);
            ret = av_interleaved_write_frame(output_fmt_ctx, &pkt);
            if (ret < 0) {
                av_log(NULL, AV_LOG_ERROR, "Error writing audio packet\n");
                av_packet_unref(&pkt);
                break;
            }
        }
        av_packet_unref(&pkt);
    }

    av_write_trailer(output_fmt_ctx);

cleanup:
    if (audio_fmt_ctx) avformat_close_input(&audio_fmt_ctx);
    if (video_fmt_ctx) avformat_close_input(&video_fmt_ctx);
    if (output_fmt_ctx && !(output_fmt_ctx->oformat->flags & AVFMT_NOFILE)) avio_closep(&output_fmt_ctx->pb);
    if (output_fmt_ctx) avformat_free_context(output_fmt_ctx);

    return ret < 0 ? 1 : 0;
}

int FFmpegWrapper::applyTransformations(std::string& src, std::string& output_filename) {
    int ret = 0;
    std::string temp_audio = "tmp/temp_audio.wav";
    std::string temp_video = "tmp/temp_video.mp4";

    // Extract and transform audio
    if ((ret = extractAudio(src, temp_audio, 0, -1)) < 0) {
        std::cerr << "Error extracting audio\n";
        return ret;
    }
    if ((ret = applyAudioTransform(temp_audio)) < 0) {
        std::cerr << "Error transforming audio\n";
        remove(temp_audio.c_str());
        return ret;
    }

    // Extract and transform video
    if ((ret = extractVideo(src, temp_video, 0, -1)) < 0) {
        std::cerr << "Error extracting video\n";
        remove(temp_audio.c_str());
        return ret;
    }
    if ((ret = applyVideoTransform(temp_video)) < 0) {
        std::cerr << "Error transforming video\n";
        remove(temp_audio.c_str());
        remove(temp_video.c_str());
        return ret;
    }

    // Merge transformed audio and video
    if ((ret = mergeAudioVideo(temp_audio + ".transformed.wav", temp_video + ".transformed.mp4", output_filename)) < 0) {
        std::cerr << "Error merging audio and video\n";
    }

    // Clean up temporary files
    remove(temp_audio.c_str());
    remove((temp_audio + ".transformed.wav").c_str());
    remove(temp_video.c_str());
    remove((temp_video + ".transformed.mp4").c_str());

    return ret < 0 ? 1 : 0;
}