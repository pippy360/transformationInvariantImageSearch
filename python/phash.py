import cv2
import numpy as np
from sklearn.neighbors import BallTree


HEX_STRINGS = np.array([f'{x:02x}' for x in range(256)])
BIN_POWERS = 2 ** np.arange(8)


def phash(image, hash_size=8, highfreq_factor=4):
    img_size = hash_size * highfreq_factor
    image = cv2.resize(image, (img_size, img_size))
    image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY if image.ndim == 4 else cv2.COLOR_BGR2GRAY)

    dct = cv2.dct(image.astype(float))
    dctlowfreq = dct[:hash_size, :hash_size]
    dctlowfreq[0, 0] = 0

    return dctlowfreq > np.mean(dctlowfreq)


def hash_to_hex(a):
    index = np.sum(a * BIN_POWERS, axis=2)
    return [''.join(x) for x in HEX_STRINGS[index]]


def hash_triangles(img, triangles):
    n = len(triangles)
    triangles = np.asarray(triangles)

    # basically the return value
    hash_size = 8
    hash_img_size = 32, 32
    low_freq_dct = np.empty((3, n, hash_size, hash_size))

    # size of the target image for affine transform
    size = width, height = int(60 * 0.86), 60

    # helper matrices
    empty_n_identity33 = np.empty((n, 3, 3))
    empty_n_identity33[:, :] = np.identity(3)

    target_points = empty_n_identity33.copy()
    target_points[:, :2, 0] = width / 2, height
    target_points[:, :2, 1] = width, 0

    input_points = empty_n_identity33.copy()
    transpose_m = empty_n_identity33

    # rotate triangles 3 times, one for each edge of the triangle
    rotations = (0, 1, 2), (1, 2, 0), (2, 0, 1)

    for i, rotation in enumerate(rotations):
        p = triangles[:, rotation, :]

        p0 = p[:, 0]
        p1 = p[:, 1] - p0
        p2 = p[:, 2] - p0

        # if p1 is to the right of p2, then switch
        _ = np.cross(p1, p2 - p1) > 0
        p1[_], p2[_] = p2[_], p1[_]

        # calc_transformation_matrix
        transpose_m[:, :2, 2] = -p0
        input_points[:, :2, 0] = p1
        input_points[:, :2, 1] = p2

        input_points_inverse = np.linalg.inv(input_points)
        transform = target_points @ input_points_inverse @ transpose_m
        transform = transform[:, :2, :]

        for k in range(n):
            image = cv2.warpAffine(img, transform[k], size)

            # calculate dct for perceptual hash
            image = cv2.resize(image, hash_img_size)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            dct = cv2.dct(image.astype(float))
            low_freq_dct[i, k] = dct[:hash_size, :hash_size]

    # calculate perceptual hash for every triangle
    low_freq_dct = low_freq_dct.reshape(3 * n, hash_size, hash_size)
    low_freq_dct[:, 0, 0] = 0
    mean = np.mean(low_freq_dct, axis=(1, 2))
    hashes = low_freq_dct > mean[:, None, None]

    return hash_to_hex(hashes)


def triangles_from_keypoints(keypoints, lower=50, upper=400):
    keypoints = np.asarray(keypoints, dtype=float)

    tree = BallTree(keypoints, leaf_size=10)
    i_lower = tree.query_radius(keypoints, r=lower)
    i_upper = tree.query_radius(keypoints, r=upper)
    in_range = [set(u) - set(l) for l, u in zip(i_lower, i_upper)]

    seen = set()
    result = []

    for i, center in enumerate(keypoints):
        seen.add(i)

        in_range_of_center = in_range[i] - seen
        if not in_range_of_center:
            continue

        processed = set()

        for j in in_range_of_center:
            if j < i + 1:
                continue

            points_idx = in_range[j] & in_range_of_center - processed
            if not points_idx:
                continue

            keypoint = keypoints[j]
            points = keypoints[list(points_idx)]
            area = np.absolute(np.cross(points - center, points - keypoint)) / 2
            result += [(center, keypoint, p) for p in points[area > 1300]]

            processed.add(j)

    return result
