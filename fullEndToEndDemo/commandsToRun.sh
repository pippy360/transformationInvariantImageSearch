#Oh boy, this is a big install, grab a cup of tea and enjoy the wait...
sudo apt-get install git cmake g++ redis-server libboost-all-dev libopencv-dev python-opencv python-numpy python-scipy -y

#remove annoying opencv error
sudo ln /dev/null /dev/raw1394

#make it
cmake .
make

#great now we should have a binary "runDemo"
