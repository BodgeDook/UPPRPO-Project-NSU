#pragma once
#include <fstream>
#include <string_view>
#include <vector>

extern "C" {
    #include <libavformat/avformat.h>
    #include <libswscale/swscale.h>
    #include <libavcodec/avcodec.h>
    #include <libavutil/imgutils.h>
    #include <libavutil/opt.h>
    #include <libavutil/channel_layout.h>
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

    int process();
private:
    Settings settings;
    std::vector<Track> tracks;

    std::vector<std::pair<double, double>> video_time_markers;
    std::vector<std::pair<double, double>> audio_time_markers;

    std::vector<std::string> track_sources;

    void configureTimeline(std::string type);

    // Merge 2 files
    int mergeAudioSourcePair(std::string& src1, std::string& src2, std::string& output_filename);
    int mergeVideoSourcePair(std::string& src1, std::string& src2, std::string& output_filename);

    // Merge pair of sources
    int mergePairAudio(std::string& src1, std::string& src2, std::string& output_filename, double from1, double to1, double from2, double to2);
    int mergePairVideo(std::string& src1, std::string& src2, std::string& output_filename, double from1, double to1, double from2, double to2);

    // Merge all sources of one track
    int mergeTrackAudio(Track track);
    int mergeTrackVideo(Track track);

    // Merge pair of tracks
    int mergePairAudioTracks(std::string& src1, std::string& src2, std::string& output_filename);
    int mergePairVideoTracks(std::string& src1, std::string& src2, std::string& output_filename);

    // Merge all tracks
    int mergeAudioTracks();
    int mergeVideoTracks();

    // Apply single transform on track
    int applyVideoTransform(std::string& src);
    int applyAudioTransform(std::string& src);

    int applyAllVideoTransforms();
    int applyAllAudioTransforms();

    int createAudioVoid(std::string& filename, double duration, int channels);
    int createVideoVoid(std::string& filename, double duration, int channels);

    int extractAudio(std::string& input_file, std::string& output_file, double from_sec, double to_sec);
    int extractVideo(std::string& input_file, std::string& output_file, double from_sec, double to_sec);

    int muxVideoAudio(std::string& videoSrc, std::string& audioSrc, std::string& outputPath);
};