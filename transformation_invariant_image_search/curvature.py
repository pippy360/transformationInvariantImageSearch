"""This file takes in a function (represented as a number of points and approximated using a spline)
and returns the local maximums of curvature.
"""

import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.integrate import cumtrapz
from scipy.signal import argrelextrema


SMOOTHING_PARAMETERIZATION_T = None
SMOOTHING_PARAMETERIZATION_S = None


def convert_t_to_arc_length(t_list, fx_t, fy_t, sub_divide=1):
    t = np.arange(len(t_list)) * sub_divide
    dfx = fx_t.derivative(1)
    dfy = fy_t.derivative(1)
    y_vals = np.sqrt(dfx(t) ** 2 + dfy(t) ** 2)

    return cumtrapz(y_vals, t_list, initial=0)


def get_parameterized_function(t, x_pts, y_pts, smoothing=None):
    fx_t = UnivariateSpline(t, x_pts, k=3, s=smoothing)
    fy_t = UnivariateSpline(t, y_pts, k=3, s=smoothing)
    return fx_t, fy_t


def calculate_curvature(arc_length, fx_s, fy_s):
    # Note: curvature points won't be equidistant if the arc_length_list isn't

    x_ = fx_s.derivative(1)(arc_length)
    x__ = fx_s.derivative(2)(arc_length)
    y_ = fy_s.derivative(1)(arc_length)
    y__ = fy_s.derivative(2)(arc_length)

    return abs(x_ * y__ - y_ * x__) / np.power(x_ ** 2 + y_ ** 2, 3 / 2)


def parameterize_function_wrt_arc_length(x, y):
    t = np.arange(x.shape[0])
    fx, fy = get_parameterized_function(t, x, y, SMOOTHING_PARAMETERIZATION_T)

    # for each point (inputX[i], inputY[i]) the "arc_length"
    # gives use the arc length from 0 to that point
    arc_length = convert_t_to_arc_length(t, fx, fy)
    fx_s, fy_s = get_parameterized_function(arc_length, fx(t), fy(t), SMOOTHING_PARAMETERIZATION_S)

    curvature = calculate_curvature(arc_length, fx_s, fy_s)

    return x, y, curvature


def local_maxima_of_curvature(pts, number_of_pixels_per_unit=1):
    '''Get the local maximums of curvature'''

    # set the scale
    input_x = pts[:, 0] / number_of_pixels_per_unit
    input_y = pts[:, 1] / number_of_pixels_per_unit

    # parameterize the function W.R.T. arc length
    xs, ys, curvature = parameterize_function_wrt_arc_length(input_x, input_y)

    # get the local maximums of curvature
    local_maxima = argrelextrema(curvature, np.greater, order=2)

    local_maxima_indexes = local_maxima[0]
    xs_maxima = xs[local_maxima_indexes]
    ys_maxima = ys[local_maxima_indexes]

    # fin_pts += zip(xs_maxima, ys_maxima)

    return xs_maxima, ys_maxima

