#! /usr/bin/env python
'''
    This module is used to calculate the bias(Transfer Function)
    caused by the mode subtraction. 

    The bias is defined as the ratio of the power spectrum 
    between the simulation maps with and without mode subtraction.

'''

import scipy as sp
import numpy as np
#from numpy.fft import *
import scipy.linalg as linalg

import os

from core import algebra, hist
from kiyopy import parse_ini
import kiyopy.utils
import kiyopy.custom_exceptions as ce
from scipy import integrate
from math import *
from sys import *
import MakePower
import matplotlib.pyplot as plt
import fftw3 as FFTW
from scipy.interpolate import interp1d
from scipy.optimize import leastsq
from mpi4py import MPI

import functions

params_init = {
    'processes' : 1,
    'plot' : True,
    'input_root' : '../newmaps/',
    'resultf' : '',
    'resultf0' : '',
    'output_root' : './',

    'simmap_root' : './',

    'kbinNum' : 20,
    'kmin' : None,
    'kmax' : None,

    'FKPweight' : False,

    'OmegaHI' : 1.e-3,
    'Omegam' : 0.23,
    'OmegaL' : 0.74,
    'z' : 1,
    'PKunit' : 'K',
    'cross' : False,
}

pi = 3.1415926
deg2rad = pi/180.
prefix = 'bc_'

class BiasCalibrate(object):
    """Calculate Power Spectrum"""

    def __init__(self, parameter_file_or_dict=None, feedback=2):
        # Read in the parameters.
        self.params = parse_ini.parse(parameter_file_or_dict,
            params_init, prefix=prefix, feedback=feedback)

        self.feedback=feedback

        self.plot = bool(self.params['plot'])

    def mpiexecute(self, nprocesses=1):
        
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()

        comm.barrier()

        if rank == 0:
            self.execute()
            for i in range(1, size):
                comm.recv(source=i, tag=11)
        else:
            comm.ssend(1, dest=0, tag=11)

        comm.barrier()
    
    def execute(self, nprocesses=1):

        params = self.params
        out_root = params['output_root']
        in_root = params['input_root']
        resultf = functions.getresultf(params)
        resultf0= params['resultf0']

        FKPweight = params['FKPweight']

        # Read the Power Spectrum Result
        # clean_{map+sim}(map+sim)
        k1 = sp.load(in_root + resultf + '_k_combined.npy')
        if FKPweight:
            pk1 = sp.load(in_root + resultf + '_p_fkp_combined.npy')
            pk12= sp.load(in_root + resultf + '_p2_fkp_combined.npy')
        else:
            pk1 = sp.load(in_root + resultf + '_p_combined.npy')
            pk12= sp.load(in_root + resultf + '_p2_combined.npy')

        #non0 = pk1.nonzero()
        #pk1 = pk1.take(non0)[0]
        #k1 = k1.take(non0)[0]
        # clean_{map}(map)
        if resultf0 != '':
            if params['cross']:
                k0 = sp.load(in_root + resultf0 + '_k.npy')
                if FKPweight:
                    pk0 = sp.load(in_root + resultf0 + '_p_fkp.npy')
                    pk02= sp.load(in_root + resultf0 + '_p2_fkp.npy')
                else:
                    pk0 = sp.load(in_root + resultf0 + '_p.npy')
                    pk02= sp.load(in_root + resultf0 + '_p2.npy')
            else:
                k0 = sp.load(in_root + resultf0 + '_k_combined.npy')
                if FKPweight:
                    pk0 = sp.load(in_root + resultf0 + '_p_fkp_combined.npy')
                    pk02= sp.load(in_root + resultf0 + '_p2_fkp_combined.npy')
                else:
                    pk0 = sp.load(in_root + resultf0 + '_p_combined.npy')
                    pk02= sp.load(in_root + resultf0 + '_p2_combined.npy')
        else:
            k0  = k1
            pk0 = np.zeros(pk1.shape)
            pk02=np.zeros(pk12.shape)

        #pk0 = pk0.take(non0)[0]
        #k0 = k0.take(non0)[0]

        # Read the Pwer Spectrum without mode subtraction
        simmap_root = params['simmap_root']
        k  = sp.load(simmap_root + 'simmaps_k_combined.npy')
        pk = sp.load(simmap_root + 'simmaps_p_combined.npy')
        pk2= sp.load(simmap_root + 'simmaps_p2_combined.npy')

        if os.path.exists(simmap_root + 'simmaps_beam_k_combined.npy'):
            k_beam  = sp.load(simmap_root + 'simmaps_beam_k_combined.npy')
            pk_beam = sp.load(simmap_root + 'simmaps_beam_p_combined.npy')
            pk2_beam= sp.load(simmap_root + 'simmaps_beam_p2_combined.npy')

            if (k_beam-k0).any() or (k_beam-k1).any() or (k_beam-k).any():
                print "k_beam and k0 are not match!!"
                return 0

            dpk = pk1-pk0
            #dpk[dpk<=0] = np.inf
            #pk_beam[pk_beam<=0] = np.inf
            dpk[dpk==0] = np.inf
            pk_beam[pk_beam==0] = np.inf
            dpk_beam = pk/pk_beam
            pk_beam[pk_beam==np.inf] = 0.
            dpk_lose = pk_beam/dpk
            dpk = dpk_beam*dpk_lose

            dpk2= (pk12-pk02)
            #dpk2[dpk2<=0] = np.inf
            #pk2_beam[pk2_beam<=0] = np.inf
            dpk2[dpk2==0] = np.inf
            pk2_beam[pk2_beam==0] = np.inf
            dpk2_beam = pk2/pk2_beam
            pk2_beam[pk2_beam==np.inf] = 0.
            dpk2_lose = pk2_beam/dpk2
            dpk2= dpk2_beam*dpk2_lose

            sp.save(out_root + 'k_beam_bias', k_beam)
            sp.save(out_root + 'b_beam_bias', dpk_beam)
            sp.save(out_root + 'b2_beam_bias', dpk2_beam)

            sp.save(out_root + 'k_lose_bias', k_beam)
            sp.save(out_root + 'b_lose_bias', dpk_lose)
            sp.save(out_root + 'b2_lose_bias', dpk2_lose)
        else:
            # Test if k and k0 are match
            if (k-k0).any() or (k-k1).any():
                print "k and k0 are not match!!"
                return 0

            dpk = pk1-pk0
            dpk[dpk<=0] = np.inf
            dpk = pk/dpk

            dpk2= (pk12-pk02)
            dpk2[dpk2<=0] = np.inf
            dpk2= pk2/dpk2

        #if params['cross']:
        #    dpk = np.sqrt(dpk)
        #    dpk2 = np.sqrt(dpk2)

        sp.save(out_root + 'k_bias', k)
        sp.save(out_root + 'b_bias', dpk)
        sp.save(out_root + 'b2_bias', dpk2)

if __name__ == '__main__':
    import sys
    if len(sys.argv)==2 :
        BiasCalibrate(str(sys.argv[1])).execute()
    elif len(sys.argv)>2 :
        print 'Maximun one argument, a parameter file name.'
    else :
        BiasCalibrate().execute()
