#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=3: 
#   }}}1
import logging
import argparse
import io
import argcomplete
import inspect
import sys
import importlib
import importlib.resources
import math
import csv
import time
import glob
#import platform
import re
import time
import pytz
import pprint
#import textwrap
import dateutil.parser
import dateutil.tz
import dateutil.relativedelta 
#import time
#import tempfile
import logging
import os
#from subprocess import Popen, PIPE, STDOUT
#from os.path import expanduser
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from io import StringIO
from tzlocal import get_localzone
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import datetime
import pandas
import dateparser
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
#   {{{2
_log = logging.getLogger('decaycalc')
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(level=logging.DEBUG, format=_logging_format, datefmt=_logging_datetime)

class DecayCalc(object):

    threshold_halflife_count = 12

    #   Continue: 2021-01-03T17:17:49AEST function, for a given month, and a given list of log labels, read all log data for that month, and previous month, then calculate and plot quantities for all given label item for each day in that month

    ##   Given <arguments>, (call methods to) get lists of data from file(s) in arg_data_dir, and return list of calculated qtys remaining for each datetime in arg_dt_list 
    #def CalculateFromFilesRange_Monthly(self, arg_dt_list, arg_data_dir, arg_halflife, arg_onset, arg_file_prefix, arg_file_postfix):
    #    pass

    #   About: (Does not handle reading of qty/datetimes from files) Given a day (either as string or python datetime), and lists of datetimes/qtys needed by <CalculationFunction> , calculate qty for each minute of given day and return minute dt range as list and corresponding list of qtys
    def CalculateRangeForDay(self, arg_day, arg_dt_items, arg_qty_items, arg_halflife, arg_onset):
        day_start, day_end = self._DayStartAndEnd_Minutes_FromDate(arg_day)
        _result_dt_list_pandas  = pandas.date_range(start=day_start, end=day_end, freq="min")
        _result_dt_list = []
        _result_qty_list = []
        for loop_dt_pandas in _result_dt_list_pandas:
            loop_dt = loop_dt_pandas.to_pydatetime()
            loop_qty = self.CalculateAtDT(loop_dt, arg_dt_items, arg_qty_items, arg_halflife, arg_onset)
            _result_dt_list.append(loop_dt)
            _result_qty_list.append(loop_qty)
        #_log.debug("loop_qty=(%s)" % str(loop_qty))
        return [ _result_dt_list, _result_qty_list ]
        

    def PlotResultsForDay(self, arg_result_dt, arg_result_qty):
        #   Remove timezone from datetimes
        arg_result_dt_nonetzinfo = []
        for loop_dt in arg_result_dt:
            arg_result_dt_nonetzinfo.append(loop_dt.replace(tzinfo=None))
        #   Hide log output for matplotlib
        mpl_logger = logging.getLogger('matplotlib')
        mpl_logger.setLevel(logging.WARNING)
        fig, ax = plt.subplots()
        ax.plot(arg_result_dt_nonetzinfo, arg_result_qty)
        #ax.plot(range(len(arg_result_qty)), arg_result_qty)
        myFmt = DateFormatter("%H")
        from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)
        ax.xaxis.set_major_formatter(myFmt)
        ax.set_ylim(0, 15)
        ax.set_xlim(arg_result_dt_nonetzinfo[0], arg_result_dt_nonetzinfo[-1])
        ax.xaxis.set_major_locator(MultipleLocator((1/24)))
        ax.yaxis.set_minor_locator(AutoMinorLocator(1))
        #fig.autofmt_xdate()
        plt.show()



    #   About: given lists arg_qty_items/arg_dt_items, (assuming expodential decay of arg_halflife and linear onset of arg_onset), find the qty remaining at arg_dt
    def CalculateAtDT(self, arg_dt, arg_dt_items, arg_qty_items, arg_halflife, arg_onset):
    #   {{{
        _log.debug("arg_dt=(%s)" % str(arg_dt))
        result_qty = Decimal(0.0)
        for loop_dt, loop_qty in zip(arg_dt_items, arg_qty_items):
            #   Reconcile timezones 
            if (loop_dt.tzinfo is None) and (arg_dt.tzinfo is not None):
                loop_dt = loop_dt.replace(tzinfo = arg_dt.tzinfo)
            elif (arg_dt.tzinfo is None) and (loop_dt.tzinfo is not None):
                arg_dt = arg_dt.replace(tzinfo = loop_dt.tzinfo)
            #   get difference between arg_dt and loop_dt in seconds
            loop_printdebug = False
            loop_delta_s = (arg_dt - loop_dt).total_seconds()
            loop_result_qty = Decimal(0.0)
            if (loop_delta_s > arg_onset) and (loop_delta_s < arg_halflife * self.threshold_halflife_count):
                loop_hl_fraction = (loop_delta_s - arg_onset) / arg_halflife
                if loop_printdebug:
                    _log.debug("loop_dt=(%s)" % str(loop_dt))
                    _log.debug("loop_delta_s=(%s)" % str(loop_delta_s))
                    _log.debug("loop_hl_fraction=(%s)" % str(loop_hl_fraction))
                    _log.debug("loop_result_qty=(%s)" % str(loop_result_qty))
                loop_result_qty = loop_qty * Decimal(0.5) ** Decimal(loop_hl_fraction)
            elif (loop_delta_s > 0) and (loop_delta_s < arg_halflife * self.threshold_halflife_count):
                loop_result_qty = loop_qty * Decimal(loop_delta_s / arg_onset)
                if loop_printdebug:
                    _log.debug("loop_dt=(%s)" % str(loop_dt))
                    _log.debug("loop_delta_s=(%s)" % str(loop_delta_s))
                    _log.debug("loop_hl_fraction=(%s)" % str(loop_hl_fraction))
                    _log.debug("loop_result_qty=(%s)" % str(loop_result_qty))
            result_qty += loop_result_qty
        _log.debug("result_qty=(%s)" % str(result_qty))
        return result_qty
    #   }}}

    #   About: Get a list of the files in arg_data_dir, where each file is of the format 'arg_file_prefix + date_str + arg_file_postfix', and date_str is %Y-%m for each year and month between one month before arg_dt_first, and arg_dt_last
    def _GetFiles_Monthly(self, arg_data_dir, arg_file_prefix, arg_file_postfix, arg_dt_first, arg_dt_last):
    #   {{{
        #   Get list of year/month strings for months between arg_dt_first/arg_dt_last, inclusive, plus the month before arg_dt_first
        if (arg_dt_first > arg_dt_last):
            raise Exception("Invalid arg_dt_first=(%s) > arg_dt_last=(%s)" % (str(arg_dt_first), str(arg_dt_last)))
        _dt_format_convertrange = '%Y-%m-%dT%H:%M:%S%Z'
        _dt_format_output = '%Y-%m'
        _dt_freq = 'MS'
        arg_dt_beforeFirst = arg_dt_first + relativedelta(months = -1)
        _log.debug("arg_dt_first=(%s)" % str(arg_dt_first))
        _log.debug("arg_dt_beforeFirst=(%s)" % str(arg_dt_beforeFirst))
        _log.debug("arg_dt_last=(%s)" % str(arg_dt_last))
        dt_Range = [ x for x in pandas.date_range(start=arg_dt_beforeFirst.strftime(_dt_format_convertrange), end=arg_dt_last.strftime(_dt_format_convertrange), freq=_dt_freq) ]
        dt_Range_str = [ x.strftime(_dt_format_output) for x in dt_Range ]
        _log.debug("dt_Range=(%s)" % str(dt_Range))
        _log.debug("dt_Range_str=(%s)" % str(dt_Range_str))
        #   Raise exception if arg_data_dir doesn't exist
        if not os.path.isdir(arg_data_dir):
            raise Exception("dir not found arg_data_dir=(%s)" % str(arg_data_dir))
        #   Get list of files of format 'arg_file_prefix + date_str + arg_file_postfix' which exist, with warning for those which don't. Raise exception if no files are found
        located_filepaths = []
        for loop_dt_str in dt_Range_str:
            loop_candidate_filename = arg_file_prefix + loop_dt_str + arg_file_postfix
            loop_candidate_filepath = os.path.join(arg_data_dir, loop_candidate_filename)
            if os.path.isfile(loop_candidate_filepath):
                located_filepaths.append(loop_candidate_filepath)
        _log.debug("located_filepaths:\n%s" % pprint.pformat(located_filepaths))
        if len(located_filepaths) == 0:
            raise Exception("no files located")
        return located_filepaths
        #   }}}

    #   About: Given a list of files, get as a list qtys and datetimes (from columns arg_col_qty and arg_col_dt), for lines where value in column arg_col_label==arg_label (if arg_label is not None, otherwise read every line). Return [ results_dt, results_qty ] lists, sorted chronologicaly 
    def _ReadData(self, arg_files_list, arg_label, arg_col_dt, arg_col_qty, arg_col_label, arg_delim):
    #   {{{
        _log.debug("arg_label=(%s)" % str(arg_label))
        _log.debug("arg_delim=(%s)" % str(arg_delim))
        _log.debug("cols: (dt, qty, label)=(%s, %s, %s)" % (arg_col_dt, arg_col_qty, arg_col_label))
        results_dt = []
        results_qty = []
        for loop_filepath in arg_files_list:
            loop_filestr = self._DecryptGPGFileToString(loop_filepath)
            for loop_line in loop_filestr.split("\n"):
                loop_line_split = loop_line.split(arg_delim)
                #_log.debug("loop_line_split=(%s)" % str(loop_line_split))
                if (arg_label is None) or (loop_line_split[arg_col_label] == arg_label):
                    loop_qty_str = loop_line_split[arg_col_qty]
                    loop_dt_str = loop_line_split[arg_col_dt]
                    loop_qty = Decimal(loop_qty_str)
                    #   If datetime is in 'dts' format, i.e: (2021-01-02)-(21-17-11), transform to iso format
                    regex_dts = r"\((\d{4}-\d{2}-\d{2})\)-\((\d{2})-(\d{2})-?(\d{2})\)"
                    _match_regex = re.match(regex_dts, loop_dt_str)
                    if (_match_regex is not None):
                        loop_dt_str = _match_regex.group(1) + "T" + _match_regex.group(2) + ":" + _match_regex.group(3) + ":" + _match_regex.group(4)
                    loop_dt = dateparser.parse(loop_dt_str)
                    if (loop_dt is None):
                        raise Exception("Failed to parse loop_dt_str=(%s)" % str(loop_dt_str))
                    #_log.debug("loop_dt_str=(%s)" % str(loop_dt_str))
                    #_log.debug("loop_qty=(%s)" % str(loop_qty))
                    #_log.debug("loop_dt=(%s)" % str(loop_dt))
                    results_dt.append(loop_dt)
                    results_qty.append(loop_qty)
        if (len(results_dt) != len(results_qty)):
            raise Exception("mismatch, len(results_dt)=(%s), len(results_qty)=(%s)" % (str(len(results_dt)), str(len(results_qty))))
        _log.debug("len(results)=(%s)" % str(len(results_dt)))
        return [ results_dt, results_qty ]
        #   }}}


    #   About: Given a path to gpg encrypted file, decrypt file using system gpg/keychain, raise Exception if file is not decryptable, or if it doesn't exist
    def _DecryptGPGFileToString(self, arg_path_file):
    #   {{{
        _log.debug("file=(%s)" % str(os.path.basename(arg_path_file)))
        cmd_gpg_decrypt = ["gpg", "-q", "--decrypt", arg_path_file ]
        p = Popen(cmd_gpg_decrypt, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        result_data_decrypt, result_stderr = p.communicate()
        result_str = result_data_decrypt.decode()
        result_stderr = result_stderr.decode()
        rc = p.returncode
        if (rc != 0):
            raise Exception("gpg decrypt non-zero returncode=(%s), result_stderr=(%s)" % (str(rc), str(result_stderr)))
        _log.debug("lines=(%s)" % str(result_str.count("\n")))
        return result_str
    #   }}}

        
    #   About: 2021-01-03T16:29:53AEST For a given date (either as string or python datetime), return [ first, last ] 
    def _DayStartAndEnd_Minutes_FromDate(self, arg_day):
    #   {{{
        if not isinstance(arg_day, datetime.datetime):
            arg_day = dateparser.parse(arg_day)
        result_start = arg_day.replace(hour=0, minute=0, second=0, microsecond=0)
        result_end = arg_day.replace(hour=23, minute=59, second=59)
        return [ result_start, result_end ]
    #   }}}
            


#   }}}1

