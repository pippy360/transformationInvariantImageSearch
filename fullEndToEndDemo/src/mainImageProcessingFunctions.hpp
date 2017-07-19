#ifndef mainImageProcessingFunctions_cpp
#define mainImageProcessingFunctions_cpp


#include <vector>
#include <opencv2/opencv.hpp>
#include <stdio.h>
#include <iomanip>      // std::setw
#include <math.h>       /* pow, atan2 */

#include "FragmentHash.h"
#include "ShapeAndPositionInvariantImage.h"
#include "Triangle.h"

#define NUM_OF_ROTATIONS 3
#define HASH_SIZE 8
#define FRAGMENT_WIDTH 60*.86
#define FRAGMENT_HEIGHT 60
#define PI 3.14159265

const std::vector<Keypoint> getTargetTriangle(int scalex, int scaley)
{
	std::vector<Keypoint> v;
	v.push_back(Keypoint(0, 0));
	v.push_back(Keypoint(.5*scalex, 1 * scaley));
	v.push_back(Keypoint(1 * scalex, 0));
	return v;
}

namespace cv
{
	Matx33d calcTransformationMatrix(const std::vector<Keypoint>& inputTriangle, const std::vector<Keypoint>& targetTriangle)
	{
		/*
		* ######CODE BY ROSCA#######
		*/
		Keypoint target_pt1 = targetTriangle[1];
		Keypoint target_pt2 = targetTriangle[2];
		cv::Matx33d targetPoints(target_pt1.x, target_pt2.x, 0.0,
			target_pt1.y, target_pt2.y, 0.0,
			0.0, 0.0, 1.0);

		Keypoint pt2 = Keypoint(inputTriangle[1].x - inputTriangle[0].x, inputTriangle[1].y - inputTriangle[0].y);
		Keypoint pt3 = Keypoint(inputTriangle[2].x - inputTriangle[0].x, inputTriangle[2].y - inputTriangle[0].y);

		cv::Matx33d inputPoints(pt2.x, pt3.x, 0.0,
			pt2.y, pt3.y, 0.0,
			0.0, 0.0, 1.0);

		cv::Matx33d transpose_m(1.0, 0.0, -inputTriangle[0].x,
			0.0, 1.0, -inputTriangle[0].y,
			0.0, 0.0, 1.0);

		return  targetPoints * inputPoints.inv() * transpose_m;
	}

	bool isToTheLeftOf(Keypoint pt1, Keypoint pt2)
	{
		return ((0 - pt1.x)*(pt2.y - pt1.y) - (0 - pt1.y)*(pt2.x - pt1.x)) > 0;
	}

	const std::vector<Keypoint> prepShapeForCalcOfTransformationMatrix(const std::vector<Keypoint>& inputTriangle, const std::vector<Keypoint>& targetTriangle)
	{
		auto pt1 = inputTriangle[0];
		auto pt2 = inputTriangle[1];
		auto pt3 = inputTriangle[2];
		auto pt2_t = Keypoint(pt2.x - pt1.x, pt2.y - pt1.y);
		auto pt3_t = Keypoint(pt3.x - pt1.x, pt3.y - pt1.y);

		auto ret = std::vector<Keypoint>();
		ret.push_back(pt1);
		if (isToTheLeftOf(pt2_t, pt3_t))
		{
			ret.push_back(pt2);
			ret.push_back(pt3);
		} else {
			ret.push_back(pt3);
			ret.push_back(pt2);
		}
		return ret;
	}

	//@shift: this is used to get every rotation of the triangle we need (3 times, one for each edge of the triangle)
	const std::vector<Keypoint> prepShapeForCalcOfTransformationMatrixWithShift(const std::vector<Keypoint> shape, const std::vector<Keypoint>& targetTriangle, int shift)
	{
		auto shape_cpy = shape;
		shift %= shape_cpy.size();
		std::rotate(shape_cpy.begin(), shape_cpy.begin() + shift, shape_cpy.end());
		return prepShapeForCalcOfTransformationMatrix(shape_cpy, targetTriangle);
	}

	Mat covertToDynamicallyAllocatedMatrix(const Matx33d transformation_matrix)
	{
		cv::Mat m = cv::Mat::ones(2, 3, CV_64F);
		m.at<double>(0, 0) = transformation_matrix(0, 0);
		m.at<double>(0, 1) = transformation_matrix(0, 1);
		m.at<double>(0, 2) = transformation_matrix(0, 2);
		m.at<double>(1, 0) = transformation_matrix(1, 0);
		m.at<double>(1, 1) = transformation_matrix(1, 1);
		m.at<double>(1, 2) = transformation_matrix(1, 2);
		return m;
	}

	Mat applyTransformationMatrixToImage(Mat inputImage, const Matx33d transformation_matrix, int outputTriangleSizeX, int outputTriangleSizeY)
	{
		Mat m = covertToDynamicallyAllocatedMatrix(transformation_matrix);
		Mat outputImage(outputTriangleSizeY, outputTriangleSizeX, CV_8UC3, Scalar(0, 0, 0));
		warpAffine(inputImage, outputImage, m, outputImage.size());
		return outputImage;
	}

	Matx33d calcTransformationMatrixWithShapePreperation(const std::vector<Keypoint>& inputTriangle, const std::vector<Keypoint>& targetTriangle, int shift)
	{
		auto newShape = prepShapeForCalcOfTransformationMatrixWithShift(inputTriangle, targetTriangle, shift);
		return calcTransformationMatrix(newShape, targetTriangle);
	}

	std::vector<ShapeAndPositionInvariantImage> normaliseScaleAndRotationForSingleFrag(ShapeAndPositionInvariantImage& fragment)
	{
		auto shape = fragment.getShape();
		auto ret = std::vector<ShapeAndPositionInvariantImage>();
		int outputTriangleSizeX = FRAGMENT_WIDTH;
		int outputTriangleSizeY = FRAGMENT_HEIGHT;
		for (unsigned int i = 0; i < NUM_OF_ROTATIONS; i++)
		{
			auto transformationMatrix = calcTransformationMatrixWithShapePreperation(shape, getTargetTriangle(outputTriangleSizeX, outputTriangleSizeY), i);
			auto input_img = fragment.getImageData();
			auto newImageData = applyTransformationMatrixToImage(input_img, transformationMatrix, outputTriangleSizeX, outputTriangleSizeY);
			auto t = ShapeAndPositionInvariantImage(fragment.getImageName(), newImageData, shape, fragment.getImageFullPath());
			ret.push_back(t);
		}

		return ret;
	}

	ShapeAndPositionInvariantImage getFragment(const ShapeAndPositionInvariantImage& input_image, const Triangle& tri)
	{
		return ShapeAndPositionInvariantImage(input_image.getImageName(), input_image.getImageData(), tri.toKeypoints(), "");
	}

	template<typename T> std::vector<T> getHashesForFragments(std::vector<ShapeAndPositionInvariantImage>& normalisedFragments)
	{
		auto ret = std::vector<T>();
		for (auto frag : normalisedFragments)
		{
			auto calculatedHash = T(frag);
			ret.push_back(calculatedHash);
		}
		return ret;
	}

	template<typename T> std::vector<T> getHashesForTriangle(ShapeAndPositionInvariantImage& input_image, const Triangle& tri)
	{
		auto fragment = getFragment(input_image, tri);
		auto normalisedFragments = normaliseScaleAndRotationForSingleFrag(fragment);
		auto hashes = getHashesForFragments<T>(normalisedFragments);

		return hashes;
	}

	template<typename T> vector<pair<Triangle, T>> getAllTheHashesForImage(ShapeAndPositionInvariantImage inputImage, std::vector<Triangle> triangles)
	{
		ShapeAndPositionInvariantImage inputImage2("", inputImage.getImageData(), std::vector<Keypoint>(), "");
		
		vector<pair<Triangle, T>> ret(triangles.size()*NUM_OF_ROTATIONS);

#pragma omp parallel for
		for (unsigned int i = 0; i < triangles.size(); i++) 
		{
			auto tri = triangles[i];
			auto hashes = getHashesForTriangle<T>(inputImage2, tri);

			for (unsigned int j = 0; j < 3; j++)
			{
				ret[(i * 3) + j] = pair<Triangle, T>(tri, hashes[j]);
			}
		}
		return ret;
	}

}//namespace cv

#endif//mainImageProcessingFunctions_cpp
