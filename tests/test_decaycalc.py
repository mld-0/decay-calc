#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=3: 
#   }}}1
#   {{{3
import importlib
import unittest
import os
import sys
import datetime
import dateutil
import logging
import io
import filecmp
from subprocess import Popen, PIPE
from unittest.mock import patch
from freezegun import freeze_time
import difflib
#   pandas must be imported *before* any freezegun fake times are used
import pandas
import inspect
import sys
import argparse
import logging
import traceback
import dateparser
import pprint
#   }}}1
#   {{{1
from decaycalc.decaycalc import DecayCalc

#   debug logging
_log = logging.getLogger('decaycalc')
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(level=logging.DEBUG, format=_logging_format, datefmt=_logging_datetime)

class Test_CliScan(unittest.TestCase):
#   {{{

    _test_postfix = "\n"
    _data_dir = os.environ.get('mld_logs_schedule')
    decaycalc = DecayCalc()
    prefix = "Schedule.calc."
    postfix = ".vimgpg"
    dt_analyse = dateparser.parse("2021-01-02T17:34:42AEST")
    dt_start = dateparser.parse("2021-01-01T16:08:18AEST")
    dt_end = dateparser.parse("2021-01-02T16:08:18AEST")
    label = "D-IR"
    col_label = 0
    col_qty = 1
    col_dt = 3
    delim = ","
    onset = 20 * 60
    halflife = 45 * 60

    def test_helloworld(self):
        pass

    def test_GetFiles_Monthly(self):
        _results = self.decaycalc._GetFiles_Monthly(self._data_dir, self.prefix, self.postfix, self.dt_start, self.dt_end)
        self.assertTrue(len(_results) > 0, "Expect non-empty _results=(%s)" % str(_results))
        sys.stderr.write(self._test_postfix)

    def test_ReadData(self):
        located_filepaths = self.decaycalc._GetFiles_Monthly(self._data_dir, self.prefix, self.postfix, self.dt_start, self.dt_end)
        results_dt, results_qty = self.decaycalc._ReadData(located_filepaths, self.label, self.col_dt, self.col_qty, self.col_label, self.delim)
        self.assertTrue(len(results_dt) > 0, "Expect non-empty results=(%s)" % results_dt)
        sys.stderr.write(self._test_postfix)

    def test_CalculateAtDT(self):
        located_filepaths = self.decaycalc._GetFiles_Monthly(self._data_dir, self.prefix, self.postfix, self.dt_start, self.dt_end)
        results_dt, results_qty = self.decaycalc._ReadData(located_filepaths, self.label, self.col_dt, self.col_qty, self.col_label, self.delim)
        remaining_qty = self.decaycalc.CalculateAtDT(self.dt_analyse, results_dt, results_qty, self.halflife, self.onset)
        sys.stderr.write(self._test_postfix)

#   }}}

