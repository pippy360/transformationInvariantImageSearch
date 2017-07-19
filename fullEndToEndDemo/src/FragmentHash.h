#ifndef fragment_hash_h
#define fragment_hash_h

#include <string>
#include <vector>
#include <Keypoint.h>
#include <memory>
#include "ShapeAndPositionInvariantImage.h"

using namespace std;

template <typename T> class FragmentHash
{
private:
protected:
    T hash_;
    vector<Keypoint> shape_;
public:

    FragmentHash()
    {}

    FragmentHash(ShapeAndPositionInvariantImage image)
    {}

    FragmentHash(string conver, std::vector<Keypoint> shape=vector<Keypoint>()):
        shape_(shape)
    {
        //convert string to hash
    }

    FragmentHash(const FragmentHash& that):
        hash_(that.hash_),
        shape_(that.shape_)
    {}

    virtual string toString() = 0;

    //getters and setters

    virtual inline T getHash() const { return hash_; } 

    virtual vector<Keypoint> getShape() const { return shape_; } 

    virtual int getHammingDistance(const FragmentHash<T>& inHash) = 0;

};

#endif // fragment_hash_h
