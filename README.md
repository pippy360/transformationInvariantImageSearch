# Transformation-Invariant Reverse Image Search 

This repo demos a reverse image search algorithm which performs 2D affine transformation-invariant partial image-matching in sublinear time with respect to the number of images in our database.

An online demo with a description of how the algorithm works is available here: 
[Demo](https://pippy360.github.io/transformationInvariantImageSearch)

The /docs directory contains this front end javascript demo: https://pippy360.github.io/transformationInvariantImageSearch

The /fullEndToEndDemo directory contains two full end to end c++ demos of the algorithm. 

The two end to end c++ demos use Redis as a database and do a direct hash lookup for the constant number of hashes produced for each query image. Each demo runs in O(1) time with respect to the number of images in the database. A nearest neighbor algorithm could also be used instead to find the closest hash within some threshold which would increase the accuracy but then the algorithm would run in amortized O(log n) time (depending on which NN algorithm was used). 

Processing each fragment/triangle of the image only requires the 3 points of the triangle and a read-only copy of the image  so the preprocessing for an image is embarrassingly parallel. If implemented correctly there should be a near linear speedup with respect to the number of cores used.

**However these demos were created quickly as a proof of concept and as a result are very slow. The demos show the alogrithm works and that it can work in O(1) time.**



# Setup



This setup was tested on a newly deployed vm on Debian GNU/Linux 9 (stretch), YMMV on different setups.

Instead of running these commands manually you can run the ./setup.sh script while in the /fullEndToEndDemo directory.

Or if you want to run the commands manually...

```console
# From the root of the repo go to ./fullEndToEndDemo
cd ./fullEndToEndDemo

# Grab all the dependencies, this install is pretty huge
sudo apt-get update
sudo apt-get install git cmake g++ redis-server libboost-all-dev libopencv-dev python-opencv python-numpy python-scipy -y

#Make it
cmake .
make

# This step is optional. It removes a pointless annoying error opencv spits out
# About: https://stackoverflow.com/questions/12689304/ctypes-error-libdc1394-error-failed-to-initialize-libdc1394
sudo ln /dev/null /dev/raw1394

# Then run either ./runDemo1.sh or ./runDemo2.sh to run the demo


```

# Python setup

All credit for the python code goes to [rachmadaniHaryono](https://github.com/rachmadaniHaryono) and [meowcoder](https://github.com/meowcoder).

This setup was tested on a newly deployed vm on Ubuntu 18.04 LTS, YMMV on different setups.

To use python package, do the following:

```console
sudo apt-get update
sudo apt-get install python3-pip python3-opencv redis-server -y

# On some systems this path is missing
# read more here: https://github.com/pypa/pip/issues/3813
PATH="$PATH:~/.local/bin"

# cd to project directory
pip3 install .
```

if you got permission error, install it under virtual env or use `--user` flag.

# Demo 1


To run this demo go to the /fullEndToEndDemo directory and run ./runDemo1.sh 

This demo shows the original image below matching the 8 transformed images below. Each image has some combination of 2D affine transformations applied to it. The demo inserts each of the 8 images individually into the database and then queries the database with the original image.


![Original Cat Image](https://pippy360.github.io/transformationInvariantImageSearch/images/cat_original.png)

![Transformed Cat Images](https://pippy360.github.io/transformationInvariantImageSearch/images/8cats.png)

## Output

Here the 8 cats images are inserted first and then the database is queried with the orginal cat image. The original image matches all 8 images despite the transfomations. 

The low number of partial image matches is because we are doing direct hash lookups and so even a small bit of change (for example from antialising) can cause the perceptual hash to be ever so slightly off. Finding a closest hash using nearest neighbor would solve this issue.
  
The demo takes <s>2 minutes</s> (1 minute 38 seconds*) to run on a quad core VM but could run orders of magnitude faster with a better implementation.

*Thanks to [meowcoder](https://github.com/meowcoder) for the speed up!

```console
user@instance-1:~/transformationInvariantImageSearch/fullEndToEndDemo$ time ./runDemo1.sh 
Loading image: inputImages/cat1.png ... done
Added 46725 image fragments to DB
Loading image: inputImages/cat2.png ... done
Added 65769 image fragments to DB
Loading image: inputImages/cat3.png ... done
Added 34179 image fragments to DB
Loading image: inputImages/cat4.png ... done
Added 44388 image fragments to DB
Loading image: inputImages/cat5.png ... done
Added 47799 image fragments to DB
Loading image: inputImages/cat6.png ... done
Added 44172 image fragments to DB
Loading image: inputImages/cat7.png ... done
Added 67131 image fragments to DB
Loading image: inputImages/cat8.png ... done
Added 18078 image fragments to DB
Loading image: inputImages/cat_original.png ... done
Added 30372 image fragments to DB
Loading image: inputImages/cat_original.png ... done
Matches:
inputImages/cat1.png: 12
inputImages/cat2.png: 16
inputImages/cat3.png: 15
inputImages/cat4.png: 1
inputImages/cat5.png: 2
inputImages/cat6.png: 4
inputImages/cat7.png: 43
inputImages/cat8.png: 18
inputImages/cat_original.png: 30352
Number of matches: 30463

real    1m38.352s
user    2m6.140s
sys     0m6.592s
```

python example

```console
$ time transformation-invariant-image-search insert fullEndToEndDemo/inputImages/cat*  &&  \
$ time transformation-invariant-image-search lookup fullEndToEndDemo/inputImages/cat_original.png

loading fullEndToEndDemo/inputImages/cat1.png
100%|██| 3/3 [00:07<00:00,  2.66s/it]
100%|██| 3/3 [00:08<00:00,  2.70s/it]
100%|█| 3/3 [00:00<00:00, 270.58it/s]
100%|| 1/1 [00:00<00:00, 2457.12it/s]
added 58956 fragments for fullEndToEndDemo/inputImages/cat1.png
loading fullEndToEndDemo/inputImages/cat2.png
100%|██| 3/3 [00:07<00:00,  2.64s/it]
100%|██| 3/3 [00:08<00:00,  2.76s/it]
100%|█| 3/3 [00:00<00:00, 149.91it/s]
100%|█| 1/1 [00:00<00:00, 902.00it/s]
added 58486 fragments for fullEndToEndDemo/inputImages/cat2.png
loading fullEndToEndDemo/inputImages/cat3.png
100%|█████████| 3/3 [00:04<00:00,  1.51s/it]
100%|█████████| 3/3 [00:04<00:00,  1.56s/it]
100%|█| 5025/5025 [00:01<00:00, 3570.22it/s]
added 30141 fragments for fullEndToEndDemo/inputImages/cat3.png
loading fullEndToEndDemo/inputImages/cat4.png
100%|███| 3/3 [00:07<00:00,  2.58s/it]
100%|███| 3/3 [00:07<00:00,  2.62s/it]
100%|██| 3/3 [00:00<00:00, 434.36it/s]
100%|█| 1/1 [00:00<00:00, 1709.87it/s]
added 53013 fragments for fullEndToEndDemo/inputImages/cat4.png
loading fullEndToEndDemo/inputImages/cat5.png
100%|█████████| 3/3 [00:08<00:00,  2.90s/it]
100%|█████████| 3/3 [00:09<00:00,  3.07s/it]
100%|█| 9420/9420 [00:02<00:00, 3238.60it/s]
added 56493 fragments for fullEndToEndDemo/inputImages/cat5.png
loading fullEndToEndDemo/inputImages/cat6.png
100%|█████████| 3/3 [00:07<00:00,  2.41s/it]
100%|█████████| 3/3 [00:07<00:00,  2.50s/it]
100%|█| 7347/7347 [00:02<00:00, 2953.52it/s]
added 44030 fragments for fullEndToEndDemo/inputImages/cat6.png
loading fullEndToEndDemo/inputImages/cat7.png
100%|███████████| 3/3 [00:11<00:00,  3.82s/it]
100%|███████████| 3/3 [00:11<00:00,  3.94s/it]
100%|█| 10544/10544 [00:04<00:00, 2393.00it/s]
added 63089 fragments for fullEndToEndDemo/inputImages/cat7.png
loading fullEndToEndDemo/inputImages/cat8.png
100%|█████████| 3/3 [00:03<00:00,  1.06s/it]
100%|█████████| 3/3 [00:03<00:00,  1.07s/it]
100%|█| 3160/3160 [00:01<00:00, 3138.56it/s]
added 18899 fragments for fullEndToEndDemo/inputImages/cat8.png
loading fullEndToEndDemo/inputImages/cat_original.png
100%|█████████| 3/3 [00:05<00:00,  1.93s/it]
100%|█████████| 3/3 [00:05<00:00,  1.94s/it]
100%|█| 5795/5795 [00:01<00:00, 3211.96it/s]
added 34764 fragments for fullEndToEndDemo/inputImages/cat_original.png
transformation-invariant-image-search insert fullEndToEndDemo/inputImages/cat  141,98s user 10,14s system 159% cpu 1:35,54 total
loading fullEndToEndDemo/inputImages/cat_original.png
100%|█████████| 3/3 [00:05<00:00,  1.83s/it]
100%|█████████| 3/3 [00:05<00:00,  1.94s/it]
100%|█| 5795/5795 [00:01<00:00, 3221.91it/s]
matches for fullEndToEndDemo/inputImages/cat_original.png:
34770      fullEndToEndDemo/inputImages/cat_original.png
237        fullEndToEndDemo/inputImages/cat7.png
36         fullEndToEndDemo/inputImages/cat2.png
19         fullEndToEndDemo/inputImages/cat4.png
14         fullEndToEndDemo/inputImages/cat8.png
7          fullEndToEndDemo/inputImages/cat1.png
4          fullEndToEndDemo/inputImages/cat3.png
2          fullEndToEndDemo/inputImages/cat5.png
1          fullEndToEndDemo/inputImages/cat6.png
transformation-invariant-image-search lookup   12,71s user 1,62s system 151% cpu 9,472 total
```

# Demo 2


To run this demo go to the /fullEndToEndDemo directory and run ./runDemo2.sh 

This demo shows partial image matching. The query image below (c) is a composite of images (a) and (b). The demo inserts images (a) and (b) into the database and then queries with image (c). Image (d) and (e) show the matching fragments, each coloured triangle is a fragment of the image that matched the composite image (c).

![Partial Image Match Example](https://pippy360.github.io/transformationInvariantImageSearch/images/compositeMatching.png)

## Output

Here the two images mona.jpg and van_gogh.jpg are inserted into the database and then the database is queried with monaComposite.jpg. The demo takes <s>5 minutes 17 seconds</s> (4 minutes 36 seconds*) to run on a quad core VM but could run orders of magnitude faster with a better implementation.

*Thanks to [meowcoder](https://github.com/meowcoder) for the speed up!

```console
user@instance-1:~/transformationInvariantImageSearch/fullEndToEndDemo$ time ./runDemo2.sh 
Loading image: ./inputImages/mona.jpg ... done
Added 26991 image fragments to DB
Loading image: ./inputImages/van_gogh.jpg ... done
Added 1129896 image fragments to DB
Loading image: ./inputImages/monaComposite.jpg ... done
Matches:
./inputImages/mona.jpg: 5
./inputImages/van_gogh.jpg: 1478
Number of matches: 1483

real    4m36.635s
user    6m50.988s
sys     0m18.224s
```

python example

```console
$ time transformation-invariant-image-search insert ./fullEndToEndDemo/inputImages/mona.jpg ./fullEndToEndDemo/inputImages/van_gogh.jpg && \
$ time transformation-invariant-image-search lookup ./fullEndToEndDemo/inputImages/monaComposite.jpg

loading ./fullEndToEndDemo/inputImages/mona.jpg
100%|███| 3/3 [00:03<00:00,  1.24s/it]
100%|███| 3/3 [00:03<00:00,  1.20s/it]
100%|██| 3/3 [00:00<00:00, 302.48it/s]
100%|█| 1/1 [00:00<00:00, 2471.60it/s]
added 24145 fragments for ./fullEndToEndDemo/inputImages/mona.jpg
loading ./fullEndToEndDemo/inputImages/van_gogh.jpg
100%|█████████████| 3/3 [02:50<00:00, 56.01s/it]
100%|█████████████| 3/3 [02:50<00:00, 56.14s/it]
100%|█| 178267/178267 [00:56<00:00, 3170.20it/s]
added 1058329 fragments for ./fullEndToEndDemo/inputImages/van_gogh.jpg
transformation-invariant-image-search insert    384,51s user 12,84s system 168% cpu 3:56,42 total
loading ./fullEndToEndDemo/inputImages/monaComposite.jpg
100%|███████████| 3/3 [01:01<00:00, 20.88s/it]
100%|███████████| 3/3 [01:01<00:00, 20.77s/it]
100%|█| 61563/61563 [00:19<00:00, 3129.92it/s]
matches for ./fullEndToEndDemo/inputImages/monaComposite.jpg:
1332       ./fullEndToEndDemo/inputImages/van_gogh.jpg
11         ./fullEndToEndDemo/inputImages/mona.jpg
transformation-invariant-image-search lookup   133,29s user 5,07s system 164% cpu 1:24,30 total
```
