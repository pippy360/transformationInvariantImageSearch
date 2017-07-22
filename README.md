# Transformation-Invariant Reverse Image Search 

This repo demos a reverse image search algorithm which performs 2D affine transformation-invariant partial image-matching in sublinear time with respect to the number of images in our database.

An online demo with a description of how the algorithm works is available here: 
[Demo](https://pippy360.github.io/transformationInvariantImageSearch)

The /docs directory contains this front end javascript demo: https://pippy360.github.io/transformationInvariantImageSearch

The /fullEndToEndDemo directory contains two full end to end c++ demos of the algorithm. 

Both end to end c++ demos use Redis as a database and do a direct hash lookup for the constant number of hashes produced for each query image. Hence the demos show the algorithm runs in O(1) time with respect to the number of images in the database. A nearest neighbour algorithm could also be used to find the closest hash within some threshold. That would increase the accuracy but the algorithm would run in amortized O(log n) time (depending on which NN algorithm was used). 

The preprocessing the alogrithm does to each image is embarrassingly parallel. Processing each fragment/triangle of the image only requires the 3 points of the triangle and a read-only copy of the image. So if implemented correctly there should be a near linear speedup with respect to the number of cores used.

**However these demos were created quickly as a proof of concept and as a result are very slow. They just show the alogrithm works and that it can work in O(1) time.**



# Setup



To run the two end to end c++ demos first clone the repo and then run the following commands.

This setup was tested on a newly deployed vm on Debian GNU/Linux 9 (stretch), YMMV on different setups.

```
cd ./fullEndToEndDemo
#grab all the dependencies, this install is pretty huge
sudo apt-get install git cmake g++ redis-server libboost-all-dev libopencv-dev python-opencv python-numpy python-scipy -y

#make it
cmake .
make

#then run either ./runDemo1.sh or ./runDemo2.sh to run the demo
```


# Demo 1


To run this demo go to the /fullEndToEndDemo directory and run ./runDemo1.sh 

This demo shows the original image below matching the 8 transformed images below. Each image has some combination of 2D affine transformations applied to it. The demo inserts each of the 8 images individually into the database and then queries the database with the original image.



![Original Cat Image](https://pippy360.github.io/transformationInvariantImageSearch/images/cat_original.png)

![Transformed Cat Images](https://pippy360.github.io/transformationInvariantImageSearch/images/8cats.png)



# Demo 2


To run this demo go to the /fullEndToEndDemo directory and run ./runDemo2.sh 

This demo shows partial image matching. The query image below (c) is a composite of images (a) and (b). The demo inserts images (a) and (b) into the database and then queries with image (c). Image (d) and (e) show the matching fragments, each coloured triangle is a fragment of the image that matched the composite image (c).



![Partial Image Match Example](https://pippy360.github.io/transformationInvariantImageSearch/images/compositeMatching.png)
