#ifndef utils_utils_hpp
#define utils_utils_hpp

#include <vector>
#include <opencv2/opencv.hpp>
#include <fstream>
#include <string>
#include <regex>

#include <stdio.h>      /* printf, scanf, puts, NULL */
#include <stdlib.h>     /* srand, rand */
#include <time.h>       /* time */
#include <math.h>

#include "PerceptualHash.h"

#include "Triangle.h"
#include "mainImageProcessingFunctions.hpp"
#include <boost/program_options.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <iostream>
#include "utils.hpp"
#include <tuple>

using boost::property_tree::ptree;
using boost::property_tree::read_json;
using boost::property_tree::write_json;

namespace pt = boost::property_tree;
using namespace std;

static unsigned long x=123456789, y=362436069, z=521288629;

unsigned long xorshf96(void) {          //period 2^96-1
    unsigned long t;
    x ^= x << 16;
    x ^= x >> 5;
    x ^= x << 1;

    t = x;
    x = y;
    y = z;
    z = t ^ x ^ y;

    return z;
}

cv::Mat convertKeypointsVectorToMat(vector<Keypoint> kps)
{
	cv::Mat ret = cv::Mat::zeros(3, kps.size(), CV_64F);

	for (unsigned int i = 0; i < kps.size(); i++)
	{
		auto k = kps[i];
		ret.at<double>(0, i) = k.x;
		ret.at<double>(1, i) = k.y;
		ret.at<double>(2, i) = 1;
	}
	return ret;
}

vector<Keypoint> convertMatToKeypointsVector(cv::Mat inputPoints)
{
	vector<Keypoint> ret;
	for (unsigned int i = 0; i < (unsigned int) inputPoints.cols; i++)
	{
		double x = inputPoints.at<double>(0, i);
		double y = inputPoints.at<double>(1, i);
		Keypoint temp(x, y);
		ret.push_back(temp);
	}
	return ret;
}

void drawSingleTriangleOntoImage(Triangle tri, cv::Mat inputImage, bool setColour = false, cv::Scalar colourInput = cv::Scalar(0,0,0)){
    auto keypoints = tri.toKeypoints();
    auto prevPoint = keypoints.back();
    
    int r = (int) xorshf96();
    int g = (int) xorshf96();
    int b = (int) xorshf96();
    for (int i = 0; i < 3; i++){
        auto currentPoint = keypoints[i];
        auto colour = (setColour)? colourInput: cv::Scalar(b,g,r);

        cv::line(inputImage, cv::Point(prevPoint.x, prevPoint.y), cv::Point(currentPoint.x, currentPoint.y),
                 colour);
        //cv::imshow("something", inputImage);
        //cv::waitKey(10);
        prevPoint = currentPoint;
    }
}


void drawTrianglesOntoImage(vector<Triangle> tris, cv::Mat inputImage, bool randomColours = true)
{
    for (auto tri: tris){
        drawSingleTriangleOntoImage(tri, inputImage, !randomColours);
    }
}

vector<Keypoint> applyTransformationMatrixToKeypointVector(vector<Keypoint> keypoints, cv::Mat transformationMat)
{
	cv::Mat keypointMat = convertKeypointsVectorToMat(keypoints);
	cv::Mat transKeypointMat = transformationMat*keypointMat;
	return convertMatToKeypointsVector(transKeypointMat);
}

vector<Keypoint> readKeypointsFromJsonFile(string filename);

//TODO: explain why this sucks
vector<Keypoint> getKeypoints(cv::Mat inputImage)
{
	cv::imwrite("tempImage.jpg", inputImage);
	FILE* file = popen("python ./src/dumpKeypointsToJson.py ./tempImage.jpg ./tempOutputKeypoints.json", "r");
	pclose(file);
	return readKeypointsFromJsonFile("./tempOutputKeypoints.json");
}

cv::Size calcBoundingRectangleOfShape(cv::Mat shape) 
{
	//convert Mat to vector of 2d Points
	vector<cv::Point> convertedMat;
	for (int i = 0; i < shape.cols; i++) {
		double x = shape.at<double>(i);
		double y = shape.at<double>(shape.cols + i);
		cv::Point tempPt(x, y);
		convertedMat.push_back(tempPt);
	}

	auto resultRect = cv::boundingRect(cv::Mat(convertedMat));
	return resultRect.size();
}

Triangle getTriangleFromRedisEntry(string redisEntry)
{
	pt::ptree root;
	std::stringstream ss;
	ss << redisEntry;
	pt::read_json(ss, root);

	vector<Keypoint> keypoints;
	for (auto pt_j : root.get_child("triangle"))
	{
		double x = pt_j.second.get<double>("x");
		double y = pt_j.second.get<double>("y");
		keypoints.push_back(Keypoint(x, y));
	}
	return Triangle(keypoints);
}

string getImageNameFromRedisEntry(string redisEntry)
{
	pt::ptree root;
	std::stringstream ss;
	ss << redisEntry;
	pt::read_json(ss, root);
	return root.get<string>("imageName");
}

string convertToRedisEntryJson(string imageName, Triangle tri)
{
	pt::ptree root;
	root.put("imageName", imageName);

	pt::ptree points;
	for (auto pt : tri.toKeypoints())
	{
		pt::ptree point;
		point.put("x", pt.x);
		point.put("y", pt.y);
		points.push_back(std::make_pair("", point));
	}
	root.add_child("triangle", points);

	std::ostringstream buf;
	write_json(buf, root, false);
	return buf.str();
}


double getKeypointDistance(Keypoint one, Keypoint two)
{
	return sqrt(pow(one.x - two.x, 2.0) + pow(one.y - two.y, 2.0));
}

vector<Keypoint> findKeypointsWithInRangeFromTwoPoints(Keypoint one, Keypoint two, vector<Keypoint> otherKeypoints, double lowerThreshold, double upperThreshold)
{
	vector<Keypoint> result;
	for (auto cmpKp : otherKeypoints)
	{
		double distanceFromPointOne = getKeypointDistance(one, cmpKp);
		double distanceFromPointTwo = getKeypointDistance(two, cmpKp);
		if (distanceFromPointOne > lowerThreshold && distanceFromPointOne < upperThreshold
			&& distanceFromPointTwo > lowerThreshold && distanceFromPointTwo < upperThreshold)
		{
			result.push_back(cmpKp);
		}
	}
	return result;
}

bool isInKeypointExcludeList(Keypoint keypoint, vector<Keypoint> excludeList) {
	for (auto kp : excludeList)
	{
		if (kp.x == keypoint.x && kp.y == keypoint.y){
			return true;
		}
	}
	return false;
}

bool shouldPointBeExcluded(Keypoint pt, vector<Keypoint> previouslyProcessedPoints, vector<Keypoint> currentProcessedPoints, Keypoint currentTopLevelPoint, Keypoint currentSecondLevelPoint)
{
	return isInKeypointExcludeList(pt, previouslyProcessedPoints)
		|| isInKeypointExcludeList(pt, currentProcessedPoints)
		|| currentTopLevelPoint == pt
		|| currentSecondLevelPoint == pt
		;
}

//TODO: explain why this sucks
vector<Triangle> buildTrianglesForSingleKeypoint(Keypoint centerKeypoint, vector<Keypoint> otherKeypoints, vector<Keypoint> previouslyProcessedPoints, double lowerThreshold, double upperThreshold)
{
	vector<Triangle> result;
	vector<Keypoint> currentProcessedPoints;//a collection of points we have processed since entering this function
	for (auto iterKeypoint : otherKeypoints)
	{
		if (isInKeypointExcludeList(iterKeypoint, previouslyProcessedPoints) || iterKeypoint == centerKeypoint) {
			continue;
		}

		double distance = getKeypointDistance(iterKeypoint, centerKeypoint);
		if (distance > lowerThreshold && distance < upperThreshold)
		{
			vector<Keypoint> finalKeypoints = findKeypointsWithInRangeFromTwoPoints(iterKeypoint, centerKeypoint, otherKeypoints, lowerThreshold, upperThreshold);
			for (auto finKp : finalKeypoints)
			{
				//check if this combination of points will make a triangle we have already created
				if (shouldPointBeExcluded(finKp, previouslyProcessedPoints, currentProcessedPoints, centerKeypoint, iterKeypoint)){
					continue;
				}
				Triangle testingTri(centerKeypoint, iterKeypoint, finKp);
				if (testingTri.calcArea() > 1300){
					result.push_back(testingTri);
				}
			}
		}
		currentProcessedPoints.push_back(iterKeypoint);
	}
	return result;
}

vector<Triangle> buildTrianglesFromKeypoints(vector<Keypoint> keypoints, double lowerThreshold = 150, double upperThreshold = 500)
{
	vector<Triangle> outputTriangles;
	//	for (auto keypoint: keypoints)
	//	{
	//FIXME: this multi-threading needs to be improved
#pragma omp parallel
	{
		vector<Triangle> vec_private;
#pragma omp for nowait schedule(static)
		for (unsigned int i = 0; i < keypoints.size(); i++)
		{
			vector<Keypoint>::const_iterator first = keypoints.begin();
			vector<Keypoint>::const_iterator last = keypoints.begin() + i;
			vector<Keypoint> processedPoints(first, last);
			auto keypoint = keypoints[i];
			auto triangles = buildTrianglesForSingleKeypoint(keypoint, keypoints, processedPoints, lowerThreshold, upperThreshold);
			for (auto tri : triangles){
				vec_private.push_back(tri);
			}
			processedPoints.push_back(keypoint);
		}
#pragma omp critical
		outputTriangles.insert(outputTriangles.end(), vec_private.begin(), vec_private.end());
	}
	return outputTriangles;
}

vector<Triangle> buildTrianglesFromKeypointJsonFile(string filename)
{
	vector<Keypoint> output = readKeypointsFromJsonFile(filename);
	vector<Triangle> ret = buildTrianglesFromKeypoints(output, 50, 400);
	return ret;
}

//TODO: see if we can remove this
vector<Triangle> getTriangles(string filename)
{
	return buildTrianglesFromKeypointJsonFile(filename);
}



ShapeAndPositionInvariantImage getLoadedImage(string imageFullPath) 
{
	cout << "Loading image: " << imageFullPath;
	cv::Mat img = cv::imread(imageFullPath);
	cout << " ... done" << endl;
	return ShapeAndPositionInvariantImage("", img, std::vector<Keypoint>(), "");
}

template<typename T>
const vector<T> readJsonHashesFile(std::ifstream *file)
{
	vector<T> ret;
	vector<Triangle> image1OutputTriangles;
	vector<Triangle> image2OutputTriangles;
	try {
		boost::property_tree::ptree pt;
		boost::property_tree::read_json(*file, pt);

		for (auto label0 : pt) {
			if (label0.first == "output") {
				for (auto label1 : label0.second) {
					if (label1.first == "imageName") {
						//TODO: process the imageName
					}
					else if (label1.first == "hashes") {
						for (auto hash_item : label1.second) {
							ret.push_back(T(hash_item.second.get_value<std::string>()));
						}
					}
				}
			}
		}

	}
	catch (std::exception const &e) {
		std::cerr << e.what() << std::endl;
	}

	return ret;
}

template<typename T>
const vector<T> readJsonHashesFile(const string filename)
{
	std::ifstream file(filename);
	return readJsonHashesFile<T>(&file);
}

vector<Keypoint> readKeypointsFromJsonFile(std::ifstream *file)
{
	vector<Keypoint> result;
	try {
		boost::property_tree::ptree pt;
		boost::property_tree::read_json(*file, pt);

		for (auto label0 : pt) {
			if (label0.first == "output") {
				for (auto label1 : label0.second) {
					if (label1.first == "keypoints") {
						for (auto kp : label1.second){
							double x, y;
							for (auto pt : kp.second){
								if (pt.first == "x"){
									x = pt.second.get_value<double>();
								}
								else{
									y = pt.second.get_value<double>();
								}
							}
							result.push_back(Keypoint(x, y));
						}
					}
				}
			}
		}
	}
	catch (std::exception const &e) {
		std::cerr << e.what() << std::endl;
	}
	return result;
}

vector<Keypoint> readKeypointsFromJsonFile(string filename)
{
	std::ifstream file(filename);
	return readKeypointsFromJsonFile(&file);
}


#endif//utils_utils_hpp
