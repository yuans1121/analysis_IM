#! /usr/bin/env python

import scipy as sp
import numpy as np
#from numpy.fft import *
import scipy.linalg as linalg

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

import functions

params_init = {
    'processes' : 1,
    'plot' : True,
    'saveweight' : False,
    #'hr' : ('15hr_40-41-43_','15hr_42_',),
    #'mid' : ('dirty_map_',),
    #'polarizations' : ('I',),
    #'last' : (),
    
    'imap_pair' : [],
    'nmap_pair' : [],
    'mmap_pair' : [],
    
    'input_root' : '../newmaps/',
    'output_root' : './',
    'resultf' : '',

    'cldir' : '',

    'boxshape' : (60,12,6),
    'boxunit' : 15., # in unit Mpc h-1
    'discrete' : 3,
    'Xrange' : (1400,),
    'Yrange' : (-6*15,6*15),
    'Zrange' : (0.,6*15),

    'kbinNum' : 20,
    'kmin' : -1,
    'kmax' : -1,

    'FKPweight' : False,
    'FKPpk' : 1.e-3,
    'OmegaHI' : 1.e-3,
    'Omegam' : 0.23,
    'OmegaL' : 0.74,
    'z' : 1,
}

pi = 3.1415926
deg2rad = pi/180.
prefix = 'pk_'

class PowerSpectrumMaker(object):
    """Calculate Power Spectrum"""

    def __init__(self, parameter_file_or_dict=None, feedback=2):
        # Read in the parameters.
        #params_init = dict(base_params_init)
        #params_init.update(self.params_init)
        self.params = parse_ini.parse(parameter_file_or_dict,
            params_init, prefix=prefix, feedback=feedback)

        self.feedback=feedback

        self.plot = bool(self.params['plot'])
    
    def execute(self, nprocesses=1):

        params = self.params
        out_root = params['output_root']
        resultf = functions.getresultf(params)

        OmegaHI = params['OmegaHI']
        Omegam = params['Omegam']
        OmegaL = params['OmegaL']
        fkpp = params['FKPpk']
        FKPweight = params['FKPweight']

        PK, k, PK2, k2 = self.GetPower()

        B = []
        Bk= []
        if (params['cldir']!=''):
            B = sp.load(params['cldir']+'b_bias.npy')
            Bk= sp.load(params['cldir']+'k_bias.npy')
            PK= PK*B

        shortnoise_fname = \
            params['input_root'] + resultf + '_p_combined.npy'
        try:
            shortnoise = np.load(shortnoise_fname)
            PK = PK - shortnoise
            print '\t:Subtracte shortnoise!!'
        except IOError:
            print '\t:No shortnoise found!!'

        print PK
        print

        non0 = PK.nonzero()
        #print PK.min(), PK.max()
        #print PK2
        #print PK
        #print k[non0]
        #return 0
        if params['saveweight']:
            if FKPweight:
                sp.save(out_root+resultf+'_p_fkp', PK)
                sp.save(out_root+resultf+'_k_fkp', k)
                sp.save(out_root+resultf+'_p2_fkp', PK2)
            else:
                sp.save(out_root+resultf+'_p', PK)
                sp.save(out_root+resultf+'_k', k)
                #sp.save(out_root+resultf+'_p2', PK2)


        if self.plot==True:
            print PK
            #print power_0
            plt.figure(figsize=(8,8))
            #print k
            #print PK
            plt.subplot('211')
            plt.scatter(k.take(non0), PK.take(non0))
            #plt.scatter(k_0, power_0, c='w')
            #plt.plot(power_th[0], power_th[1], c='r')
            plt.loglog()
            #plt.semilogx()
            plt.ylim(ymin=1.e-1)    
            plt.xlim(xmin=k.min(), xmax=k.max())
            plt.title('Power Spectrum')
            plt.xlabel('$k$')
            plt.ylabel('$P(k) (Kelvin^{2}(h^{-1}Mpc)^3)$')

            PK = PK*k*k*k/2./pi/pi
            #power_th[1] = power_th[1]*power_th[0]*power_th[0]*power_th[0]/2/pi/pi

            #print PK
            plt.subplot('212')
            plt.scatter(k.take(non0), PK.take(non0))
            #plt.plot(power_th[0], power_th[1], c='r')
            plt.loglog()
            #plt.semilogx()
            plt.ylim(ymin=1.e-4)    
            plt.xlim(xmin=k.min(), xmax=k.max())
            plt.xlabel('$k (h Mpc^{-1})$')
            plt.ylabel('$\Delta^2 (Kelvin^{2})$')
            #plt.show()
            if FKPweight:
                plt.savefig(out_root+resultf+'_p_fkp'+'.eps', format='eps')
            else:
                plt.savefig(out_root+resultf+'_p'+'.eps', format='eps')

    #       #PK2 = np.log10(PK2)
    #       plt.figure(figsize=(6,6))
    #       extent = (k2[0][0], k2[0][-1], k2[1][0], k2[1][-1])
    #       plt.imshow(PK2, origin='lower', extent = extent, interpolation='nearest')
    #       plt.xlabel('$k vertical (h Mpc^{-1})$')
    #       plt.ylabel('$k parallel (h Mpc^{-1})$')
    #       cb = plt.colorbar()
    #       cb.set_label('$lg(P^{2D}_{k_pk_v}) (Kelvin^2(h^{-1}Mpc)^3)$')
    #       plt.loglog()
    #       if FKPweight:
    #           plt.savefig(out_root+'power2_fkp_'+resultf+'.eps', format='eps')
    #       else:
    #           plt.savefig(out_root+'power2_'+resultf+'.eps', format='eps')

            plt.show()
            #print 'Finished @_@ '
        return PK

    def GetPower(self):
        params = self.params

        fftbox = self.GetRadioFFTbox()

        kbn = params['kbinNum']
        kmin = params['kmin']
        kmax = params['kmax']

        kunit = 2.*pi/(params['boxunit'])
        PK = np.zeros(kbn)
        if (kmin==-1) or (kmax==-1):
            k = np.logspace(
                log10(1./params['boxshape'][0]), log10(sqrt(3)), num=kbn+1)
        else:
            kmin = kmin
            kmax = kmax
            k = np.logspace(log10(kmin), log10(kmax), num=kbn+1)
        PK2 = np.zeros(shape=(10, 10))
        k2 = np.zeros(shape=(2, 10))
        #print k
        MakePower.Make(fftbox, PK, k, PK2, k2, kunit)
        k = k[:-1]
        k2 = k2*kunit

        return PK, k, PK2, k2
        
    def GetDelta(self, box, nbox, mbox):
        """
            This function is used to change intensity box to overdensity box.
            Here ,for radio maps, it do nothing.
            For optical maps, funcion is redefined in mkpower_wigglez.py
        """
        return box, nbox

    def GetRadioFFTbox(self):
        params = self.params
        #resultf = params['hr'][0]
        #if len(params['last']) != 0:
        #   resultf = resultf + params['last'][0]
        #resultf = resultf + '-' + params['hr'][1]
        #if len(params['last']) != 0:
        #   resultf = resultf + params['last'][1]

        # Make parent directory and write parameter file.
        kiyopy.utils.mkparents(params['output_root'])
        #parse_ini.write_params(params, 
        #   params['output_root']+'params.ini',prefix='pk_' )
        in_root = params['input_root']
        out_root = params['output_root']

        fkpp = params['FKPpk']
        FKPweight = params['FKPweight']
        
        #### Process ####
        imap_pair = params['imap_pair']
        nmap_pair = params['nmap_pair']
        mmap_pair = params['mmap_pair']

        box_fname  = in_root + 'fftbox/' + 'fftbox_' + imap_pair[0]
        box  = np.load(box_fname)

        nbox_fname = in_root + 'fftbox/' + 'fftbox_' + nmap_pair[0]
        nbox = np.load(nbox_fname)

        if len(params['mmap_pair'])!=0:
            mbox_fname = in_root + 'fftbox/' + 'fftbox_' + mmap_pair[0]
            mbox = np.load(mbox_fname)
            box, nbox = self.GetDelta(box, nbox, mbox)

        # Using map in different day 
        box_fname  = in_root + 'fftbox/' + 'fftbox_' + imap_pair[1]
        box2 = np.load(box_fname)

        nbox_fname = in_root + 'fftbox/' + 'fftbox_' + nmap_pair[1]
        nbox2 = np.load(nbox_fname)

        if len(params['mmap_pair'])!=0:
            mbox_fname = in_root + 'fftbox/' + 'fftbox_' + mmap_pair[1]
            mbox2 = np.load(mbox_fname)
            box2, nbox2 = self.GetDelta(box2, nbox2, mbox2)
        
        box = box*nbox
        box2 = box2*nbox2
        #box = nbox*nbox
        #box2 = nbox2*nbox2

        #normal = (nbox**2).flatten().sum()
        #normal2 = (nbox2**2).flatten().sum()
        #normal = sqrt(normal)*sqrt(normal2)
        normal = (nbox*nbox2).flatten().sum()
        #normal = sqrt((nbox**2*nbox2**2).flatten().sum())
        #print normal

        V = params['boxunit']**3

        print "PowerMaker: FFTing "
        inputa = np.zeros(params['boxshape'], dtype=complex)
        outputa = np.zeros(params['boxshape'], dtype=complex)
        fft = FFTW.Plan(inputa,outputa,direction='forward', flags=['measure'])
        inputa.imag = 0.
        inputa.real = box
        FFTW.execute(fft)

        #print outputa[10][10]

        inputb = np.zeros(params['boxshape'], dtype=complex)
        outputb = np.zeros(params['boxshape'], dtype=complex)
        fft = FFTW.Plan(inputb,outputb,direction='forward', flags=['measure'])
        inputb.imag = 0.
        inputb.real = box2
        FFTW.execute(fft)
        
        #print outputb[10][10]

        fftbox = (outputa.__mul__(outputb.conjugate())).real

        #fftbox = (outputa*(outputa.conjugate())).real
        fftbox = fftbox*V/normal #/2./pi/pi/pi

        return fftbox


if __name__ == '__main__':
    import sys
    if len(sys.argv)==2 :
        PowerSpectrumMaker(str(sys.argv[1])).execute()
    elif len(sys.argv)>2 :
        print 'Maximun one argument, a parameter file name.'
    else :
        PowerSpectrumMaker().execute()
