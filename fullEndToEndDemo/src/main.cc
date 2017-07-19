#include <vector>
#include <opencv2/opencv.hpp>
#include <fstream>
#include <string>
#include <regex>

#include <stdio.h>      /* printf, scanf, puts, NULL */
#include <stdlib.h>     /* srand, rand */
#include <time.h>       /* time */

#include "PerceptualHash.h"
#include "PerceptualHash_Fast.h"

//#include "FragmentHash.h"
//#include "ShapeAndPositionInvariantImage.h"
#include "Triangle.h"
#include "mainImageProcessingFunctions.hpp"
#include <boost/program_options.hpp>
#include <iostream>
#include "utils.hpp"
#include "hiredis/hiredis.h"
#include <map>

using namespace std;

void addAllHashesToRedis(string imagePath){
    auto loadedImage = getLoadedImage(imagePath);
    vector<Keypoint> keypoints = getKeypoints(loadedImage.getImageData());
    vector<Triangle> tris = buildTrianglesFromKeypoints(keypoints, 50, 400);;
    auto hashTrianglePairs = cv::getAllTheHashesForImage<hashes::PerceptualHash>(loadedImage, tris);

    redisContext *c;
//    redisReply *reply;
    const char *hostname = "127.0.0.1";
    int port = 6379;

    struct timeval timeout = { 1, 500000 }; // 1.5 seconds
    c = redisConnectWithTimeout(hostname, port, timeout);
    if (c == NULL || c->err) {
        if (c) {
            printf("Connection error: %s\n", c->errstr);
            redisFree(c);
        } else {
            printf("Connection error: can't allocate redis context\n");
        }
        exit(1);
    }

    int count = 0;
    for (auto hashTriangle : hashTrianglePairs)
    {
        string redisEntry = convertToRedisEntryJson(imagePath, hashTriangle.first);
        redisCommand(c,"SADD %s %s", hashTriangle.second.toString().c_str(), redisEntry.c_str());

	count++;
    }
    cout << "Added " << count << " image fragments to DB" << endl;
}

int findMatchingHashInRedis(string imageName){
    auto loadedImage = getLoadedImage(imageName);
    vector<Keypoint> keypoints = getKeypoints(loadedImage.getImageData());
    vector<Triangle> tris = buildTrianglesFromKeypoints(keypoints, 50, 400);;
    auto hashTrianglePairs = cv::getAllTheHashesForImage<hashes::PerceptualHash>(loadedImage, tris);

    redisContext *c;
    redisReply *reply;
    const char *hostname = "127.0.0.1";
    int port = 6379;

    struct timeval timeout = { 1, 500000 }; // 1.5 seconds
    c = redisConnectWithTimeout(hostname, port, timeout);
    if (c == NULL || c->err) {
        if (c) {
            printf("Connection error: %s\n", c->errstr);
            redisFree(c);
        } else {
            printf("Connection error: can't allocate redis context\n");
        }
        exit(1);
    }
//    cout << "finished hashing" << endl;
//    vector<hashes::PerceptualHash_Fast> result;
    vector<string> result;
//    for (auto hash : hashes)
//    {
    unsigned int batchSize = 1000;
    for (unsigned int i = 0; i < hashTrianglePairs.size(); i++)
    {
        unsigned int j = 0;
        for(;i < hashTrianglePairs.size() && j < batchSize; j++, i++){
            auto hashTriangle = hashTrianglePairs[i];
            redisAppendCommand(c,"SMEMBERS %s", hashTriangle.second.toString().c_str());
        }

        for(; j > 0; j--){
            redisGetReply(c, (void **) &reply );
            //unsigned int r = redisGetReply(c, (void **) &reply );
            for (unsigned int k = 0; k < reply->elements; k++)
            {
                string str(reply->element[k]->str);
                result.push_back(str);
            }
        }

    }
    std::map<string,vector<Triangle>> resultMap;
    for (auto t_str : result)
    {
        auto redisReplyImageName = getImageNameFromRedisEntry(t_str);
        auto redisReplyTriangle = getTriangleFromRedisEntry(t_str);
        resultMap[redisReplyImageName];
        resultMap[redisReplyImageName].push_back(redisReplyTriangle);
    }
    cout << "Matches:" << endl;
    for(auto const& ent1 : resultMap)
    {
        auto tempImg = cv::imread(ent1.first);
        //drawTrianglesOntoImage(ent1.second, tempImg);
        //cv::imwrite("./outputImages/outputFromSearch_"+ent1.second[0].toString()+".jpg", tempImg);
        cout << ent1.first << ": " << ent1.second.size() << endl;
    }

    cout << "Number of matches: " << result.size() << endl;
    return result.size();
}


void redisClearDatabase(){
    redisContext *c;
    const char *hostname = "127.0.0.1";
    int port = 6379;

    struct timeval timeout = { 1, 500000 }; // 1.5 seconds
    c = redisConnectWithTimeout(hostname, port, timeout);
    if (c == NULL || c->err) {
        if (c) {
            printf("Connection error: %s\n", c->errstr);
            redisFree(c);
        } else {
            printf("Connection error: can't allocate redis context\n");
        }
        exit(1);
    }
    redisCommand(c,"FLUSHALL");
    redisFree(c);
}

void compareTwoImages(string imageName1, string imageName2) {

    //clear the db
    redisClearDatabase();

    //add the first image to db
    addAllHashesToRedis(imageName1);

    //check for matches using the second image
    cout << "{\n\tcount: " << findMatchingHashInRedis(imageName2) << "\n}";
}

int main(int argc, char* argv[])
{
    if (argc < 3){
        printf("error: no args!!!\n Example:\nTo insert an image run the following command:\n ./runDemo insert inputImages/cat1.png\nTo query the database with an image run the following command:\n ./runDemo lookup inputImages/cat1.png\n");
        return -1;
    }


    if (argc > 2 && !strcmp(argv[1], "insert")){
	for (int i = 2; i < argc; i++) {
    		string imageName = argv[i];
        	addAllHashesToRedis(imageName);
	}
    }else if (argc > 2 && !strcmp(argv[1], "lookup")){
	for (int i = 2; i < argc; i++) {
    		string imageName = argv[i];
        	findMatchingHashInRedis(imageName);
	}
    }else{
        cout << "Bad argument: " << argv[1] << endl;
    }
}
