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
        if TurningPoint.time_diff(turnings[i], turnings[i + 1]) < min_pha:
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
