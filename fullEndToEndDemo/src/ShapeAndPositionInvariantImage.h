#pragma once
#include <string>
#include <vector>
#include <opencv2/opencv.hpp>

#include "Keypoint.h"

class ShapeAndPositionInvariantImage
{
public:
	ShapeAndPositionInvariantImage(const std::string imageName, const cv::Mat imageData, const std::vector<Keypoint> shape, const std::string imageFullPath);

	const std::string& getImageName() const { return imageName_; }
	cv::Mat getImageData() const { return imageData_; }
	const std::vector<Keypoint>& getShape() const { return shape_; }
	const std::string& getImageFullPath() const { return imageFullPath_; }

private:
	const std::string imageName_;
	const cv::Mat imageData_;
	const std::vector<Keypoint> shape_;
	const std::string imageFullPath_;
};

inline ShapeAndPositionInvariantImage::ShapeAndPositionInvariantImage(const std::string imageName, const cv::Mat imageData, const std::vector<Keypoint> shape, const std::string imageFullPath)
	: imageName_(imageName),
	  imageData_(imageData),
	  shape_(shape),
	  imageFullPath_(imageFullPath) {}