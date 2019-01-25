"""This file gets 2D affine transformation-invariant keypoints for a given image.
It's really just a bunch of hacks thrown together that works well enough for the proof of concept.
The whole proof of concept would be drastically better with a well designed 2D affine
transformation-invariant keypointing algorithm.
"""

import sys
import json

import cv2
import numpy as np

import curvature


PIXEL_VALS = [
    16, 124, 115, 68, 98, 176, 225, 55, 50, 53, 129, 19, 57, 160, 143, 237,
    75, 164, 206, 167, 103, 140, 90, 112, 244, 240, 107, 202, 185, 72, 71,
    109, 74, 183, 205, 46, 121, 180, 142, 126, 38, 247, 166, 144, 67, 134,
    194, 198, 23, 186, 33, 163, 24, 117, 37, 76, 147, 47, 52, 42, 70, 108,
    30, 54, 89, 59, 73, 91, 151, 6, 173, 86, 182, 178, 10, 207, 171, 13, 77,
    88, 159, 125, 11, 188, 238, 41, 92, 118, 201, 132, 48, 28, 195, 17, 119,
    64, 25, 45, 114, 80, 187, 105, 204, 158, 20, 169, 83, 191, 199, 234, 136,
    81, 252, 141, 242, 219, 138, 161, 154, 135, 63, 153, 239, 130, 223, 249,
    122, 93, 216, 127, 111, 15, 12, 8, 44, 193, 245, 0, 235, 120, 31, 165, 3,
    155, 43, 26, 152, 94, 29, 232, 35, 218, 230, 233, 214, 217, 7, 156, 189,
    228, 137, 209, 145, 226, 97, 215, 170, 51, 224, 100, 61, 69, 250, 4, 34,
    56, 255, 60, 84, 110, 203, 222, 133, 248, 106, 212, 87, 253, 208, 101, 116,
    251, 190, 99, 32, 113, 157, 27, 79, 82, 146, 149, 5, 210, 65, 22, 181, 131,
    62, 36, 184, 196, 231, 192, 66, 213, 2, 254, 174, 211, 236, 229, 58, 221,
    21, 150, 123, 175, 177, 179, 246, 96, 227, 1, 18, 241, 49, 128, 78, 40,
    14, 162, 85, 39, 172, 104, 9, 200, 220, 139, 168, 95, 243, 197, 148, 102
]


def recolour(img, gauss_width=41):
    pixel_vals = np.array(PIXEL_VALS, dtype=img.dtype)
    div = 40
    size = div * (len(pixel_vals) // div)

    for i in range(0, size, div):
        pixel_vals[i:i + div] = pixel_vals[i]

    pixel_vals[size:] = pixel_vals[size]

    img = cv2.GaussianBlur(img, (gauss_width, gauss_width), 0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    vals = pixel_vals[gray]

    # v = vals[i, j]
    # img[i, j, 2 - v % 3] = v
    m = np.fliplr(np.identity(3, dtype=img.dtype))
    img = m[vals % 3] * vals[:, :, np.newaxis]

    return img


def compute_keypoints(img):
    gauss_width = 21
    img = recolour(img, gauss_width)
    b, _, _ = cv2.split(img)

    points = compute_keypoints_internal(b)
    # points.extend(compute_keypoints_internal(g))
    # points.extend(compute_keypoints_internal(r))

    return points


def find_contours(*args, **kwargs):
    # opencv 2: contours, hierarchy
    # opencv 3: image, contours, hierarchy
    # opencv 4: contours, hierarchy
    # https://docs.opencv.org/4.0.0/d3/dc0/group__imgproc__shape.html
    r = cv2.findContours(*args, **kwargs)
    return r['4' > cv2.__version__ >= '3']


def compute_keypoints_internal(single_channel_image):
    ret, img = cv2.threshold(single_channel_image, 127, 255, cv2.THRESH_BINARY)
    contours = find_contours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    area_here = 400
    contours = [c for c in contours if cv2.contourArea(c) > area_here]

    fin_contours = []

    for cnt in contours:
        M = cv2.moments(cnt)
        c_x = int(M["m10"] / M["m00"])
        c_y = int(M["m01"] / M["m00"])
        fin_contours.append((c_x, c_y))

    for cnt in contours:
        ret = np.array([(pt[0][0], pt[0][1]) for pt in cnt])
        xcoords, ycoords = curvature.local_maxima_of_curvature(ret)
        fin_contours += zip(xcoords, ycoords)

    return fin_contours


def dump_keypoints(img, filename):
    keypoints = [{'x': p[0], 'y': p[1]} for p in compute_keypoints(img)]
    output = {'output': {'keypoints': keypoints}}

    with open(filename, 'w+') as f:
        json.dump(output, f)


def main():
    if len(sys.argv) < 3:
        print("you need to pass in an image path!!!! and also an output path for the json")
        return -1

    img = cv2.imread(sys.argv[1])
    dump_keypoints(img, sys.argv[2])


if __name__ == '__main__':
    main()
