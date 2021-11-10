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
    dating(s, 5, 2, width=3, min_dur=6, min_pha=3, min_boudary=3)
    will apply the procedure to 3 curves: the MA-5, MA-2, and the original curve s

    dating(s, width=3, min_dur=6, min_pha=3, min_boudary=3)
    will apply the procedure to only the original curve: s

    dating(s)
    will apply the precedure to only the original curve: s, with default parameter: width=3, min_dur=6, min_pha=3, min_boudary=3
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

seplen = 60
sepchr = "-"


class TurningPoint(object):
    def __init__(self, dti, sta, val):
        """Init turning point object

        :param dti: datetime of the turning point
        :type dti: datetime object
        :param sta: status of turning point: P / T
        :type sta: str
        :param val: value of turning point
        :type val: int
        """
        self.dti = dti
        self.sta = sta
        self.val = val

    def __str__(self):
        return "%s: %s: %.2f" % (self.sta, self.dti, self.val)

    def __repr__(self):
        return "%s: %s: %.2f" % (self.sta, self.dti, self.val)

    def __gt__(self, other):
        return self.val > other.val

    def __lt__(self, other):
        return self.val < other.val

    def __eq__(self, other):
        return self.val == other.val

    def __ge__(self, other):
        return self.val >= other.val

    def __le__(self, other):
        return self.val <= other.val

    def time_diff(self, other):
        return abs((self.dti - other.dti).n)


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
                peaks.append(TurningPoint(i, "P", self.s[i]))
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
                troughs.append(TurningPoint(i, "T", self.s[i]))
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
            new.append(TurningPoint(id, p.sta, temp[id]))
        return new


def alternation_check(turnings):
    """Check for Alternation of Peaks and Troughs

    :param turnings: list of TurningPoint objects
    :type turnings: list
    """
    i = 0
    while i < len(turnings) - 1:
        if turnings[i].sta == turnings[i + 1].sta:
            if turnings[i].sta == "P":
                if turnings[i] <= turnings[i + 1]:
                    turnings.pop(i)
                else:
                    turnings.pop(i + 1)
                    i += 1
            elif turnings[i].sta == "T":
                if turnings[i] >= turnings[i + 1]:
                    turnings.pop(i)
                else:
                    turnings.pop(i + 1)
                    i += 1
        else:
            i += 1
    return turnings


def duration_check(turnings, min_dur):
    """Check for minimum duration of a cycle

    :param turnings: list of TurningPoint objects
    :type turnings: list
    :param min_dur: minimum cycle duration
    :type min_dur: int
    :return: list of evaluated TurningPoint objects
    :rtype: list
    """
    i = 0
    while i < len(turnings) - 2:
        if (turnings[i + 2].dti - turnings[i].dti).n < min_dur:
            if turnings[i].sta == "P":
                if turnings[i + 2] >= turnings[i]:
                    turnings.pop(i)
                else:
                    turnings.pop(i + 2)
            else:
                if turnings[i] >= turnings[i + 1]:
                    turnings.pop(i)
                else:
                    turnings.pop(i + 1)
            turnings = alternation_check(turnings)
            turnings = duration_check(turnings, min_dur)
        else:
            i += 1
    return turnings


def phase_check(turnings, min_pha):
    """
    Check for minimum duration of phase

    :param turnings: list of TurningPoint objects
    :type turnings: list
    :param min_pha: minimum phase duration
    :type min_pha: int
    :return: list of evaluated TurningPoint objects
    :rtype: list
    """
    i = 0
    while i < len(turnings) - 1:
        if (turnings[i + 1].dti - turnings[i].dti).n < min_pha:
            turnings.pop(i + 1)
            turnings = alternation_check(turnings)
            turnings = phase_check(turnings, min_pha)
        else:
            i += 1
    return turnings


def start_end_check(turnings, curve, min_boudary):
    """
    Remove turns that too close to the begining and end of the series

    :param turnings: list of TurningPoint objects
    :type turnings: list
    :param curve: The curve to check
    :type curve: BBSeries object
    :param min_boudary: minimum duration in the start and end of the series
    :type min_boudary: int
    :return: list of evaluated TurningPoint objects
    :rtype: list
    """
    if turnings[0].dti < curve.beginDate + min_boudary:
        turnings.pop(0)
    if turnings[-1].dti > curve.endDate - min_boudary:
        turnings.pop(-1)
    return turnings


def dating(
    s,
    *args,
    width=3,
    min_dur=6,
    min_pha=3,
    min_boudary=3,
    spencer=False,
    verbose=True,
    plot=True
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
    sepline = sepchr * seplen
    original = BBSeries(s)
    curves = [original.draw_ma(arg) for arg in sorted(args, reverse=True)]

    if spencer:
        spencer = original.draw_spencer()
        curves.insert(1, spencer)

    curves.append(original)

    for idx, curve in enumerate(curves):
        if idx == 0:
            turns = curve.get_turnings(width=width)
        else:
            turns = curve.re_apply(turns, width=width)

        alternation_check(turns)
        duration_check(turns, min_dur=min_dur)
        phase_check(turns, min_pha=min_pha)

        if curve.name == "original":
            start_end_check(turns, original, min_boudary=min_boudary)

        if verbose:
            print(sepline)
            print(
                "dating: %s | width: %s | min_dur: %s | min_pha: %s"
                % (curve.name, width, min_dur, min_pha)
            )
            for num, turn in enumerate(turns):
                print("(%02d) %s" % (num, turn))

        if plot:
            plot_turns(curve, turns)

    return turns


def plot_turns(curve, turns):
    """plot the curve and turning points

    :param curve: BBSeries object
    :type curve: BBseries
    :param turns: list of TurningPoint objects
    :type turns: list
    """
    fig, ax = plt.subplots()
    curve.s.plot()
    for turn in turns:
        ax.annotate("x", xy=(turn.dti, turn.val))
    plt.show()


def tester(width=3, min_pha=3):
    import sys

    df = pd.read_csv("./test_series.csv")
    s = df["hp_gdp2010b_sa"]
    s.index = pd.period_range(start="2003", freq="Q", periods=len(s))
    if len(sys.argv) > 1:
        if sys.argv[1] == "-s":
            dating(s, width=int(sys.argv[2]), min_pha=int(sys.argv[3]))
        elif sys.argv[1] == "-m":
            dating(
                s,
                int(sys.argv[2]),
                int(sys.argv[3]),
                width=int(sys.argv[4]),
                min_pha=int(sys.argv[5]),
            )
    else:
        dating(s, width=width, min_pha=min_pha)


if __name__ == "__main__":
    tester()
