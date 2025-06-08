#include "operationfactory.hpp"

#include <rapidjson/filereadstream.h>

/*
    OperationFactory class, creates an std::vector<VideoOperation*> from JSON configuration file.
    Has methods:
    1. createOperationList method that creates std::vector<VideoOperation*> of the operations
*/

// Constructor, gets path to JSON configuration file
OperationFactory::OperationFactory() = default;

OperationFactory::OperationFactory(std::string_view jsonFilePath): jsonFilePath(std::string(jsonFilePath)){
    this->status = 0;

    std::cout << this->jsonFilePath.c_str() << "\n";

    FILE* fp = fopen("config.json", "rb");

    if(!fp){
        std::cerr << "Error: unable to open config.json" << std::endl;
        this->status = 1;
    }
    else{
        rapidjson::FileReadStream is(fp, this->readBuffer, sizeof(this->readBuffer));

        this->doc.ParseStream(is);

        if(this->doc.HasParseError()){
            std::cerr << "Error: failed to parse config.json" << std::endl;
            fclose(fp);
            this->status = 1;
        }

        fclose(fp);
    }
}

int OperationFactory::parseSettings(){
    if(this->status == 0){
        if(this->doc.HasMember("settings") && doc["settings"].IsObject()){
            auto settings = doc["settings"].GetObject();
            if(settings.HasMember("title") && settings["title"].IsString())
                this->settings.outputFilePath = settings["title"].GetString();
            else{
                std::cerr << "Error: config.json doesn't have \"title\" member" << std::endl;
                return 1;
            }

            if(settings.HasMember("framerate") && settings["framerate"].IsInt())
                this->settings.framerate = settings["framerate"].GetInt();
            else{
                std::cerr << "Error: config.json doesn't have \"framerate\" member" << std::endl;
                return 1;
            }

            if(settings.HasMember("codec") && settings["codec"].IsString())
                this->settings.codec = settings["codec"].GetString();
            else{
                std::cerr << "Error: config.json doesn't have \"codec\" member" << std::endl;
                return 1;
            }

            if(settings.HasMember("resolution") && settings["resolution"].IsObject()){
                auto resolution = settings["resolution"].GetObject();

                if(resolution.HasMember("width") && resolution["width"].IsInt())
                    this->settings.dst_width = resolution["width"].GetInt();
                else{
                    std::cerr << "Error: config.json doesn't have \"width\" member in \"resolution\"" << std::endl;
                    return 1;
                }

                if(resolution.HasMember("height") && resolution["height"].IsInt())
                    this->settings.dst_height = resolution["height"].GetInt();
                else{
                    std::cerr << "Error: config.json doesn't have \"height\" member in \"resolution\"" << std::endl;
                    return 1;
                }
            }
        }
        else{
            std::cerr << "Error: config.json doesn't have \"settings\" member" << std::endl;
            return 1;
        }

        return 0;
    }

    return 1;
}

int OperationFactory::parseTracks(){
    if(this->status == 0){
        if(this->doc.HasMember("tracks") && this->doc["tracks"].IsArray()){
            auto tracks = this->doc["tracks"].GetArray();

            for(auto& track: tracks){
                if(track.HasMember("name") && track["name"].IsString() && 
                track.HasMember("type") && track["type"].IsString() &&
                track.HasMember("items") && track["items"].IsArray()){
                    std::string track_name = track["name"].GetString();
                    std::string track_type = track["type"].GetString();
                    auto items = track["items"].GetArray();
                    std::vector<Item> items_vect;

                    for(auto& item: items){
                        if(item.HasMember("name") && item["name"].IsString() &&
                        item.HasMember("type") && item["type"].IsString() &&
                        item.HasMember("source") && item["source"].IsString() &&
                        item.HasMember("in_frame") && item["in_frame"].IsInt() &&
                        item.HasMember("out_frame") && item["out_frame"].IsInt() &&
                        item.HasMember("effects") && item["effects"].IsArray()){
                            std::string item_name = item["name"].GetString();
                            std::string item_type = item["type"].GetString();
                            std::string item_source = item["source"].GetString();
                            int in_frame = item["in_frame"].GetInt();
                            int out_frame = item["out_frame"].GetInt();
                            auto effects = item["effects"].GetArray();
                            std::vector<Effect> effects_vect;
                            

                            for(auto& effect: effects){
                                if(effect.HasMember("name") && effect["name"].IsString() &&
                                effect.HasMember("settings") && effect["settings"].IsObject() &&
                                effect.HasMember("keyframes") && effect["keyframes"].IsArray()){
                                    std::string effect_name = effect["name"].GetString();
                                    auto settings = effect["settings"].GetObject();

                                    std::map<std::string, float> settings_map;
                                    std::vector<int> keyframes_vector;

                                    for(auto it = settings.MemberBegin(); it != settings.MemberEnd(); it++){
                                        const std::string key = it->name.GetString();
                                        if(it->value.IsFloat()){
                                            float value = it->value.GetFloat();
                                            settings_map[key] = value;
                                        }
                                        else{
                                            std::cerr << "Invalid setting type for key: " << key << " in item " << item_name << "\n";
                                            return 1;
                                        }
                                    }

                                    auto keyframes = effect["keyframes"].GetArray();

                                    for(auto& keyframe: keyframes){
                                        if (keyframe.IsInt() || keyframe.IsFloat()) {
                                            int value = keyframe.IsInt() ? keyframe.GetInt() : static_cast<int>(keyframe.GetFloat());
                                            keyframes_vector.push_back(value);
                                        }
                                        else{
                                            std::cerr << "    Invalid keyframe type in item " << item_name << "\n";
                                        }
                                    }

                                    Effect effect_struct{effect_name, settings_map, keyframes_vector};
                                    effects_vect.push_back(effect_struct);
                                }
                                else{
                                    std::cerr << "Invalid effect in item " << item_name << "\n";
                                    return 1;
                                }

                            }
                            Item item_struct{item_name, item_type, item_source, in_frame, out_frame, effects_vect};
                            items_vect.push_back(item_struct);
                        }
                        else{
                            std::cerr << "Invalid item in track " << track_name << "\n";
                            return 1;
                        }
                    }
                    Track track_struct{track_name, track_type, items_vect};
                    this->tracks.push_back(track_struct);
                }
                else{
                    std::cerr << "Invalid track\n";
                    return 1;
                }
            }
            return 0;
        }
        else{
            std::cerr << "No tracks specified\n";
            return 1;
        }
    }

    return 1;
}

Settings OperationFactory::getSettings() const{
    return this->settings;
}

std::vector<Track> OperationFactory::getTracks() const{
    return this->tracks;
}

void OperationFactory::testParse() const{
    std::cout << "Settings:\n";
    std::cout << "\toutFilePath: " << this->settings.outputFilePath << "\n";
    std::cout << "\tdst_width: " << this->settings.dst_width << "\n";
    std::cout << "\tdst_height: " << this->settings.dst_height << "\n";
    std::cout << "\tframerate: " << this->settings.framerate << "\n";

    std::cout << "Tracks:\n";
    if(!this->tracks.empty()){
        for(auto& track: this->tracks){
            std::cout << "\tname: " << track.name << "\n";
            std::cout << "\ttype: " << track.type << "\n";

            std::cout << "\tItems:\n";
            if(!track.items.empty()){
                for(auto& item: track.items){
                    std::cout << "\t\tname: " << item.name << "\n";
                    std::cout << "\t\ttype: " << item.type << "\n";
                    std::cout << "\t\tsource: " << item.source << "\n";
                    std::cout << "\t\tstartFrame: " << item.startFrame << "\n";
                    std::cout << "\t\tendFrame: " << item.endFrame << "\n";

                    std::cout << "\t\tEffects:\n";
                    if(!item.effects.empty()){
                        for(auto& effect: item.effects){
                            std::cout << "\t\t\tname: " << effect.name << "\n";

                            std::cout << "\t\t\tParameters:\n";
                            if(!effect.parameters.empty()){
                                for(auto it = effect.parameters.begin(); it != effect.parameters.end(); it++){
                                    std::cout << "\t\t\t\t" << it->first << ": " << it->second << "\n";
                                }
                            }

                            std::cout << "\t\t\tKeyframes:\n";
                            if(!effect.keyframes.empty()){
                                for(int keyframe: effect.keyframes){
                                    std::cout << "\t\t\t\t" << keyframe << "\n";
                                }
                            }
                        }
                    }
                }
            }
        }
    }   
}