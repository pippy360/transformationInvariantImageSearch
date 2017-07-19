#ifndef perceptual_fast_hash_h
#define perceptual_fast_hash_h

#include <string>
#include <vector>
#include <memory>
#include "opencv2/opencv.hpp"
#include "Keypoint.h"
#include "FragmentHash.h"
#include "img_hash_opencv_module/PHash_Fast.h"
using namespace std;


namespace hashes{
class PerceptualHash_Fast : public FragmentHash<vector<bool>> {
private:
    vector<bool> hash;
    vector<Keypoint> shape;

    static std::string convertHashToString(vector<bool> hash) {
        std::string ret = "";
        int h = 0;
        for (unsigned int i = 0; i < hash.size(); i++) {
            if (hash[i]) {
                h += pow(2, (i % 8));
            }

            if (i % 8 == 7) {
                std::stringstream buffer;
                buffer << std::hex << std::setfill('0') << std::setw(2) << h;
                ret += buffer.str();
                h = 0;
            }
        }
        return ret;
    }

    static vector<bool> hex_str_to_hash(std::string inputString) {
        std::vector<bool> hash;
        int size = inputString.size() / 2;
        for (int i = 0; i < size; i++) {
            std::string str2 = inputString.substr(i * 2, 2);
            if (str2.empty()) {
                continue;
            }

            unsigned int value = 0;
            std::stringstream SS(str2);
            SS >> std::hex >> value;
            for (int j = 0; j < 8; j++) {
                bool check = !!((value >> j) & 1);
                hash.push_back(check);
            }
        }
        return hash;
    }

    static std::vector<bool> matHashToBoolArr(cv::Mat const inHash) {
        const unsigned char *data = inHash.data;
        std::vector<bool> v;
        for (int i = 0; i < 8; i++) {
            unsigned char c = data[i];
            for (int j = 0; j < 8; j++) {
                int shift = (8 - j) - 1;
                bool val = ((c >> shift) & 1);
                v.push_back(val);
            }
        }
        return v;
    }

    static vector<bool> computeHash(cv::Mat const input) {
        cv::Mat inHash;
        auto algo = cv::img_hash::PHash_Fast();
        algo.compute(input, inHash);
        return matHashToBoolArr(inHash);
    }

    //returns hamming distance
    static int getHashDistance(const FragmentHash<vector<bool>> &first, const FragmentHash<vector<bool>> &second) {
        const vector<bool> hash1 = first.getHash();
        const vector<bool> hash2 = second.getHash();
        assert(hash1.size() == hash2.size());

        int dist = 0;
        for (unsigned int i = 0; i < hash1.size(); i++) {
            dist += (hash1[i] != hash2[i]);
        }
        return dist;
    }

public:

    PerceptualHash_Fast()
    {}

    PerceptualHash_Fast(ShapeAndPositionInvariantImage frag):
            FragmentHash<vector<bool>>(frag)
    {
        hash_ = computeHash(frag.getImageData());
    }

    PerceptualHash_Fast(string getHashFromString, std::vector<Keypoint> shape=vector<Keypoint>()):
            FragmentHash<vector<bool>>(getHashFromString, shape)
    {
        hash_ = hex_str_to_hash(getHashFromString);
    }

    PerceptualHash_Fast(const PerceptualHash_Fast& that) :
            FragmentHash(that)
    {}

    string toString() override 
    {
        return convertHashToString(hash_);
    }
    
    int getHammingDistance(const FragmentHash<vector<bool>>& inHash){
        return getHashDistance(*this, inHash);
    }


};

}//end of namespace
#endif // perceptual_fast_hash_h


