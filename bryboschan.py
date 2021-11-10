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
import turningpoint

seplen = 60
sepchr = "-"


class BBSeries(object):
    def __init__(self, series, name="original"):
        """Init BB object

        :param series: time series for dating
        :type series: pandas series object
        """
        self.s = series
        self.name = name
        self.beginDate = series.index[0]
        self.endDate = series.index[-1]

    def draw_ma(self, window):
        """draw the moving average curve

        :param window: number of time-interval to calculate moving average
        :type window: int
        :return: BBSeries object of moving average curve
        :rtype: BBSeries object
        """
        ma = self.s.rolling(window=window).mean().dropna()
        return BBSeries(ma, "ma-%s" % window)

    def draw_spencer(self, window=5, weights=[-3, 12, 17, 12, -3]):
        """draw spencer curve

        :param window: number of time interval for spencer curve, defaults to 5
        :type window: int, optional
        :param weights: weight of spencer curve, defaults to [-3, 12, 17, 12, -3]
        :type weights: list, optional
        :return: BBSeries object of spencer curve
        :rtype: BBSeries object
        """
        spencer = self.s.rolling(window=window, center=True).apply(
            lambda seq: np.average(seq, weights=weights)
        )
        return BBSeries(spencer, "spencer-curve-%s-%s" % (window, weights))

    def _maxima(self, width):
        """find local peak

        :param width: area on either side
        :type width: int
        :return: list of peaks
        :rtype: list
        """
        peaks = []
        for i in self.s.index[width:-width]:
            if max(self.s[i - width : i + width]) == self.s[i]:
                peaks.append(turningpoint.TurningPoint(i, "P", self.s[i]))
        return peaks

    def _minima(self, width):
        """find local troughs

        :param width: area on either side
        :type width: int
        :return: list of peaks
        :rtype: list
        """
        troughs = []
        for i in self.s.index[width:-width]:
            if min(self.s[i - width : i + width]) == self.s[i]:
                troughs.append(turningpoint.TurningPoint(i, "T", self.s[i]))
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
            temp = self.s[p.dti - width : p.dti + width]
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
        self.s.plot()
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
        spencer=False,
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
        curves = [self.draw_ma(window) for window in sorted(ma, reverse=True)]
        curves.append(self)
        if spencer and ma:
            curves.insert(1, self.draw_spencer())

        for idx, curve in enumerate(curves):
            if idx == 0:
                turns = curve.get_turnings(width=width)
            else:
                turns = curve.re_apply(turns, width=width)

            turningpoint.alternation_check(turns)
            turningpoint.duration_check(turns, min_dur=min_dur)
            turningpoint.phase_check(turns, min_pha=min_pha)

            if curve.name == "original":
                turningpoint.start_end_check(turns, self, min_boudary=min_boudary)

            if verbose:
                # print turns information
                print(sepline)
                print(
                    "dating: %s | width: %s | min_dur: %s | min_pha: %s"
                    % (curve.name, width, min_dur, min_pha)
                )
                for num, turn in enumerate(turns):
                    print("(%02d) %s" % (num, turn))
                # plot turns on the series
                curve.plot_turns(turns)

        if not verbose:
            self.plot_turns(turns)
        return turns


def dating(
    s,
    ma=[],
    width=3,
    min_dur=6,
    min_pha=3,
    min_boudary=3,
    spencer=False,
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
    original = BBSeries(s)
    turns = original.dating(
        ma=ma,
        width=width,
        min_dur=min_dur,
        min_pha=min_pha,
        min_boudary=min_boudary,
        spencer=spencer,
        verbose=verbose,
    )

    return turns


def tester(width=3, min_pha=3):
    import sys

    df = pd.read_csv("./test_series.csv")
    s = df["CYCLE_LOGGDP2010B"]
    s.index = pd.period_range(start="2003", freq="Q", periods=len(s))
    args = sys.argv[1:]

    if len(args) > 0:
        mode = args[0]
        if mode == "-s":
            width = int(args[1])
            min_pha = int(args[2])
            turns = dating(s, width=width, min_pha=min_pha)
        elif mode == "-m":
            ma1 = int(args[1])
            ma2 = int(args[2])
            width = int(args[3])
            min_pha = int(args[4])
            turns = dating(
                s,
                ma=[ma1, ma2],
                width=width,
                min_pha=min_pha,
            )
    else:
        turns = dating(s, width=width, min_pha=min_pha)

    print(turns)


if __name__ == "__main__":
    tester()
