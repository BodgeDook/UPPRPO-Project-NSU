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
    #include <libswresample/swresample.h>
}

#include "settings.hpp"
#include "track.hpp"

class FFmpegWrapper{
public:
    FFmpegWrapper(Settings settings, std::vector<Track> tracks);

    void process(std::string src);
private:
    Settings settings;
    std::vector<Track> tracks;

    std::vector<std::pair<int, int>> video_time_markers;
    std::vector<std::pair<int, int>> audio_time_markers;

    void configureTimeline(std::string type);

    int processAudio();
    int processVideo();

    int mergePairAudio();
    int mergePairVideo();

    int mergeFullAudio();
    int mergeFullVideo();

    int applyVideoTransform();
    int applyAudioTransform();

    int applyAllVideoTransforms();
    int applyAllAudioTransforms();

    int extractAudio(std::string& input_file, double from_sec, double to_sec);
    int extractVideo(std::string& input_file, int from, int to);
};