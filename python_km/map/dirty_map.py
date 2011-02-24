"""Make a dirty map (and noise matrix) from data.

Loops over polarizations and only consideres only the 0th cal state (if you
want something else, change it in the time stream).
"""

import copy

import scipy as sp
import numpy.ma as ma
import numpy.linalg as linalg

from kiyopy import parse_ini
import kiyopy.utils
import kiyopy.custom_exceptions as ce
from core import utils, data_block, fitsGBT, data_map, fits_map, algebra
import tools

prefix = 'dm_'
# Parameters prefixed with 'dm_' when read from file.
params_init = {
               # IO:
               'input_root' : './',
               # The unique part of every fname
               'file_middles' : ("testfile_GBTfits",),
               'input_end' : ".fits",
               'output_root' : "./testoutput_",
               # What data to process within each file.
               'scans' : (),
               'IFs' : (0,),
               # Map parameters (Ra (deg), Dec (deg)).
               'field_centre' : (325.0, 0.0),
               # In pixels.
               'map_shape' : (5, 5),
               'pixel_spacing' : 0.5, # degrees
               # What noise model to use.  Options are:
               #  'grid' : just grid the data and devid by number of counts.
               #  'diag_file' : measure the time varience of each file.
               #  'disjoint_scans' : treat each scan as highly correlated
               #                     internally but uncorrelated between scans.
               # 'diag*' and 'grid' produce a noise file in the same format as
               # the map. 'disjoint_scans' produces a full noise covarience
               # (n_pix^2 numbers), each polarization in its onwn file.
               'noise_model' : 'grid'
               }

class DirtyMap(object) :
    """Converts time stream data into a dirty map.
    
    This module reads in multiple time stream files and turns them into a 
    (dirty) map. There are several options for how the noise is treated.
    'grid' and 'diag_file' both assume diagonal noise, while 'disjoint_scans'
    assumes that data entries can only be compared within a scan.
    
    This last one uses a full N^2 covarience matrix which requires a rather
    large amount of memory. It is not reccomended that you run this on one
    anything but the smallest map sizes, unless you have several Gigs of RAM.
    This is meant to be run on machines with > 24 GB of RAM.

    The net result is noise wieghted map, aka the dirty map.  The equivalend
    algebraic operation is. P^T N^(-1) d.  The map inverse noise matrix is 
    also produced: C_n^(-1) = P^T N^(-1) P.
    """
   
    def __init__(self, parameter_file_or_dict=None, feedback=2) :
        # Read in the parameters.
        self.params = parse_ini.parse(parameter_file_or_dict, params_init, 
                                 prefix='mm_')
        self.feedback = feedback

    def execute(self, nprocesses=1) :
        """Function that acctually does the work.

        The nprocesses parameter does not do anything yet.  It is just there
        for compatibility with the pipeline manager.
        """
        params = self.params
        kiyopy.utils.mkparents(params['output_root'])
        parse_ini.write_params(params, params['output_root'] + 'params.ini',
                               prefix='mm_')
        # Rename some commonly used parameters.
        map_shape = params['map_shape']
        spacing = params['pixel_spacing']
        algorithm = params['noise_model']
        ra_spacing = -spacing/sp.cos(params['field_centre'][1]*sp.pi/180.)
        if not algorithm in ('grid', 'diag_file', 'disjoint_scans') :
            raise ValueError('Invalid noise model: ' + algorithm)
        if len(params['IFs']) != 1 :
            raise ce.FileParameterTypeError('Can only process a single IF.')

        # Set up to iterate over the pol states.
        npol = 2 # This will be reset when we read the first data block.
        pol_ind = 0

        while pol_ind < npol :
            # Flag for the first block processed (will allowcate memory on the 
            # first iteration).
            first_block = True
            # Loop over the files to process.
            for file_middle in params['file_middles'] :
                input_fname = (params['input_root'] + file_middle +
                               params['input_end'])
                # Read in the data, and loop over data blocks.
                Reader = fitsGBT.Reader(input_fname)
                Blocks = Reader.read(params['scans'], params['IFs'])
                
                # Calculate the time varience at each frequency.  This will be
                # used as weights in most algorithms.
                if not algorithm == 'grid' :
                    var = tools.calc_time_var_file(Blocks, pol_ind, 0)
                    # Convert from masked array to array.
                    var = var.filled(9999.)
                else :
                    var = 1.
                weight = 1/var
                
                for Data in Blocks :
                    dims = Data.dims
                    Data.calc_freq()
                    # On first pass set up the map parameters.
                    if first_block :
                        shape = map_shape + (dims[-1],)
                        if first_pol :
                            npol = dims[1]
                        # Get the current polarization integer.
                        this_pol = Data.field['CRVAL4'][pol_ind]
                        # The Map skeleton is a DataMap object that contains
                        # all the information to make a map except for the map
                        # data itself.  The skeleton is saved to disk as a fits
                        # file so it can be used in the future to make fits
                        # maps.
                        MapSkeleton = tools.set_up_map(Data, 
                                            params['field_centre'], shape[0:2], 
                                            (ra_spacing, spacing))
                        # Allowcate memory for the map.
                        map_data = sp.zeros(shape, dtype=float)
                        map_data = algebra.make_vect(map_data,
                                        axis_names=('ra', 'dec', 'freq'))
                        # Allowcate memory for the inverse map noise.
                        if algorithm in ('grid', 'diag_file') :
                            noise_inv = sp.zeros(shape, dtype=float)
                            noise_inv = algebra.make_mat(noise_inv,
                                            axis_names=('ra', 'dec', 'freq'),
                                            row_axes=(0,1,2), col_axes=(0,1,2))
                        elif algorithm in ('disjoint_scans', 'ds_grad') :
                            # At each frequency use full N^2 noise matrix, but
                            # assume each frequency has uncorrelated noise.
                            # This is a big matrix so make sure it is
                            # reasonable.
                            size = shape[0]^2*shape[1]^2*shape[2]
                            if size > 4e9 : # 16 GB
                                raise RuntimError('Map size too big.  Asked '
                                                  'for a lot of memory.')
                            noise_inv = sp.zeros(shape[0:2] + shape,
                                                 dtype=sp.float32)
                            noise_inv = algebra.make_mat(noise_inv,
                                            axis_names=('ra', 'dec', 'ra',
                                                        'dec' 'freq'),
                                            row_axes=(0,1,4), col_axes=(2,3,4))
                            # Allowcate memory for temporary data. Hold the
                            # number of times each pixel in this scan is hit.
                            pixel_hits = sp.empty((dims[0], dims[-1]))
                        first_block = False
                    else :
                        MapSkeleton.history = data_map.merge_histories(
                            Map, Data)

                    # Figure out the pointing pixel index and the frequency 
                    # indicies.
                    Data.calc_pointing()
                    ra_inds = tools.calc_inds(Data.ra, 
                               params['field_centre'][0], shape[0], ra_spacing)
                    dec_inds = tools.calc_inds(Data.dec, 
                                         params['field_centre'][1], 
                                         shape[1], params['pixel_spacing'])
                    data = Data.data[:,pol_ind,0,:]
                    if algorithm in ('grid', 'diag_file') :
                        add_data_2_map(data, ra_inds, dec_inds, map_data, 
                                       noise_inv, None, weight)
                    elif algorithm in ('disjoint_scans', ) :
                        add_data_2_map(data - ma.mean(data, 0), ra_inds, 
                                       dec_inds, map_data, None, None, weight)
                        pixel_hits[:] = 0
                        pixel_list = pixel_counts(data, ra_inds, dec_inds, 
                                        pixel_hits, map_shape=shape[0:2])
                        add_scan_noise(pixel_list, pixel_hits, var, noise_inv)
                # End Blocks for loop.
            # End file name for loop.
        # Now write the dirty maps out for this polarization.
        map_file_name = (params['output_root'] + 'map_' +
                         utils.polint2str(this_pol) + '.npy')
        algebra.save(map_data, map_file_name)
        noise_file_name = (params['output_root'] + 'noise_inv_' +
                         utils.polint2str(this_pol) + '.npy')
        # Also write 
        # End polarization for loop.





def add_data_2_map(data, ra_inds, dec_inds, map, noise_i, counts=None,
                   weight=1) :
    """Add a data masked array to a map.
    
    This function also adds the weight to the noise matrix for diagonal noise.
    """

    ntime = len(ra_inds)
    shape = sp.shape(map)
    if len(dec_inds) != ntime or len(data[:,0]) != ntime :
        raise ValueError('Time axis of data, ra_inds and dec_inds must be'
                         ' same length.') 
    if sp.shape(counts) != sp.shape(map) or len(map[0,0,:]) != len(data[0,:]) :
        raise ValueError('Map-counts shape  mismatch or data frequency axis '
                         'length mismatch.')

    for time_ind in range(ntime) :
        if (ra_inds[time_ind] >= 0 and ra_inds[time_ind] < shape[0] and
            dec_inds[time_ind] >= 0 and dec_inds[time_ind] < shape[1]) :
            # Get unmasked
            unmasked_inds = sp.logical_not(ma.getmaskarray(data[time_ind,:]))
            ind_map = (ra_inds[time_ind], dec_inds[time_ind], unmasked_inds)
            if not counts is None :
                counts[ind_map] += 1
            map[ind_map] += (weight*data)[time_ind, unmasked_inds]
            if not noise_i is None :
                if not hasattr(weight, '__iter__') :
                    noise_i[ind_map] += weight
                else :
                    noise_i[ind_map] += weight[unmasked_ inds]

def pixel_counts(data, ra_inds, dec_inds, pixel_hits, map_shape=(-1,-1)) :
    """Counts the hits on each unique pixel.

    Returns pix_list, a list of tuples, each tuple is a (ra,dec) index on a 
    map pixel hit on this scan.  The list only contains unique entries.  The
    array pixel_hits (preallowcated for performance), is
    filled with the number of hits on each of these pixels as a function of
    frequency index. Only the entries pixel_hits[:len(pix_list), :] 
    are meaningful.
    """

    if ra_inds.shape != dec_inds.shape or ra_inds.ndim != 1 :
        raise ValueError('Ra and Dec arrays not properly shaped.')
    if counts.shape[-1] != data.shape[-1] or counts.shape[0] < len(ra_inds):
        raise ValueError('counts not allowcated to right shape.')

    pix_list = []
    for ii in range(len(ra_inds)) :
        pix = (ra_inds[ii], dec_inds[ii])
        if ((map_shape[0] > -1 and pix[0] >= map_shape[0]) or 
            (map_shape[1] > -1 and pix[1] >= map_shape[1]) or
            pix[0] < 0 or pix[1] < 0) :
            continue
        elif not pix in pix_list :
            pix_list.append(pix)
        unmasked_freqs = sp.logical_not(ma.getmaskarray(data)[ii,:])
        counts[pix_list.index(pix), unmasked_freqs] += 1

    return pix_list

def add_scan_noise(pixels, pixel_hits, variance, noise_inv) :
    """Adds a scan to the map inverse noise matrix.

    Passed a list of map indices that were hit this scan and an array of the
    number of times each pixel was hit at each frequency.  This is all added to
    noise_inv, inversly wieghted by variance.  Governing formula found in
    Kiyo's notes November 27, 2010.
    """
    
    # Calculate number of good pointings are each frequency.
    n_pix = len(pixels)
    pointings = sp.sum(pixel_hits[:n_pix,:], 0)
    f_inds = pointings > 0
    point = pointings[f_inds]
    if hasattr(variance, '__iter__') :
        var = variance[f_inds]
    else :
        var = variance
    for ii, p1 in enumerate(pixels) :
        noise_inv[p1 + p1 + (f_inds,)] += sp.array(pixel_hits[ii,f_inds], 
                                                   dtype=float)/var
        for jj, p2 in enumerate(pixels) :
            noise_inv[p1 + p2 + (f_inds,)] -= (sp.array(pixel_hits[ii,f_inds], 
                                   dtype=float)*pixel_hits[jj,f_inds]/point/var)


# For running this module from the command line
if __name__ == '__main__' :
    import sys
    if len(sys.argv) == 2 :
        DirtyMap(str(sys.argv[1])).execute()
    elif len(sys.argv) > 2:
        print 'Maximum one argument, a parameter file name.'
    else :
        DirtyMap().execute()

