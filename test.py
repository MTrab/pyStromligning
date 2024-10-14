"""Test file for the library."""

from pystromligning import Stromligning

LAT = 56.46185623639339
LON = 10.866395953404707

strom = Stromligning()
strom.set_location(LAT, LON)
strom.set_company("norlys_flexel")
strom.update()

print(strom)
