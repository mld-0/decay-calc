#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=3: 
#   }}}1
#   {{{3
import operator
import shutil
import logging
import argparse
import subprocess
import io
import os
import argcomplete
import inspect
import sys
import os
import importlib
import importlib.resources
import math
import csv
import time
import glob
import platform
import inspect
import re
import time
import pytz
import pprint
import textwrap
import dateutil.parser
import dateutil.tz
import dateutil.relativedelta 
import time
import tempfile
import logging
from subprocess import Popen, PIPE, STDOUT
from os.path import expanduser
from pathlib import Path
from datetime import datetime, timedelta, date
from subprocess import Popen, PIPE, STDOUT
from io import StringIO
from tzlocal import get_localzone
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import pandas
import dateparser
#   }}}1
#   {{{2
_log = logging.getLogger('decaycalc')
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(level=logging.DEBUG, format=_logging_format, datefmt=_logging_datetime)

class DecayCalc(object):

    #   Given <arguments>, (call methods to) get lists of data from file(s) in arg_data_dir, and return list of calculated qtys remaining for each datetime in arg_dt_list 
    def CalculateFromFilesRange_Monthly(self, arg_dt_list, arg_data_dir, arg_halflife, arg_onset, arg_file_prefix, arg_file_postfix):
        pass
    
    #   About: Given (sorted list of datetimes) arg_dt_items, and corresponding list arg_qty_items, (assuming expodential decay of arg_halflife and linear onset of arg_onset), find the qty remaining at each datetime in arg_dt_list 
    def Calculate(self, arg_dt_list, arg_dt_items, arg_qty_items, arg_halflife, arg_onset):
        pass

    #   About: Get a list of the files in arg_data_dir, where each file is of the format 'arg_file_prefix + date_str + arg_file_postfix', and date_str is %Y-%m for each year and month between one month before arg_dt_first, and arg_dt_last
    def _GetFiles_Monthly(self, arg_data_dir, arg_file_prefix, arg_file_postfix, arg_dt_first, arg_dt_last):
    #   {{{
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


                    #   Continue: 2021-01-02T19:17:24AEST decaycalc, parsing of ()-() 'DTS' format datetimes, transform to iso (parseable) format
                    #loop_dt_str = loop_dt_str.replace(")-(", " ")
                    #loop_dt_str = loop_dt_str.replace("(", "")
                    #loop_dt_str = loop_dt_str.replace(")", "")

                    _log.debug("loop_dt_str=(%s)" % str(loop_dt_str))
                    loop_dt = dateparser.parse(loop_dt_str)

                    _log.debug("loop_qty=(%s)" % str(loop_qty))
                    _log.debug("loop_dt=(%s)" % str(loop_dt))

                    results_dt.append(loop_dt)
                    results_qty.append(loop_qty)
        if (len(results_dt) != len(results_qty)):
            raise Exception("mismatch, len(results_dt)=(%s), len(results_qty)=(%s)" % (str(len(results_dt)), str(len(results_qty))))
        _log.debug("len(results)=(%s)" % str(len(results_dt)))
        return [ results_dt, results_qty ]


    #   About: Given a path to gpg encrypted file, decrypt file using system gpg/keychain, raise Exception if file is not decryptable, or if it doesn't exist
    def _DecryptGPGFileToString(self, arg_path_file):
    #   {{{
        _log.debug("arg_path_file:\n%s" % str(arg_path_file))
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


#   }}}1

