r"""Code to run large batches of quadratic estimators on combinations of
data/sims

The code is run in two steps:
1. with compile_tag=None (default) calculate and cache all the power spectra
2. with compile_tag=some identifier for the outputs, read the caches, write a
summary file, and return the power spectra and bins

The reason for this structure is that it is expensive to compute the hundreds
of power spectra that go into a plot, but one also needs to try out many
different ways of combining the outputs to form transfer functions, etc.,
different 2D->1D binnings, etc.

The bin edges for the output power spectra are in
        bin_left = pwr_1d[0]['bin_left']
        bin_center = pwr_1d[0]['bin_center']
        bin_right = pwr_1d[0]['bin_right']

TODO: generate=True and False have different outputs and will get confused now
replace pwr2d_run with pwr_out[0], pwr1d_run with pwr_out[1]
"""
import numpy as np
import math
from utils import data_paths
from correlate import map_pair as mp
from correlate import pwrspec_estimation as pe
from utils import batch_handler
from kiyopy import parse_ini


def call_xspec_run(map1_key, map2_key,
                   noiseinv1_key, noiseinv2_key,
                   inifile=None):
    r"""a free-standing function which calls the xspec analysis
    """
    params_init = {
        "unitless": True,
        "return_3d": False,
        "truncate": False,
        "window": None,
        "refinement": 2,
        "pad": 5,
        "order": 2,
        "freq_list": tuple(range(256)),
        "bins": [0.00765314, 2.49977141, 35]
                   }
    prefix = 'xs_'

    params = parse_ini.parse(inifile, params_init, prefix=prefix)
    if inifile is None:
        print "WARNING: no ini file for pwrspec estimation"

    # initialize and calculate the xspec
    simpair = mp.MapPair(map1_key, map2_key,
                         noiseinv1_key, noiseinv2_key,
                         params['freq_list'], avoid_db=True)

    bparam = params['bins']
    bins = np.logspace(math.log10(bparam[0]),
                       math.log10(bparam[1]),
                       num = bparam[2], endpoint=True)

    retval = simpair.pwrspec_summary(window=params['window'],
                                     unitless=params['unitless'],
                                     bins=bins,
                                     truncate=params['truncate'],
                                     refinement=params['refinement'],
                                     pad=params['pad'],
                                     order=params['order'],
                                     return_3d=params['return_3d'])

    return retval


def call_phys_space_run(cube1_file, cube2_file,
                        inifile=None):
    """Directly call the power spectral estimation on some physical vol"""
    params_init = {
        "unitless": True,
        "return_3d": False,
        "truncate": False,
        "window": "blackman",
        "bins": [0.00765314, 2.49977141, 35]
                   }
    prefix = 'xs_'

    params = parse_ini.parse(inifile, params_init, prefix=prefix)
    if inifile is None:
        print "WARNING: no ini file for pwrspec estimation"

    bparam = params['bins']
    bins = np.logspace(math.log10(bparam[0]),
                       math.log10(bparam[1]),
                       num = bparam[2], endpoint=True)

    retval = pe.calculate_xspec_file(cube1_file, cube2_file, bins,
                    weight1_file=None, weight2_file=None,
                    truncate=params['truncate'], window=params['window'],
                    return_3d=params['return_3d'], unitless=params['unitless'])

    return retval


def convert_keydict_to_filedict(dbkeydict, db=None):
    if db is None:
        db = data_paths.DataPath()

    filedict = {}
    for name in dbkeydict:
        filedict[name] = db.fetch(dbkeydict[name])

    return filedict


def theory_power_spectrum(redshift_filekey, bin_centers,
                          unitless=True, fileout="theory.dat"):
    r"""TODO: make this work ... needs some minor changes
    probably move elsewhere
    """
    zfilename = datapath_db.fetch(redshift_filekey, intend_read=True,
                                      pick='1')

    zspace_cube = algebra.make_vect(algebra.load(zfilename))
    simobj = corr21cm.Corr21cm.like_kiyo_map(zspace_cube)
    pwrspec_input = simobj.get_pwrspec(bin_center)
    if unitless:
        pwrspec_input *= bin_center ** 3. / 2. / math.pi / math.pi

    outfile = open(fileout, "w")
    for specdata in zip(bin_left, bin_center, bin_right, pwrspec_input):
        outfile.write(("%10.15g " * 4 + "\n") % specdata)

    outfile.close()
