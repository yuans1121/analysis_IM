#!/usr/bin/python
"""Module that put data in units of cal temperture and subtracts median."""

import scipy as sp
import numpy.ma as ma

import kiyopy.custom_exceptions as ce
import base_single


class CalScale(base_single.BaseSingle) :
    """Pipeline module that performs scales data by the cal on the data.
    
    See the main funciton of this module: cal_scale.scale_by_cal for a detailed
    doc string.
    """

    prefix = 'cs_'
    params_init = {
                   'scale_time_average' : True,
                   'scale_freq_average' : False,
                   'subtract_time_median' : False
                   }

    def action(self, Data):
        scale_by_cal(Data, self.params['scale_time_average'],
                     self.params['scale_freq_average'], 
                     self.params['subtract_time_median'])
        Data.add_history('Converted to units of noise cal temperture.')
        return Data


def scale_by_cal(Data, scale_t_ave=True, scale_f_ave=False, sub_med=False) :
    """Puts all data in units of the cal temperature.
    
    Data is put into units of the cal temperature, thus removing dependance on
    the gain.  This can be done by deviding by the time average of the cal
    (scale_t_ave=True, Default) thus removing dependance on the frequency
    dependant gain.  Alternatively, you can scale by the frequency average to
    remove the time dependant gain (scale_f_ave=True). Data is then in units of 
    the frequency averaged cal temperture. You can also do both (reccomended).
    After some scaling the data ends up in units of the cal temperture as a
    funciton of frequency.

    Optionally you can also subtract the time average of the data off here
    (subtract_time_median), since you might be done with the cal information at
    this point.
    """
    
    # Here we check the polarizations and cal indicies
    xx_ind = 0
    yy_ind = 3
    xy_inds = [1,2]
    if (Data.field['CRVAL4'][xx_ind] != -5 or
        Data.field['CRVAL4'][yy_ind] != -6 or
        Data.field['CRVAL4'][xy_inds[0]] != -7 or
        Data.field['CRVAL4'][xy_inds[1]] != -8) :
            raise ce.DataError('Polarization types not as expected.')
    on_ind = 0
    off_ind = 1
    if (Data.field['CAL'][on_ind] != 'T' or
        Data.field['CAL'][off_ind] != 'F') :
            raise ce.DataError('Cal states not in expected order.')
    
    # A bunch of calculations used to test phase closure.  Not acctually
    # relevant to what is being done here.
    #a = (Data.data[5, xy_inds, on_ind, 15:20]
    #     - Data.data[5, xy_inds, off_ind, 15:20])
    #a /= sp.sqrt( Data.data[5, xx_ind, on_ind, 15:20] 
    #              - Data.data[5, xx_ind, off_ind, 15:20])
    #a /= sp.sqrt( Data.data[5, yy_ind, on_ind, 15:20] 
    #              - Data.data[5, yy_ind, off_ind, 15:20])
    #print a[0,:]**2 + a[1,:]**2
    
    diff_xx = Data.data[:,xx_ind,on_ind,:] - Data.data[:,xx_ind,off_ind,:]
    diff_yy = Data.data[:,yy_ind,on_ind,:] - Data.data[:,yy_ind,off_ind,:]
    
    if scale_t_ave :
        # Find the cal medians (in time) and scale by them.
        cal_tmed_xx = ma.median(diff_xx, 0)
        Data.data[:,xx_ind,:,:] /= cal_tmed_xx
        cal_tmed_yy = ma.median(diff_yy, 0)
        Data.data[:,yy_ind,:,:] /= cal_tmed_yy
        Data.data[:,xy_inds,:,:] /= ma.sqrt(cal_tmed_yy*cal_tmed_xx)
    
    if scale_f_ave :
        # The frequency gains have have systematic structure to them, they are
        # not by any approximation gaussian distributed.  Use means, not
        # medians across frequency.
        # Unless we have already scaled by the time average, which would take
        # out all the frequency structure.
        if scale_t_ave :
            operation = ma.median
        else :
            operation = ma.mean
        cal_fmea_xx = operation(diff_xx, -1)
        ntime = len(cal_fmea_xx)
        cal_fmea_xx.shape = (ntime, 1, 1)
        Data.data[:,xx_ind,:,:] /= cal_fmea_xx
        cal_fmea_yy = operation(diff_yy, -1)
        cal_fmea_yy.shape = (ntime, 1, 1)
        Data.data[:,yy_ind,:,:] /= cal_fmea_yy
        cal_fmea_xx.shape = (ntime, 1, 1, 1)
        cal_fmea_yy.shape = (ntime, 1, 1, 1)
        Data.data[:,xy_inds,:,:] /= ma.sqrt(cal_fmea_yy*cal_fmea_xx)

    if scale_f_ave and scale_t_ave :
        # We have devided out t_cal twice so we need to put one factor back in.
        cal_xx = ma.median(cal_tmed_xx)
        cal_yy = ma.median(cal_tmed_yy)
        Data.data[:,xx_ind,:,:] *= cal_xx
        Data.data[:,yy_ind,:,:] *= cal_yy
        Data.data[:,xy_inds,:,:] *= ma.sqrt(cal_yy*cal_xx)

    # Subtract the time median if desired.
    if sub_med :
        Data.data -= ma.median(Data.data, 0)

# If this file is run from the command line, execute the main function.
if __name__ == "__main__":
    import sys
    CalScale(str(sys.argv[1])).execute()
