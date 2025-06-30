#ifndef FFMPEGWRAPPER_HPP
#define FFMPEGWRAPPER_HPP

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/opt.h>
#include <libavutil/channel_layout.h>
#include <libswscale/swscale.h>
#include <libswresample/swresample.h>
}

#include <string>
#include <vector>

struct Item {
    std::string source;
    std::string type;
    double begin;
    double end;
};

struct Track {
    std::string name;
    std::string type;
    std::vector<Item> items;
};

struct Settings {
    int sample_rate;
    int framerate;
    int dst_width;
    int dst_height;
    std::string outputFilePath;
};

class FFmpegWrapper {
public:
    FFmpegWrapper(Settings settings, std::vector<Track> tracks);
    void configureTimeline(std::string type);
    int extractAudio(std::string& input_file, std::string& output_file, double from_sec, double to_sec);
    int extractVideo(std::string& input_file, std::string& output_file, double from_sec, double to_sec);
    int createAudioVoid(std::string& filename, double duration, int channels);
    int createVideoVoid(std::string& filename, double duration, int width, int height);
    int mergePairAudio(std::string& src1, std::string& src2, std::string& output_filename, double from1, double to1, double from2, double to2);
    int mergePairVideo(std::string& src1, std::string& src2, std::string& output_filename, double from1, double to1, double from2, double to2);
    int mergeTrackAudio(Track track);
    int mergeTrackVideo(Track track);
    int mergeAudioTracks();
    int mergeVideoTracks();
    int mergePairAudioTracks(std::string& src1, std::string& src2, std::string& output_filename);
    int mergePairVideoTracks(std::string& src1, std::string& src2, std::string& output_filename);
    int applyVideoTransform(std::string& src);
    int applyAudioTransform(std::string& src);
    int applyAllVideoTransforms();
    int applyAllAudioTransforms();
    int process();
    int muxVideoAudio(std::string& video_file, std::string& audio_file, std::string& output_file);

private:
    Settings settings;
    std::vector<Track> tracks;
    std::vector<std::string> track_sources;
    std::vector<std::pair<double, double>> audio_time_markers;
    std::vector<std::pair<double, double>> video_time_markers;
    int mergeAudioSourcePair(std::string& src1, std::string& src2, std::string& output_filename);
    int mergeVideoSourcePair(std::string& src1, std::string& src2, std::string& output_filename);
    int mergeAudioVideo(std::string& audio_file, std::string& video_file, std::string& output_filename);
    int applyTransformations(std::string& src, std::string& output_filename);
};

#endif