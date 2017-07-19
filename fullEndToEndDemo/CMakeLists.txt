cmake_minimum_required(VERSION 3.0)
project(imageHashTesting)

set(CMAKE_CXX_STANDARD 11)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/Modules/")

find_package(Boost REQUIRED)

#find_package(hiredis REQUIRED)

include_directories(${Boost_INCLUDE_DIRS})
include_directories(include)

find_package(OpenMP REQUIRED)

set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")

include_directories(src)

include_directories(include)

SET(TARGET_H
        src/AverageHash.h
        src/BlockMeanHash.h
        src/PerceptualHash.h
        src/FragmentHash.h
        src/Keypoint.h
        src/ShapeAndPositionInvariantImage.h
        src/Triangle.h
	src/mainImageProcessingFunctions.hpp        
        )

set(IMAGE_HASH_FILES 
        src/img_hash_opencv_module/phash.cpp
        src/img_hash_opencv_module/PHash_Fast.cpp
        )


set(SOURCE_FILE 
        src/main.cc
	${IMAGE_HASH_FILES} 
	)

find_package( OpenCV REQUIRED )
include_directories(${OpenCV_INCLUDE_DIRS})

#set( CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin )
set( CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib )

add_executable(demo.out ${SOURCE_FILE} ${TARGET_H})

link_directories(lib)
target_link_libraries(runDemo ${OpenCV_LIBS})
target_link_libraries(runDemo ${CMAKE_CURRENT_SOURCE_DIR}/lib/libhiredis.a)

# Options. Turn on with 'cmake -Dmyvarname=ON'.

set(CMAKE_CXX_FLAGS "-std=c++11 -fopenmp -g -Wall")



get_property(dirs DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY INCLUDE_DIRECTORIES)
foreach(dir ${dirs})
  message(STATUS "dir='${dir}'")
endforeach()
