import ctypes
import os
import sys

try:
    FDP_DLL_FNAME = {"darwin": "libFDP.dylib"}[sys.platform]
    FDP_DLL_FPATH = os.path.join(os.path.dirname(__file__), FDP_DLL_FNAME)
    FDP_DLL_HANDLE = ctypes.CDLL(FDP_DLL_FPATH)
except KeyError:
    raise Exception("PyFDP: Unsupported platform: '{}'".format(sys.platform))
except OSError:
    raise Exception("PyFDP: FDP shared library not found: '{}'".format(FDP_DLL_FPATH))
