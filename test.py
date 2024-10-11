"""Test file for the library."""

from pyStromligning import Stromligning

LAT = 56.46185623639339
LON = 10.866395953404707

strom = Stromligning(LAT, LON)
companies = strom.get_companies()

print(strom)
