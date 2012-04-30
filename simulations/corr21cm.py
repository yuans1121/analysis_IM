
import numpy as np

from corr import RedshiftCorrelation
from simulations.maps import Map3d

from utils import cubicspline as cs
from utils import units



class Corr21cm(RedshiftCorrelation, Map3d):
    r"""Correlation function of HI brightness temperature fluctuations.

    Incorporates reasonable approximations for the growth factor and
    growth rate.

    """

    add_mean = False

<<<<<<< HEAD
    def __init__(self, ps = None, redshift = 0.0, **kwargs):
        from os.path import join, dirname
        if ps == None:

            psfile = join(dirname(__file__),"data/ps_z1.5.dat")
=======
    def __init__(self, ps=None, sigma_v=0.0, redshift=0.0, **kwargs):
        if ps == None:
            from os.path import join, dirname
            #psfile = join(dirname(__file__),"data/ps_z1.5.dat")
            psfile = join(dirname(__file__),"data/wigglez_halofit_z1.5.dat")
            print "loading matter power file: " + psfile
>>>>>>> 2bb5253943ff6d75ecc81895ad37e53d3a7aaae5
            redshift = 1.5

            kstar = 5.0
            c1 = cs.LogInterpolater.fromfile(psfile)
            ps = lambda k: np.exp(-0.5 * k**2 / kstar**2) * c1(k)

        self._sigma_v = sigma_v

        RedshiftCorrelation.__init__(self, ps_vv=ps, redshift=redshift)
        self._load_cache(join(dirname(__file__),"data/corr_z1.5.dat"))
        #self.load_fft_cache(join(dirname(__file__),"data/fftcache.npz"))


    def T_b(self, z):
        r"""Mean 21cm brightness temperature at a given redshift.

        Temperature is in mK.

        Parameters
        ----------
        z : array_like
            Redshift to calculate at.

        Returns
        -------
        T_b : array_like

        Notes: the prefactor used to be 0.3 mK, but Tzu-Ching pointed out that this
        was from and error in 2008PhRvL.100i1303C, Eric recalculated this to be
        0.39 mK (agrees with 0.4 mK quoted over phone from Tzu-Ching)
        """

        return (0.39 * ((self.cosmology.omega_m + self.cosmology.omega_l * (1+z)**-3) / 0.29)**-0.5
                * ((1.0 + z) / 2.5)**0.5 * (self.omega_HI(z) / 1e-3))

    def mean(self, z):
        if self.add_mean:
            return self.T_b(z)
        else:
            return np.zeros_like(z)

    def omega_HI(self, z):
        return 1e-3

    def x_h(self, z):
        r"""Neutral hydrogen fraction at a given redshift.

        Just returns a constant at the moment. Need to add a more
        sophisticated model.

        Parameters
        ----------
        z : array_like
            Redshift to calculate at.

        Returns
        -------
        x_e : array_like
        """
        return 1e-3

    def prefactor(self, z):
        return self.T_b(z)


    def growth_factor(self, z):
        r"""Approximation for the matter growth factor.

        Uses a Pade approximation.

        Parameters
        ----------
        z : array_like
            Redshift to calculate at.

        Returns
        -------
        growth_factor : array_like

        Notes
        -----
        See _[1].

        .. [1] http://arxiv.org/abs/1012.2671
        """

        x = ((1.0 / self.cosmology.omega_m) - 1.0) / (1.0 + z)**3

        num = 1.0 + 1.175*x + 0.3064*x**2 + 0.005355*x**3
        den = 1.0 + 1.857*x + 1.021 *x**2 + 0.1530  *x**3

        d = (1.0 + x)**0.5 / (1.0 + z) * num / den

        return d

    def growth_rate(self, z):
        r"""Approximation for the matter growth rate.

        From explicit differentiation of the Pade approximation for
        the growth factor.

        Parameters
        ----------
        z : array_like
            Redshift to calculate at.

        Returns
        -------
        growth_factor : array_like

        Notes
        -----
        See _[1].

        .. [1] http://arxiv.org/abs/1012.2671
        """

        x = ((1.0 / self.cosmology.omega_m) - 1.0) / (1.0 + z)**3

        dnum = 3.0*x*(1.175 + 0.6127*x + 0.01607*x**2)
        dden = 3.0*x*(1.857 + 2.042 *x + 0.4590 *x**2)

        num = 1.0 + 1.175*x + 0.3064*x**2 + 0.005355*x**3
        den = 1.0 + 1.857*x + 1.021 *x**2 + 0.1530  *x**3

        f = 1.0 + 1.5 * x / (1.0 + x) + dnum / num - dden / den

        return f


    def bias_z(self, z):
        r"""It's unclear what the bias should be. Using 1 for the moment. """

        return np.ones_like(z) * 1.0


    def getfield(self):
        r"""Fetch a realisation of the 21cm signal.
        """
        z1 = units.nu21 / self.nu_upper - 1.0
        z2 = units.nu21 / self.nu_lower - 1.0

        cube = self.realisation(z1, z2, self.x_width, self.y_width, self.nu_num, self.x_num, self.y_num, zspace = False)[::-1,:,:].copy()

        return cube

    def get_kiyo_field(self, refinement=1):
        r"""Fetch a realisation of the 21cm signal (NOTE: in K)
        """
        z1 = units.nu21 / self.nu_upper - 1.0
        z2 = units.nu21 / self.nu_lower - 1.0

        cube = self.realisation(z1, z2, self.x_width, self.y_width,
                                self.nu_num, self.x_num, self.y_num,
                                refinement=refinement, zspace = False) * 0.001

        return cube

    def get_pwrspec(self, k_vec):
        r"""Fetch the power spectrum of the signal
        The effective redshift is found by averaging over 256 redshifts...
        """
        z1 = units.nu21 / self.nu_upper - 1.0
        z2 = units.nu21 / self.nu_lower - 1.0

        return self.powerspectrum_1D(k_vec, z1, z2, 256) * 1.e-6

    def get_kiyo_field_physical(self, refinement=1, density_only=False,
                                no_mean=False, no_evolution=False):
        r"""Fetch a realisation of the 21cm signal (NOTE: in K)
        """
        z1 = units.nu21 / self.nu_upper - 1.0
        z2 = units.nu21 / self.nu_lower - 1.0

        (cube, rsf, d) = self.realisation(z1, z2, self.x_width, self.y_width,
                                self.nu_num, self.x_num, self.y_num,
                                refinement=refinement, zspace = False,
                                report_physical=True, density_only=density_only,
                                no_mean=no_mean, no_evolution=no_evolution)

        return (cube * 0.001, rsf * 0.001, d)
