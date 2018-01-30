#!/bin/env dls-python
import unittest, logging, datetime
import para_log_view

example_line = "[Sat Jan 27 09:13:38 2018]2018/01/27 09:13:38.723 FrameHandler: Run[3]--AcqComplete[0]--> Idle[0] "
bad_lines = ["[-- Console up -- Sat Jan 27 00:00:10 2018] ",
             "@@@ Welcome to the procServ process server (procServ Process Server 2.5.1) "]

class TestParser(unittest.TestCase):
    def test_date(self):
        date = para_log_view.parse_date(example_line)
        print date
        self.assertEqual(date,"Sat Jan 27 09:13:38 2018")

    def test_bad_date(self):
        for bad_line in bad_lines:
            date = para_log_view.parse_date(bad_line)
            self.assertEqual(date,"")

    def test_strptime(self):
        date = para_log_view.get_date_from_line(example_line)
        print date
        self.assertEqual(date.year, 2018)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 27)
        self.assertEqual(date.hour, 9)
        self.assertEqual(date.minute, 13)
        self.assertEqual(date.second, 38)

    def test_bad_strptime(self):
        for bad_line in bad_lines:
            date = para_log_view.get_date_from_line(bad_line)
            self.assertEqual(date, None)

    def test_advance_hour(self):
        x_date = datetime.datetime(year = 2018,
                                   month =1,
                                   day = 27,
                                   hour = 15,
                                   minute = 12,
                                   second=1)

        y_date = datetime.datetime(year=2018,
                                   month=1,
                                   day=27,
                                   hour=16,
                                   minute=12,
                                   second=2)

        self.assertEqual(para_log_view.advance_hour(14, x_date, y_date), 15)
        self.assertEqual(para_log_view.advance_hour(14, x_date, x_date), 15)
        self.assertEqual(para_log_view.advance_hour(14, x_date, None), 15)
        self.assertEqual(para_log_view.advance_hour(14, None, y_date), 16)
        self.assertEqual(para_log_view.advance_hour(14, None, None), 14)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()