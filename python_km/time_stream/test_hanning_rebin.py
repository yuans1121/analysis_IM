"""Unit tests for hanning a rebin_freq modules."""

import unittest
import copy

import scipy as sp
import numpy.ma as ma

import sys

import hanning
import rebin_freq
import core.data_block
import core.fitsGBT

test_file = 'testfile_GBTfits.fits'

class TestFunctions(unittest.TestCase) :
    """Since these operations actually changes the data, these are only sanity
    tests, far from thorough."""
    
    def setUp(self) :
        Reader = core.fitsGBT.Reader(test_file, feedback=0)
        self.Data = Reader.read(1,1)
        self.Data.verify()
        self.Data_copy = copy.deepcopy(self.Data)

    def test_hanning_data_changed(self) :
        """Copy the data, see that we did something."""
        hanning.hanning_smooth(self.Data)
        # For lack of anything better to test:
        self.Data.verify()
        # Make sure we actually did something.
        self.assertTrue(not ma.allclose(self.Data.data, self.Data_copy.data))
        # Make sure we didn't change other fields, like LST.
        self.assertTrue(sp.allclose(self.Data.field['LST'],
                        self.Data_copy.field['LST']))

    def test_hanning_cases(self) :
        data = self.Data.data
        data[:,:,:,:] = 1.
        data[5,2,1,631] = 4.
        data[7,3,1,853] = ma.masked
        hanning.hanning_smooth(self.Data)
        self.assertTrue(data[7,3,1,853] is ma.masked)
        self.assertTrue(data[7,3,1,852] is ma.masked)
        self.assertTrue(data[7,3,1,854] is ma.masked)
        self.assertAlmostEqual(data[5,2,1,631], 2.5)
        self.assertAlmostEqual(data[5,2,1,630], 1.75)
        self.assertAlmostEqual(data[5,2,1,632], 1.75)

    
    # TODO For Hanning:
    # Could test that end pointes end up masked.  Could test that points
    # adjacent to masked data end up masked.
    
    def test_rebin_runs(self) :
        rebin_freq.rebin(self.Data, 1.0)
        self.Data.verify()
        self.assertAlmostEqual(-1.0, self.Data.field['CDELT1']/1.0e6)

    def test_rebin_get_freqs_right(self) :
        """Make sure that the frequencies calculated by the rebinner are
        consistant with the ones calculated by calc_freq()."""
        rebin_freq.rebin(self.Data, 2.0)
        old_freq = sp.array(self.Data.freq)
        self.Data.calc_freq()
        self.assertTrue(sp.allclose(old_freq, self.Data.freq))
        self.Data.verify()
        self.assertEqual(self.Data.dims[-1], len(self.Data.freq))

    def test_end_freqs(self) :
        self.Data.calc_freq()
        old_top = self.Data.freq[-1]
        old_bot = self.Data.freq[0]
        rebin_freq.rebin(self.Data, 0.9)
        self.assertAlmostEqual(old_top, self.Data.freq[-1], places=-7)
        self.assertAlmostEqual(old_bot, self.Data.freq[0], places=-7)

    def test_rebins_data_right(self) :
        """set all data to 0 except 1 entry, figure out the f, rebin and
        check that only the closest new f is non-zero."""
        self.Data.data[:,:,:,:] = 0
        self.Data.data[5,2,0,324] = 1
        self.Data.calc_freq()
        oldf = self.Data.freq[324]
        rebin_freq.rebin(self.Data, 2.0, mean=True)
        new_ind = (abs(self.Data.freq - oldf)).argmin()
        self.assertNotAlmostEqual(0, self.Data.data[5,2,0,new_ind])
        self.Data.data[5,2,0,new_ind] = 0.0
        self.assertTrue(sp.allclose(self.Data.data, 0.0))

    def tearDown(self) :
        del self.Data
        del self.Data_copy


if __name__ == '__main__' :
    unittest.main()
