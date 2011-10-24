"""tools for plotting data cubes; this code is new and in developement"""
import subprocess
import os
import numpy as np
import numpy.ma as ma
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from core import algebra
import multiprocessing
from utils import data_paths

cube_frame_dir = "/mnt/raid-project/gmrt/eswitzer/wiggleZ/cube_frames/"

def plot_single(plotitem):
    """plot a single map slice; helper function for process pool"""
    (index, cube_slice, xaxis, yaxis, vaxis, xylabels, aspect, \
            title, cbar_title, fileprefix) = plotitem
    print title, repr(cube_slice.shape)
    plt.figure(figsize=(7,3.3))
    cplot = plt.contourf(xaxis, yaxis, np.transpose(cube_slice), vaxis)
    plt.axis('scaled')
    plt.axes().set_aspect(aspect) # 'equal' also?
    plt.xlim((np.min(xaxis), np.max(xaxis)))
    plt.ylim((np.min(yaxis), np.max(yaxis)))
    plt.xlabel(xylabels[0])
    plt.ylabel(xylabels[1])
    plt.title(title, fontsize=9)
    cticks = np.linspace(min(vaxis), max(vaxis), 7, endpoint=True)
    cbar = plt.colorbar(cplot, ticks=cticks)
    cbar.ax.set_yticklabels([('%5.2g' % val) for val in cticks])
    #cbar = plt.colorbar(cplot)
    cbar.ax.set_ylabel(cbar_title)
    filename = fileprefix + str('%03d' % index) + '.png'
    plt.savefig(filename, dpi=200)
    plt.clf()


def make_cube_movie(cubename, colorbar_title, cube_frame_dir,
                    filetag_suffix="",
                    outputdir="./", sigmarange=6., ignore=None, multiplier=1.,
                    transverse=False, title=None, sigmacut=None, logscale=False):
    """Make a stack of spatial slice maps and animate them
    transverse plots along RA and freq and image plane is in Dec
    First mask any points that exceed `sigmacut`, and then report the extent of
    `sigmarange` away from the mean
    """
    # set up the labels:
    tag = ".".join(cubename.split(".")[:-1])  # extract root name
    tag = tag.split("/")[-1]
    fileprefix = cube_frame_dir + tag
    nlevels = 500

    if transverse:
        orientation = "_freqRA"
    else:
        orientation = "_RADec"

    if not title:
        title = tag

    # prepare the data
    cube = algebra.make_vect(algebra.load(cubename)) * multiplier
    if logscale:
        cube = np.log10(cube)

    isnan = np.isnan(cube)
    isinf = np.isinf(cube)
    maskarray = ma.mask_or(isnan, isinf)

    if ignore is not None:
        maskarray = ma.mask_or(maskarray, (cube == ignore))

    if sigmacut:
        #np.set_printoptions(threshold=np.nan, precision=4)
        deviation = np.abs((cube-np.mean(cube))/np.std(cube))
        extend_maskarray = (cube > (sigmacut * deviation))
        maskarray = ma.mask_or(extend_maskarray, maskarray)

    mcube = ma.masked_array(cube, mask=maskarray)

    try:
        whmaskarray = np.where(maskarray)[0]
        mask_fraction = float(len(whmaskarray))/float(cube.size)
    except:
        mask_fraction = 0.

    print "fraction of map clipped: %f" % mask_fraction
    (cube_mean, cube_std) = (mcube.mean(), mcube.std())
    print "cube mean=%g std=%g" % (cube_mean, cube_std)

    try:
        len(sigmarange)
        color_axis = np.linspace(sigmarange[0], sigmarange[1],
                                nlevels, endpoint=True)
    except TypeError:
        if (sigmarange > 0.):
            color_axis = np.linspace(cube_mean - sigmarange * cube_std,
                                    cube_mean + sigmarange * cube_std,
                                    nlevels, endpoint=True)
        else:
            color_axis = np.linspace(ma.min(mcube),  ma.max(mcube),
                                    nlevels, endpoint=True)

    print "using range: [%g, %g]" % (np.min(color_axis), np.max(color_axis))

    freq_axis = cube.get_axis('freq')
    freq_axis /= 1.e6  # convert to MHz
    (ra_axis, dec_axis) = (cube.get_axis('ra'), cube.get_axis('dec'))

    runlist = []
    if transverse:
        for decind in range(cube.shape[2]):
            fulltitle = title + " (dec = %3.1f)" % (dec_axis[decind])
            runlist.append((decind, cube[:, :, decind], freq_axis,
                            ra_axis, color_axis, ["Freq","Ra"], 20., fulltitle,
                            colorbar_title, fileprefix))
    else:
        for freqind in range(cube.shape[0]):
            fulltitle = title + " (freq = %3.1f MHz)" % (freq_axis[freqind])
            runlist.append((freqind, cube[freqind, :, :], ra_axis,
                            dec_axis, color_axis, ["RA","Dec"], 1., fulltitle,
                            colorbar_title, fileprefix))

    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()-4)
    pool.map(plot_single, runlist)

    subprocess.check_call(('ffmpeg', '-r', '10', '-y', '-i', cube_frame_dir + tag + \
               '%03d.png', outputdir + tag + filetag_suffix + orientation + '.mp4'))

    for fileindex in range(len(runlist)):
        os.remove(fileprefix + str('%03d' % fileindex) + '.png')


def plot_GBT_maps(keyname, transverse=False, skip_noise=False, skip_map=True,
                  outputdir="./", sigmarange=[0.,0.001]):
    datapath_db = data_paths.DataPath()

    section_list = ['A', 'B', 'C', 'D']
    for section in section_list:
        if not skip_map:
            filename = datapath_db.fetch(keyname, intend_read=True,
                                         pick=(section + '_clean_map'))
            title = "Sec. %s, %s" % (section, keyname)
            make_cube_movie(filename,
                               "Temperature (mK)", cube_frame_dir,
                               sigmarange=5.,
                               outputdir=outputdir, multiplier=1000.,
                               transverse=transverse,
                               title=title)

            filename = datapath_db.fetch(keyname, intend_read=True,
                                         pick=(section + '_dirty_map'))
            title = "Sec. %s, %s (dirty)" % (section, keyname)
            make_cube_movie(filename,
                               "Temperature (mK)", cube_frame_dir,
                               sigmarange=5.,
                               outputdir=outputdir, multiplier=1000.,
                               transverse=transverse,
                               title=title)

        if not skip_noise:
            filename = datapath_db.fetch(keyname, intend_read=True,
                                         pick=(section + '_noise_diag'))
            title = "Sec. %s, %s (noise)" % (section, keyname)
            # sigmacut=0.008
            make_cube_movie(filename,
                               "Covariance", cube_frame_dir,
                               sigmarange=sigmarange,
                               outputdir=outputdir, multiplier=1.,
                               logscale=False,
                               transverse=transverse,
                               title=title)


def plot_simulations(keyname, transverse=False, outputdir="./"):
    """make movies of the 15hr simulations
    permutations: with or without streaming, including beam, adding real data
    """
    datapath_db = data_paths.DataPath()

    filename = datapath_db.fetch(keyname, pick='15')
    make_cube_movie(filename,
                       "Temperature (mK)", cube_frame_dir, sigmarange=5.,
                       outputdir=outputdir, multiplier=1000., transverse=transverse)

    #make_cube_movie(root_directory + "sim_beam_" + suffix,
    #                   "Temperature (mK)", cube_frame_dir, sigmarange=5.,
    #                   outputdir="./", multiplier=1000., transverse=transverse)
    #make_cube_movie(root_directory + "sim_beam_plus_data" + suffix,
    #                   "Temperature (mK)", cube_frame_dir, sigmarange=10.,
    #                   outputdir="./", multiplier=1000., transverse=transverse)
    #make_cube_movie(root_directory + "simvel_" + suffix,
    #                   "Temperature (mK)", cube_frame_dir, sigmarange=5.,
    #                   outputdir="./", multiplier=1000., transverse=transverse)
    #make_cube_movie(root_directory + "simvel_beam_" + suffix,
    #                   "Temperature (mK)", cube_frame_dir, sigmarange=5.,
    #                   outputdir="./", multiplier=1000., transverse=transverse)
    #make_cube_movie(root_directory + "simvel_beam_plus_data" + suffix,
    #                   "Temperature (mK)", cube_frame_dir, sigmarange=10.,
    #                   outputdir="./", multiplier=1000., transverse=transverse)


def plot_difference(filename1, filename2, title, sigmarange=6., sigmacut=None,
                    transverse=False, outputdir="./", multiplier=1000.,
                    logscale=False, fractional=False, filetag_suffix="",
                    ignore=None, diff_filename="./difference.npy"):
    """make movies of the difference of two maps (assuming same dimensions)"""
    map1 = algebra.make_vect(algebra.load(filename1))
    map2 = algebra.make_vect(algebra.load(filename2))

    if fractional:
        difftitle = "fractional diff."
        dmap = (map1-map2)/map1*100.
    else:
        difftitle = "difference"
        dmap = map1-map2

    algebra.save(diff_filename, dmap)

    make_cube_movie(diff_filename,
                       difftitle, cube_frame_dir, sigmarange=6,
                       sigmacut=sigmacut, outputdir=outputdir, ignore=ignore,
                       multiplier=multiplier, transverse=transverse,
                       logscale=False)

    make_cube_movie(filename1,
                       title, cube_frame_dir, sigmarange=sigmarange,
                       sigmacut=sigmacut, outputdir=outputdir, ignore=ignore,
                       multiplier=multiplier, transverse=transverse,
                       logscale=logscale, filetag_suffix="_1")

    make_cube_movie(filename2,
                       title, cube_frame_dir, sigmarange=sigmarange,
                       sigmacut=sigmacut, outputdir=outputdir, ignore=ignore,
                       multiplier=multiplier, transverse=transverse,
                       logscale=logscale, filetag_suffix="_2")
