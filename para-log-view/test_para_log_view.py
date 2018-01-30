#!/bin/env dls-python
import unittest, logging
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()