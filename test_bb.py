import unittest
import pandas as pd
from bb.bryboschan import *
from bb.turningpoint import *


class TestBB(unittest.TestCase):
    def setUp(self):

        # SetUp for testing alternation check
        self.dti = pd.period_range(start="2003", freq="Q", periods=75)
        self.turns = [TurningPoint(self.dti[3], "T", -11000)]
        self.turns.append(TurningPoint(self.dti[7], "T", -12000))
        self.turns.append(TurningPoint(self.dti[9], "T", -11000))
        self.turns.append(TurningPoint(self.dti[11], "P", 5000))
        self.turns.append(TurningPoint(self.dti[12], "P", 5000))
        self.turns.append(TurningPoint(self.dti[15], "T", 2000))
        self.turns.append(TurningPoint(self.dti[20], "P", 9000))
        self.turns.append(TurningPoint(self.dti[25], "T", 1000))
        self.alter_turns = alternation_check(self.turns)

        # SetUp for testing duration check
        self.turns1 = [TurningPoint(self.dti[3], "T", -11000)]
        self.turns1.append(TurningPoint(self.dti[4], "P", 2000))
        self.turns1.append(TurningPoint(self.dti[5], "T", -3000))
        self.turns1.append(TurningPoint(self.dti[6], "P", 3000))
        self.turns1.append(TurningPoint(self.dti[7], "T", 2000))
        self.turns1.append(TurningPoint(self.dti[8], "P", 3000))
        self.turns1.append(TurningPoint(self.dti[9], "T", 2000))
        self.turns1.append(TurningPoint(self.dti[10], "P", 3000))
        self.dur_turns1 = duration_check(self.turns1, min_dur=6)

        self.turns2 = [TurningPoint(self.dti[3], "T", -11000)]
        self.turns2.append(TurningPoint(self.dti[4], "P", 2000))
        self.turns2.append(TurningPoint(self.dti[9], "T", -3000))
        self.turns2.append(TurningPoint(self.dti[10], "P", 3000))
        self.turns2.append(TurningPoint(self.dti[14], "T", 2000))
        self.turns2.append(TurningPoint(self.dti[16], "P", 4000))
        self.turns2.append(TurningPoint(self.dti[20], "T", 2000))
        self.turns2.append(TurningPoint(self.dti[21], "P", 3000))
        self.dur_turns2 = duration_check(self.turns2, min_dur=6)

        # SetUp for testing phase check
        self.turns3 = [TurningPoint(self.dti[3], "T", -11000)]
        self.turns3.append(TurningPoint(self.dti[4], "P", 2000))
        self.turns3.append(TurningPoint(self.dti[5], "T", -3000))
        self.turns3.append(TurningPoint(self.dti[8], "P", 3000))
        self.turns3.append(TurningPoint(self.dti[11], "T", 2000))
        self.turns3.append(TurningPoint(self.dti[14], "P", 4000))
        self.turns3.append(TurningPoint(self.dti[15], "T", 2000))
        self.turns3.append(TurningPoint(self.dti[18], "P", 3000))
        self.pha_turns3 = phase_check(self.turns3, min_pha=3)

        # SetUp for testing start-end
        self.dti1 = pd.period_range(start="2003", freq="Q", periods=10)
        self.s = pd.Series(
            [1000, 2000, -2000, 3000, -4000, 6000, 2000, 100, 1000, -2000],
            index=self.dti1,
        )
        self.s = BBSeries(self.s, start="2003", freq="Q")
        self.turns4 = [
            TurningPoint(self.dti1[1], "P", 2000),
            TurningPoint(self.dti1[6], "T", 2000),
        ]
        self.start_end = start_end_check(self.turns4, self.s, 3)

    def tearDown(self):
        pass

    def test_alternation_check(self):
        self.assertEqual(len(self.alter_turns), 5)
        self.assertEqual(self.alter_turns[0].dti, self.dti[7])
        self.assertEqual(self.alter_turns[1].dti, self.dti[12])
        self.assertEqual(self.alter_turns[-1].dti, self.dti[25])

    def test_duration_check(self):
        self.assertEqual(len(self.dur_turns1), 2)
        self.assertEqual(self.dur_turns1[0].dti, self.dti[3])
        self.assertEqual(self.dur_turns1[1].dti, self.dti[10])
        self.assertEqual(len(self.dur_turns2), 5)
        self.assertEqual(self.dur_turns2[0].dti, self.dti[3])
        self.assertEqual(self.dur_turns2[-1].dti, self.dti[20])

    def test_phase_check(self):
        self.assertEqual(len(self.pha_turns3), 4)
        self.assertEqual(self.pha_turns3[1].dti, self.dti[8])
        self.assertEqual(self.pha_turns3[-1].dti, self.dti[14])

    def test_start_end_check(self):
        self.assertEqual(len(self.start_end), 1)
        self.assertEqual(self.s.beginDate, self.dti1[0])
        self.assertEqual(self.s.endDate, self.dti1[9])
        self.assertEqual(self.start_end[0].dti, self.dti1[6])


if __name__ == "__main__":
    unittest.main()
