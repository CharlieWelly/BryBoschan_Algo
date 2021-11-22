""" 
BB.py apply Bry and Boschan procedure to identify turning points from a detrend seasonal adjusted time series

To run this module, first the time series need to be read from file and convert to Pandas Series object.
This Pandas Series object need to have "period_range" index. See https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html for further detail.

For example:     
    df = pd.read_csv("./test_series.csv")
    s = df["hp_gdp2010b_sa"]
    s.index = pd.period_range(start="2003", freq="Q", periods=len(s))

Call function dating() with appropriate parameters for dating the time series

For example:
    dating(s, ma=[5, 2], width=3, min_dur=6, min_pha=3, min_boudary=3)
    will apply the procedure to 3 curves: the MA-5, MA-2, and the original curve s

    dating(s, width=3, min_dur=6, min_pha=3, min_boudary=3)
    will apply the procedure to only the original curve: s

    dating(s)
    will apply the precedure to only the original curve: s, with default parameter: width=3, min_dur=6, min_pha=3, min_boudary=3
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from . import turningpoint

seplen = 60
sepchr = "-"


class BBSeries(object):
    def __init__(self, series, start, freq, name="original"):
        """Init BB object

        :param series: time series for dating
        :type series: pandas series object
        """
        self.series = series
        self.start = start
        self.freq = freq
        self.idx = pd.period_range(
            start=self.start, periods=len(self.series), freq=self.freq
        )
        self.series.index = self.idx
        self.name = name
        self.beginDate = series.index[0]
        self.endDate = series.index[-1]

    def rm_outliers(self, threshold, verbose=False):
        spcer = self.draw_spencer()
        stdv = spcer.series.std()
        mean = spcer.series.mean()
        upper = mean + threshold * stdv
        lower = mean - threshold * stdv
        outliers = self.series.loc[(self.series > upper) | (self.series < lower)]
        if verbose and len(outliers) > 0:
            print("Outliers:\n%s" % outliers)
        return self.series.clip(lower, upper)

    def draw_ma(self, *parg, window):
        """draw the moving average curve

        :param window: number of time-interval to calculate moving average
        :type window: int
        :return: BBSeries object of moving average curve
        :rtype: BBSeries object
        """
        series = parg[0] if parg else self.series
        ma = series.rolling(window=window).mean().dropna()
        return BBSeries(ma, self.start, self.freq, "ma-%s" % window)

    def draw_spencer(self, *parg, window=5, weights=[-3, 12, 17, 12, -3]):
        """draw spencer curve

        :param window: number of time interval for spencer curve, defaults to 5
        :type window: int, optional
        :param weights: weight of spencer curve, defaults to [-3, 12, 17, 12, -3]
        :type weights: list, optional
        :return: BBSeries object of spencer curve
        :rtype: BBSeries object
        """
        series = parg[0] if parg else self.series
        spencer = series.rolling(window=window, center=True).apply(
            lambda seq: np.average(seq, weights=weights)
        )
        return BBSeries(
            spencer, self.start, self.freq, "spencer-curve-%s-%s" % (window, weights)
        )

    def _maxima(self, width):
        """find local peak

        :param width: area on either side
        :type width: int
        :return: list of peaks
        :rtype: list
        """
        peaks = []
        for i in self.series.index[width:-width]:
            if max(self.series[i - width : i + width]) == self.series[i]:
                peaks.append(turningpoint.TurningPoint(i, "P", self.series[i]))
        return peaks

    def _minima(self, width):
        """find local troughs

        :param width: area on either side
        :type width: int
        :return: list of peaks
        :rtype: list
        """
        troughs = []
        for i in self.series.index[width:-width]:
            if min(self.series[i - width : i + width]) == self.series[i]:
                troughs.append(turningpoint.TurningPoint(i, "T", self.series[i]))
        return troughs

    def get_turnings(self, width):

        """Identify turning points

        :param width: area on either side of checking point
        :type width: int
        :return: list of Turning Points sorted by time
        :rtype: list
        """
        peaks = self._maxima(width)
        troughs = self._minima(width)
        return sorted((peaks + troughs), key=lambda x: x.dti)

    def re_apply(self, turnings, width):
        """apply set of turning points to second curve

        :param turnings: list of turning points from previous curve
        :type turnings: list
        :param width: area on either side
        :type width: int
        """
        new = []
        for p in turnings:
            temp = self.series[p.dti - width : p.dti + width]
            id = temp.idxmax() if p.sta == "P" else temp.idxmin()
            new.append(turningpoint.TurningPoint(id, p.sta, temp[id]))
        return new

    def plot_turns(self, turns):
        """plot the curve and turning points

        :param curve: BBSeries object
        :type curve: BBseries
        :param turns: list of TurningPoint objects
        :type turns: list
        """
        fig, ax = plt.subplots()
        self.series.plot()
        for turn in turns:
            ax.annotate("x", xy=(turn.dti, turn.val))
        plt.show()

    def dating(
        self,
        ma=[],
        width=3,
        min_dur=6,
        min_pha=3,
        min_boudary=3,
        threshold=3.5,
        spencer=False,
        rm_outliers=False,
        verbose=False,
    ):
        """
        Bry and Boschan dating process for identifying turning points

        :param ma: list of ma curves to draw
        :type ma: list
        :param width: area on either side, defaults to 3
        :type width: int, optional
        :param min_dur: minimum duration of a cycle, defaults to 6
        :type min_dur: int, optional
        :param min_pha: minimum duration of a phase, defaults to 3
        :type min_pha: int, optional
        :param min_boudary: minimum start and end of the series, defaults to 3
        :type min_boudary: int, optional
        :param verbose: to print out result and plot the line, defaults to True
        :type verbose: bool, optional
        :return: list of final TurningPoint objects
        :rtype: list
        """

        sepline = sepchr * seplen

        series = (
            self.rm_outliers(threshold=threshold, verbose=verbose)
            if rm_outliers
            else self.series
        )

        curves = [
            self.draw_ma(series, window=window) for window in sorted(ma, reverse=True)
        ]
        curves.append(self)

        if spencer and ma:
            curves.insert(1, self.draw_spencer(series))

        for idx, curve in enumerate(curves):
            if idx == 0:
                turns = curve.get_turnings(width=width)
            else:
                turns = curve.re_apply(turns, width=width)

            if verbose:
                # print initial information
                print(sepline)
                print(
                    "dating: %s | width: %s | min_dur: %s | min_pha: %s"
                    % (curve.name, width, min_dur, min_pha)
                )

            turningpoint.alternation_check(turns, verbose=verbose)
            turningpoint.duration_check(turns, min_dur=min_dur, verbose=verbose)
            turningpoint.phase_check(turns, min_pha=min_pha, verbose=verbose)

            if curve.name == "original":
                turningpoint.start_end_check(
                    turns, self, min_boudary=min_boudary, verbose=verbose
                )

            if verbose:
                # print result cycle
                for num, turn in enumerate(turns):
                    print("(%02d) %s" % (num, turn))
                # plot turns on the series
                curve.plot_turns(turns)
        return turns


def dating(
    series,
    ma=[],
    width=3,
    min_dur=6,
    min_pha=3,
    min_boudary=3,
    threshold=3.5,
    spencer=False,
    rm_outliers=False,
    verbose=False,
):
    """
    Bry and Boschan dating process for identifying turning points

    :param s: detrend seasonal adjusted original series for dating process
    :type s: pandas time series
    :param width: area on either side, defaults to 3
    :type width: int, optional
    :param min_dur: minimum duration of a cycle, defaults to 6
    :type min_dur: int, optional
    :param min_pha: minimum duration of a phase, defaults to 3
    :type min_pha: int, optional
    :param min_boudary: minimum start and end of the series, defaults to 3
    :type min_boudary: int, optional
    :param verbose: to print out result and plot the line, defaults to True
    :type verbose: bool, optional
    :return: list of final TurningPoint objects
    :rtype: list
    """
    original = BBSeries(series)
    turns = original.dating(
        ma=ma,
        width=width,
        min_dur=min_dur,
        min_pha=min_pha,
        min_boudary=min_boudary,
        threshold=threshold,
        spencer=spencer,
        rm_outliers=rm_outliers,
        verbose=verbose,
    )

    return turns
