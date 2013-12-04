#! /usr/bin/env python
"""
    This module used to convert the maps into fftbox

    ----  Jun 28, 2012. Y.-CH. LI  ----
    add blackman window

    ----  Jun 18, 2012. Y.-CH. LI  ----
    add tabs_list, which is used to label different maps with the same name. 

    ----  Jan 15, 2012. Y.-CH. LI  ----
    use 'imap_root', 'nmap_root' and 'mmap_root' instead of 'input_root'
    in order to use maps located in different directions

    ----  Jan 08, 2012. Y.-CH. LI  ----
    Modified the name system
    use 'imap_list', 'nmap_list' and 'mmap_list' instead of 'hr'+'mid'+'last'

    add key word 'submean'
        if   'submean'==True:  it will subtracte the mean value of the maps
        else 'submean'==False: it will not.
    default value is False. 
    For some simulation maps, This process is needed.
    
    ----  Dec 11, 2011. Y.-CH. LI  ----
    If the intensity map is already overdensity, the parameter 'mid' 
    should have two elements:
        middle part for intensity map name, and 
        middle part for inverse noise map name.
    The inverse noise map will be the weight for power spectrum estimation.

    If the intensity map is not the overdensity, the parameter 'mid'
    should have three elements:
        middle part for intensity map name, 
        middle part for inverse noise map name(or selection function), and
        middle part for mock map name.
    

        
    
"""
import os
import ctypes
import scipy as sp
import numpy as np
from numpy.fft import *
import scipy.linalg as linalg
import multiprocessing as mp
import random

from core import algebra, hist
from kiyopy import parse_ini
import kiyopy.utils
import kiyopy.custom_exceptions as ce
from scipy import integrate
from math import *
from sys import *
import matplotlib.pyplot as plt
import MakePower
from utils import fftutil
from mpi4py import MPI

# public functions are defined in this module
import functions

pi = 3.1415926
deg2rad = pi/180.

params_init = {
    'processes' : 1,
    'plot' : True,

    'imap_root' : [],
    'nmap_root' : [],
    'mmap_root' : [],

    'imap_list' : [],
    'nmap_list' : [],
    'mmap_list' : [],
    'tabs_list' : [],

    'half' : None,
    #'half' : 'lower', 
    #'half' : 'upper', 

    'submean' : False,

    'output_root' : './',

    'window' : '',

    'map_multiplier' : 1.,

    'boxshape' : (60,12,6),
    'boxunit' : 15., # in unit Mpc h-1
    'discrete' : 3.,
    'Xrange' : None,
    'Yrange' : None,
    'Zrange' : None,

    'cutlist': [],
}
prefix = 'pre_'

class Prepare(object):
    """Remove the Big Peak in the map"""

    def __init__(self, parameter_file_or_dict=None, feedback=2):
        # Read in the parameters.
        self.params = parse_ini.parse(
            parameter_file_or_dict, params_init, prefix=prefix)

        self.feedback=feedback

        self.plot = bool(self.params['plot'])

        params = self.params

        if not params['Xrange']:
            map_tmp = algebra.load(params['imap_root'][0] + params['imap_list'][0])
            map_tmp = algebra.make_vect(map_tmp)
            if params['half'] != None:
                map_tmp = functions.getmap_halfz(map_tmp, params['half'])
            rangex, rangey, rangez = functions.getedge(map_tmp)
            self.params['boxunit'] = max((rangex[1]-rangex[0])/params['boxshape'][0],
                                         (rangey[1]-rangey[0])/params['boxshape'][1],
                                         (rangez[1]-rangez[0])/params['boxshape'][2])
            rangexc = (rangex[1]-rangex[0])/2.+rangex[0]
            rangeyc = (rangey[1]-rangey[0])/2.+rangey[0]
            rangezc = (rangez[1]-rangez[0])/2.+rangez[0]
            rangexh = floor(self.params['boxunit']*params['boxshape'][0]/2.) + 1.
            rangeyh = floor(self.params['boxunit']*params['boxshape'][1]/2.) + 1.
            rangezh = floor(self.params['boxunit']*params['boxshape'][2]/2.) + 1.
            self.params['Xrange'] = (rangexc-rangexh, rangexc+rangexh)
            self.params['Yrange'] = (rangeyc-rangeyh, rangeyc+rangeyh)
            self.params['Zrange'] = (rangezc-rangezh, rangezc+rangezh)
            params = self.params
            print 'X : [%f, %f]'%self.params['Xrange']
            print 'Y : [%f, %f]'%self.params['Yrange']
            print 'Z : [%f, %f]'%self.params['Zrange']
            print 'Box Unit: %f'%self.params['boxunit']


    def mpiexecute(self, nprocesses=1):
        
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()

        params = self.params

        n_map = len(params['imap_list'])

        if rank==0:
            out_root = params['output_root']
            # Make parent directory and write parameter file.
            kiyopy.utils.mkparents(out_root)

            # make directions for fftbox saving
            if not os.path.exists(out_root+'fftbox/'):
                os.mkdir(out_root+'fftbox/')
            f = open(out_root+'fftbox/box.info', 'w')
            print >> f, 'Box Unit: %f'%self.params['boxunit']
            print >> f, 'X : [%f, %f]'%self.params['Xrange']
            print >> f, 'Y : [%f, %f]'%self.params['Yrange']
            print >> f, 'Z : [%f, %f]'%self.params['Zrange']
            f.close()

        comm.barrier()

        if rank<n_map:
            self.params['imap_list'] = self.params['imap_list'][rank::size]
            self.params['imap_root'] = self.params['imap_root'][rank::size]
            self.params['nmap_list'] = self.params['nmap_list'][rank::size]
            self.params['nmap_root'] = self.params['nmap_root'][rank::size]
            if len(self.params['mmap_list'])!=0:
                self.params['mmap_list'] = self.params['mmap_list'][rank::size]
                self.params['mmap_root'] = self.params['mmap_root'][rank::size]
            if len(self.params['tabs_list'])!=0:
                self.params['tabs_list'] = self.params['tabs_list'][rank::size]
            finish = self.execute()
            print "RANK %d : Job finished"

        comm.barrier()
    
    def execute(self, nprocesses=1):
        params = self.params


        imap_list = params['imap_list']
        nmap_list = params['nmap_list']
        mmap_list = params['mmap_list']

        n_processes = params['processes']
        out_root = params['output_root']

        # Make parent directory and write parameter file.
        kiyopy.utils.mkparents(out_root)

        # make directions for fftbox saving
        if not os.path.exists(out_root+'fftbox/'):
            os.mkdir(out_root+'fftbox/')

        #### Process ####
        n_new = n_processes -1
        n_map = len(imap_list)
        print "%d maps need to be prepare"%n_map

        if n_new <=0:
            for ii in range(len(params['imap_list'])):
                imap_fname = imap_list[ii]
                nmap_fname = nmap_list[ii]
                if len(mmap_list)!=0:
                    mock_fname = mmap_list[ii]
                    self.process_map(ii, imap_fname, nmap_fname, mmap_fname)
                else:
                    self.process_map(ii, imap_fname, nmap_fname)
        elif n_new >32:
            raise ValueError("Processes limit is 32")
        else: 
            process_list = range(n_new)
            for ii in xrange(n_map + n_new):
                if ii >= n_new:
                    process_list[ii%n_new].join()
                    if process_list[ii%n_new].exitcode != 0:
                        raise RuntimeError("A thred faild with exit code"
                            + str(process_list[ii%n_new].exitcode))
                if ii < n_map:
                    imap_fname = imap_list[ii]
                    nmap_fname = nmap_list[ii]
                    #end = pol_str
                    #if len(last)!=0:
                    #   end = end + last[ii]
                    #imap_fname = hr[ii] + mid[0] + end + '.npy'
                    #nmap_fname = hr[ii] + mid[1] + end + '.npy'

                    # prepare the mock maps for optical 
                    #if len(mid)==3:
                    if len(mmap_list)!=0:
                        mock_fname = mmap_list[ii]
                        process_list[ii%n_new] = mp.Process(
                            target=self.process_map, 
                            args=(ii, imap_fname, nmap_fname, mock_fname))
                    else:
                        process_list[ii%n_new] = mp.Process(
                            target=self.process_map, 
                            args=(ii, imap_fname, nmap_fname))
                    process_list[ii%n_new].start()
        return 0

    def process_map(self, index, imap_fname, nmap_fname, mock_fname=None):
        params = self.params
        out_root = params['output_root']

        imap_froot = params['imap_root'][index]
        nmap_froot = params['nmap_root'][index]

        window = params['window']
        
        if mock_fname != None:
            mmap_froot = params['mmap_root'][index]
            imap, nmap, mmap = functions.getmap(
                imap_froot + imap_fname, 
                nmap_froot + nmap_fname,
                mmap_froot + mock_fname, 
                params['half'])

            print "Map multiply %f" %params['map_multiplier']
            imap = imap*params['map_multiplier']

            if window != '':
                window_function = fftutil.window_nd(nmap.shape, name=window)
                nmap *= window_function

            box, nbox, mbox = functions.fill(params, imap, nmap, mmap)
            #print mmap.flatten().mean()
            #print nmap.flatten().max()
            #print box.flatten().max()

            ## get the overdencity
            #alpha = box.flatten().sum()/mbox.flatten().sum()
            #print alpha
            #box = box - alpha*mbox
            #box[nbox!=0] = box[nbox!=0]/nbox[nbox!=0]

            ## get the fkp weight
            #nbox = nbox/(1.+nbox*1000)

            if len(params['tabs_list']) != 0:
                pkrm_mfname = out_root + 'fftbox/' + 'fftbox_'\
                    + params['tabs_list'][index] +  mock_fname 
            else:
                pkrm_mfname = out_root + 'fftbox/' + 'fftbox_'\
                    +  mock_fname
            np.save(pkrm_mfname, mbox)
            #algebra.save(pkrm_nfname, mbox)
        else:
            #box, nbox = self.fill(imap, nmap)
            imap, nmap = functions.getmap(
                imap_froot + imap_fname,
                nmap_froot + nmap_fname,
                half = params['half'])

            print "Map multiply %f" %params['map_multiplier']
            imap = imap*params['map_multiplier']

            # multiply the window 
            if window != '':
                window_function = fftutil.window_nd(nmap.shape, name=window)
                nmap *= window_function

            # subtract the mean value of the imaps
            if params['submean']==True:
                print "Note: Subtracted mean: ",imap.flatten().mean()
                imap = imap - imap.flatten().mean()

            # cut off some bad frequencies. 
            if len(params['cutlist'])!=0:
                print '\t:Bad frequencies cutting off'
                nmap[params['cutlist']]=0

            box , nbox = functions.fill(params, imap, nmap)

            #nbox = nbox/(1.+3.e3*nbox)
            #nbox = nbox/(1.+7.e-5*nbox)

        if len(params['tabs_list']) != 0:
            pkrm_fname = out_root + 'fftbox/' + 'fftbox_'\
                + params['tabs_list'][index] + imap_fname
            np.save(pkrm_fname, box)
            #algebra.save(pkrm_fname, box)

            pkrm_nfname = out_root + 'fftbox/' + 'fftbox_'\
                + params['tabs_list'][index] + nmap_fname
            np.save(pkrm_nfname, nbox)
            #algebra.save(pkrm_nfname, nbox)
        else:
            pkrm_fname = out_root + 'fftbox/' + 'fftbox_'\
                + imap_fname
            np.save(pkrm_fname, box)
            #algebra.save(pkrm_fname, box)

            pkrm_nfname = out_root + 'fftbox/' + 'fftbox_'\
                + nmap_fname
            np.save(pkrm_nfname, nbox)
            #algebra.save(pkrm_nfname, nbox)

#       print mmap.shape

#       print 'Removing Peak... Map:' + hr_str[:-1]
#       self.pkrm(imap,nmap,
#           out_root+'pkrm'+hr_str+'dirty_map_'+pol_str+'.png', threshold=2.5)

        #print imap.flatten().max()
        #print imap.flatten().min()
        #print box.flatten().max()
        #print box.flatten().min()


    def pkrm(self, imap, nmap, fname, threshold=2.0):
        freq = imap.get_axis('freq')/1.e6
        if self.plot==True:
            plt.figure(figsize=(8,8))
            plt.subplot(211)
            plt.title('Map with peak remove')
            plt.xlabel('Frequece (MHz)')
            plt.ylabel('$\Delta$ T(Kelvin) Without Foreground')
            #for i in range(13,14):
            #   for j in range(25, 26):
            for i in range(0,imap.shape[2]):
                for j in range(0, imap.shape[1]):
                    plt.plot(freq, imap.swapaxes(0,2)[i][j])

        dsigma = 50
        while(dsigma>0.01):
            sigma = imap.std(0)
            for i in range(0, imap.shape[0]):
                good = [np.fabs(imap[i]).__lt__(threshold*sigma)]
                choicelist = [imap[i]]
                imap[i] = np.select(good, choicelist)
                choicelist = [nmap[i]]
                nmap[i] = np.select(good, choicelist)
            dsigma = (sigma.__sub__(imap.std(0))).max()
            #print dsigma
        #print '\n'

        if self.plot==True:
            plt.subplot(212)
            plt.xlabel('Frequece (MHz)')
            plt.ylabel('$\Delta$ T(Kelvin) Without Foreground')
            #for i in range(13,14):
            #   for j in range(25, 26):
            for i in range(0,imap.shape[2]):
                for j in range(0, imap.shape[1]):
                    plt.plot(freq, imap.swapaxes(0,2)[i][j])

            plt.savefig(fname, format='png')
            plt.show()
            #plt.ylim(-0.0001,0.0001)


if __name__ == '__main__':
    import sys
    if len(sys.argv)==2 :
        Prepare(str(sys.argv[1])).execute()
    elif len(sys.argv)>2 :
        print 'Maximun one argument, a parameter file name.'
    else :
        Prepare().execute()