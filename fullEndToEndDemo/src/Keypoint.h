#pragma once
#include <iostream>   
#include <string>  
#include <math.h>

using namespace std;

class Keypoint
{
public:
	double x, y;
	Keypoint() {};

	Keypoint(double _x, double _y)
	{
		x = _x;
		y = _y;
	}

	string toString(){
		std::ostringstream ss;
		ss << "kp[ "<< x << ", " << y << "]";
		return ss.str();
	}

	inline bool operator==(const Keypoint& rhs) const {
		return (x == rhs.x && y == rhs.y);
	}
};

namespace std {

    template <>
    struct hash<Keypoint>
    {
        std::size_t operator()(const Keypoint& k) const
        {
            using std::hash;
            return ((hash<double>()(k.x) ^ (hash<double>()(k.y) << 1)) >> 1);
        }
    };

}


