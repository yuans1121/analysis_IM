import numpy as np

import units


class Map2d(object):
    r"""A 2-d sky map.
    
    Attributes
    ----------
    x_width, y_width : float
        Angular size along each axis (in degrees).
    x_num, y_num : int
        Number of pixels along each angular axis.

        
    """
    x_width = 5.0
    y_width = 5.0

    x_num = 128
    y_num = 128

    def _width_array(self):
        return np.array([self.x_width, self.y_width], dtype=np.float64)*units.degree

    def _num_array(self):
        return np.array([self.x_num, self.y_num], dtype=np.int)

    @classmethod
    def like_map(cls, mapobj):
        c = cls()
        c.x_width = mapobj.x_width
        c.y_width = mapobj.y_width
        c.x_num = mapobj.x_num
        c.y_num = mapobj.y_num

        return c

class Map3d(object):
    r"""A 3-d sky map.

    Attributes
    ----------
    x_width, y_width : float
        Angular size along each axis (in degrees).
    nu_upper, nu_lower : float
        Range of frequencies (in Mhz).
    x_num, y_num : int
        Number of pixels along each angular axis.
    nu_num : int
        Number of frequency bins.
        
    """
    x_width = 5.0
    y_width = 5.0
    
    x_num = 128
    y_num = 128

    nu_num = 128

    nu_lower = 120.0
    nu_upper = 325.0

    def _width_array(self):
        return np.array([self.nu_upper - self.nu_lower, self.x_width*units.degree, self.widthy*units.degree], dtype=np.float64)

    def _num_array(self):
        return np.array([self.nu_num, self.x_num, self.y_num], dtype=np.int)

    @classmethod
    def like_map(cls, mapobj):
        c = cls()
        c.x_width = mapobj.x_width
        c.y_width = mapobj.y_width
        c.nu_upper = mapobj.nu_upper
        c.nu_lower = mapobj.nu_lower
        c.x_num = mapobj.x_num
        c.y_num = mapobj.y_num
        c.nu_num = mapobj.nu_num

        return c

