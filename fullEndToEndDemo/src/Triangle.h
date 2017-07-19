#ifndef SRC_TRIANGLE_H
#define SRC_TRIANGLE_H
#include "Keypoint.h"

using namespace std;

class Triangle
{
public:

    inline Triangle(){
    }

	inline Triangle(Keypoint one, Keypoint two, Keypoint three){
		keypoints_[0] = one;
		keypoints_[1] = two;
		keypoints_[2] = three;
	}

	inline Triangle(vector<Keypoint> list){
		keypoints_[0] = list[0];
		keypoints_[1] = list[1];
		keypoints_[2] = list[2];
	}
	Keypoint keypoints_[3];

    std::vector<Keypoint> toKeypoints() const
    {
        std::vector<Keypoint> ret;
        for (int i = 0; i < 3; i++)
        {
            ret.push_back(keypoints_[i]);
        }
        return ret;
    }

    string toString() const
    {
        string ret = "";
        for (auto kp: keypoints_)
        {
            ret += kp.toString() + ", ";
        }
        return ret;
    }

    double calcArea() {
        double x0 = keypoints_[0].x;
        double x1 = keypoints_[1].x;
        double x2 = keypoints_[2].x;

        double y0 = keypoints_[0].y;
        double y1 = keypoints_[1].y;
        double y2 = keypoints_[2].y;

        return std::abs(x0 * (y1 - y2) + x1 * (y2 - y0) + x2 * (y0 - y1)) / 2;
    }

    bool hasMatchingKeypoint(Keypoint checkingKeypoint, const Triangle &triangle) const {
        for (auto kp: triangle.toKeypoints())
        {
            if (checkingKeypoint == kp) {
                return true;
            }
        }
        return false;
    }

    inline bool operator==(const Triangle& rhs) const {
        for (auto kp: keypoints_)
        {
            if(hasMatchingKeypoint(kp, rhs))
            {
                //check next keypoint
            }else{
                return false;
            }
        }
        return true;
    }
};

namespace std {

    template <>
    struct hash<Triangle>
    {
        std::size_t operator()(const Triangle& k) const
        {
            using std::hash;
            auto kps = k.toKeypoints();
            return ((hash<Keypoint>()(kps[0]) ^ (hash<Keypoint>()(kps[1]) << 1)) >> 1 ^ hash<Keypoint>()(kps[2]));
        }
    };

}



#endif //SRC_TRIANGLE_H