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

    def __repr__(self):
        return "<%s: %s: %.2f>" % (self.sta, self.dti, self.val)

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


def duration_check(turnings, min_dur, verbose=False):
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
        printed = None
        if TurningPoint.time_diff(turnings[i], turnings[i + 2]) < min_dur:
            if turnings[i].sta == "P":
                if turnings[i + 2] >= turnings[i]:
                    printed = turnings.pop(i)
                else:
                    printed = turnings.pop(i + 2)
            else:
                if turnings[i] >= turnings[i + 1]:
                    printed = turnings.pop(i)
                else:
                    printed = turnings.pop(i + 1)
            if verbose:
                print("remove %s: failed duration check" % printed)

            turnings = alternation_check(turnings, verbose)
            turnings = duration_check(turnings, min_dur, verbose)

        else:
            i += 1
    return turnings


def alternation_check(turnings, verbose=False):
    """Check for Alternation of Peaks and Troughs

    :param turnings: list of TurningPoint objects
    :type turnings: list
    """
    i = 0
    while i < len(turnings) - 1:
        printed = None
        if turnings[i].sta == turnings[i + 1].sta:
            if turnings[i].sta == "P":
                if turnings[i] <= turnings[i + 1]:
                    printed = turnings.pop(i)
                else:
                    printed = turnings.pop(i + 1)
                    i += 1
            elif turnings[i].sta == "T":
                if turnings[i] >= turnings[i + 1]:
                    printed = turnings.pop(i)
                else:
                    printed = turnings.pop(i + 1)
                    i += 1
            if verbose:
                print("remove %s: failed alternation check" % printed)
        else:
            i += 1
    return turnings


def phase_check(turnings, min_pha, verbose=False):
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
        printed = None
        if TurningPoint.time_diff(turnings[i], turnings[i + 1]) < min_pha:
            printed = turnings.pop(i + 1)
            if verbose:
                print("remove %s: failed phase_check" % printed)
            turnings = alternation_check(turnings)
            turnings = phase_check(turnings, min_pha)
        else:
            i += 1
    return turnings


def start_end_check(turnings, curve, min_boudary, verbose=False):
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
    printed = None
    if turnings[0].dti < curve.beginDate + min_boudary:
        printed = turnings.pop(0)
    if turnings[-1].dti > curve.endDate - min_boudary:
        printed = turnings.pop(-1)
    if verbose and printed:
        print("remove %s: falied start_end_check" % printed)
    return turnings
