# transformationInvariantImageSearch
A reverse image search algorithm which performs 2D affine transformation-invariant partial image-matching in sublinear time
Online demo available here: https://pippy360.github.io/transformationInvariantImageSearch

This repo is a cleaned up version of the many other repos on my github that this project is spread across.

The /docs directory contains this front end javascript demo https://pippy360.github.io/transformationInvariantImageSearch

The /fullEndToEndDemo directory contains two full end to end demos of the algorithm. 

#Demo 1

This demo shows the original image below matching the 8 transformed images below. Each image has some combination of 2D affine transformations applied to it. The demo inserts each of the 8 images individually into the database and then queries the database with the original image.

![Original Cat Image](https://pippy360.github.io/transformationInvariantImageSearch/images/cat_original.png)

![Transformed Cat Images](https://pippy360.github.io/transformationInvariantImageSearch/images/compositeMatching.png)

#Demo 2

This demo shows partial image matching. The query image below (c) is a composite of images (a) and (b). The demo inserts images (a) and (b) into the database and then queries with image (c). Image (d) and (e) show the matching fragments, each coloured triangle is a fragment of the image that matched the composite image (c).

![Partial Image Match Example](https://pippy360.github.io/transformationInvariantImageSearch/images/compositeMatching.png)
