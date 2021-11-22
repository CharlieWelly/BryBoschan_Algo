import sys
import pandas as pd
from bb.bryboschan import dating


def tester(width=3, min_pha=3):

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
