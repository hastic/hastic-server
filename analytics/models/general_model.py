from models import Model

import utils
import numpy as np
import pandas as pd
import scipy.signal
from scipy.fftpack import fft
from scipy.signal import argrelextrema
import math
from scipy.stats import gaussian_kde
from scipy.stats import norm



class GeneralModel(Model):

    def __init__(self):
        super()
        self.segments = []
        self.ipats = []
        self.state = {
            'convolve_max': 200,
            'WINDOW_SIZE': 240,
        }
        self.all_conv = []

    def do_fit(self, dataframe: pd.DataFrame, segments: list) -> None:
        data = dataframe['value']
        convolve_list = []
        for segment in segments:
            if segment['labeled']:
                segment_from_index = utils.timestamp_to_index(dataframe, pd.to_datetime(segment['from'], unit='ms'))
                segment_to_index = utils.timestamp_to_index(dataframe, pd.to_datetime(segment['to'], unit='ms'))

                segment_data = data[segment_from_index: segment_to_index + 1]
                if len(segment_data) == 0:
                    continue
                x = segment_from_index + int((segment_to_index - segment_from_index) / 2)
                self.ipats.append(x)
                segment_data = data[x - self.state['WINDOW_SIZE'] : x + self.state['WINDOW_SIZE']]
                segment_min = min(segment_data)
                segment_data = segment_data - segment_min
                convolve = scipy.signal.fftconvolve(segment_data, segment_data)
                convolve_list.append(max(convolve))

        if len(convolve_list) > 0:
            self.state['convolve_max'] = float(max(convolve_list))
        else:
            self.state['convolve_max'] = self.state['WINDOW_SIZE'] / 3

    def do_predict(self, dataframe: pd.DataFrame) -> list:
        data = dataframe['value']
        pat_data = data[self.ipats[0] - self.state['WINDOW_SIZE']: self.ipats[0] + self.state['WINDOW_SIZE']]
        x = min(pat_data)
        pat_data = pat_data - x
        y = max(pat_data)

        for i in range(self.state['WINDOW_SIZE'] * 2, len(data)):
            watch_data = data[i - self.state['WINDOW_SIZE'] * 2: i]
            w = min(watch_data)
            watch_data = watch_data - w
            conv = scipy.signal.fftconvolve(pat_data, watch_data)
            self.all_conv.append(max(conv))
        all_conv_peaks = utils.peak_finder(self.all_conv, self.state['WINDOW_SIZE'] * 2)

        filtered = self.__filter_prediction(all_conv_peaks, data)
        return set(item + self.state['WINDOW_SIZE'] for item in filtered)

    def __filter_prediction(self, segments: list, data: list):
        if len(segments) == 0 or len(self.ipats) == 0:
            return []
        delete_list = []

        for val in segments:
            if self.all_conv[val] < self.state['convolve_max'] * 0.8:
                delete_list.append(val)

        for item in delete_list:
            segments.remove(item)

        return set(segments)