#! /usr/bin/env python 

import numpy as np
from core import algebra

def get_2d_k_bin_centre(ps_2d):

    k_p = np.arange(ps_2d.shape[0]) - ps_2d.shape[0]//2
    k_p = ps_2d.info['k_p_centre'] * ps_2d.info['k_p_delta']**k_p

    k_v = np.arange(ps_2d.shape[1]) - ps_2d.shape[1]//2
    k_v = ps_2d.info['k_v_centre'] * ps_2d.info['k_v_delta']**k_v

    return k_p, k_v

def get_2d_k_bin_edges(ps_2d):

    k_p, k_v = get_2d_k_bin_centre(ps_2d)

    k_p_edges  = np.append(k_p, k_p[-1]*ps_2d.info['k_p_delta'])
    k_p_edges /= np.sqrt(ps_2d.info['k_p_delta'])

    k_v_edges  = np.append(k_v, k_v[-1]*ps_2d.info['k_v_delta'])
    k_v_edges /= np.sqrt(ps_2d.info['k_v_delta'])

    return k_p_edges, k_v_edges

def load_transfer_function(rf_root, tr_root, auto=True):
    
    ps_rf = algebra.make_vect(algebra.load(rf_root))
    ps_tr = algebra.make_vect(algebra.load(tr_root))

    ps_tr[ps_tr==0] = np.inf

    transfer_function = ps_rf/ps_tr

    if auto:
        transfer_function **=2

    k_p_edges, k_v_edges = get_2d_k_bin_edges(ps_rf)

    return transfer_function, k_p_edges, k_v_edges

def load_weight(ns_root, transfer_function=None):
    
    ps_ns = algebra.make_vect(algebra.load(ns_root))
    kn_ns = algebra.make_vect(algebra.load(ns_root.replace('pow', 'kmn')))

    kn_ns[kn_ns==0] = np.inf

    gauss_noise = 2. * ps_ns / np.sqrt(kn_ns)
    if transfer_function != None:
        gauss_noise *= transfer_function

    gauss_noise[gauss_noise==0] = np.inf
    weight = (1./gauss_noise)**2

    k_p_edges, k_v_edges = get_2d_k_bin_edges(ps_ns)

    return weight, k_p_edges, k_v_edges

def load_power_spectrum_err(ps_root):
    
    ps_2derr = algebra.make_vect(algebra.load(ps_root.replace('pow', 'err')))

    k_p_edges, k_v_edges = get_2d_k_bin_edges(ps_2derr)

    return ps_2derr, k_p_edges, k_v_edges

def load_power_spectrum(ps_root):
    
    ps_2d = algebra.make_vect(algebra.load(ps_root))
    kn_2d = algebra.make_vect(algebra.load(ps_root.replace('pow', 'kmn')))

    k_p_edges, k_v_edges = get_2d_k_bin_edges(ps_2d)

    return ps_2d, kn_2d, k_p_edges, k_v_edges

def convert_2dps_to_1dps_sim(rf_root):

    power_spectrum = algebra.make_vect(algebra.load(rf_root))
    power_spectrum_err = algebra.make_vect(algebra.load(rf_root.replace('pow', 'err')))
    k_mode_number = algebra.make_vect(algebra.load(rf_root.replace('pow', 'kmn')))

    k_p_edges, k_v_edges = get_2d_k_bin_edges(power_spectrum)
    k_p_centre, k_v_centre = get_2d_k_bin_centre(power_spectrum)
    k_centre = np.sqrt(k_p_centre[:,None]**2 + k_v_centre[None, :]**2).flatten()
    k_edges_1d = k_p_edges

    #power_spectrum *= k_mode_number
    #power_spectrum_err *= k_mode_number

    power_spectrum_err **= 2

    k_mode,k_e = np.histogram(k_centre, k_edges_1d, weights=np.ones_like(k_centre))
    #k_mode,k_e = np.histogram(k_centre, k_edges_1d, weights=k_mode_number.flatten())
    power, k_e = np.histogram(k_centre, k_edges_1d, weights=power_spectrum.flatten())
    err,   k_e = np.histogram(k_centre, k_edges_1d, weights=power_spectrum_err.flatten())
    k_mode[k_mode==0] = np.inf
    power_1d = power/k_mode
    power_1d_err = np.sqrt(err)/k_mode
    return power_1d, power_1d_err, k_p_centre

def convert_2dps_to_1dps(ps_root, ns_root, tr_root, rf_root):

    transfer_function, k_p_edges, k_v_edges = load_transfer_function(rf_root, tr_root)

    weight, k_p_edges, k_v_edges = load_weight(ns_root, transfer_function)

    power_spectrum, k_mode_number, k_p_edges, k_v_edges = load_power_spectrum(ps_root)

    power_spectrum_err, k_p_edges, k_v_edges = load_power_spectrum_err(ps_root)

    power_spectrum *= transfer_function
    power_spectrum *= weight
    #power_spectrum *= k_mode_number

    power_spectrum_err *= transfer_function
    power_spectrum_err *= weight
    #power_spectrum_err *= k_mode_number
    power_spectrum_err **= 2

    k_p_centre, k_v_centre = get_2d_k_bin_centre(power_spectrum)
    k_centre = np.sqrt(k_p_centre[:,None]**2 + k_v_centre[None, :]**2).flatten()

    k_edges_1d = k_p_edges

    k_mode,k_e = np.histogram(k_centre, k_edges_1d, weights=np.ones_like(k_centre))
    #k_mode, k_e = np.histogram(k_centre, k_edges_1d, weights=k_mode_number.flatten())
    #k_mode_2, k_e = np.histogram(k_centre, k_edges_1d, weights=(k_mode_number**2).flatten())
    normal, k_e = np.histogram(k_centre, k_edges_1d, weights=weight.flatten())
    normal_2, k_e = np.histogram(k_centre, k_edges_1d, weights=(weight**2).flatten())
    power, k_e = np.histogram(k_centre, k_edges_1d, weights=power_spectrum.flatten())
    err, k_e = np.histogram(k_centre, k_edges_1d, weights=power_spectrum_err.flatten())

    k_mode[k_mode==0] = np.inf
    normal[normal==0] = np.inf
    power_1d = power/normal/k_mode
    power_1d_err = np.sqrt(err/normal_2)/k_mode

    return power_1d, power_1d_err, k_p_centre
