import pyfits
import scipy as sp
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid

from parkes import fitsGBT

#rawdatapath = ('/mnt/raid-project/gmrt/raid-pen/pen/Parkes/2dF/DATA/p641/sdfits/rawdata/sept11/east/2008-09-11_1217_east1_1392_P641.sdfits',)
#rawdatapath = ('/mnt/raid-project/gmrt/raid-pen/pen/Parkes/2dF/DATA/p641/sdfits/rawdata/sept14/east/2008-09-14_2027_west2_1315_P641.sdfits',)
#rawdatapath = ('/mnt/raid-project/gmrt/raid-pen/pen/Parkes/2dF/DATA/p641/sdfits/rawdata/sept12/west/2008-09-12_1534_west2_1315_P641.sdfits',)
#rawdatapath = ('/mnt/raid-project/gmrt/raid-pen/pen/Parkes/2dF/DATA/p641/sdfits/rawdata/sept11/west/2008-09-11_1647_west1_1290_drift_P641.sdfits',)
#rawdatapath = ('/mnt/raid-project/gmrt/raid-pen/pen/Parkes/2dF/DATA/p641/sdfits/rawdata/sept13/west/2008-09-13_1737_west1_1315_P641.sdfits',)

#rawdatapath = ('/mnt/raid-project/gmrt/ycli/86_wigglez1hr_centre_ralongmap_19-28.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/55_wigglez15hrst_ralongmap_272-279.fits',)
#rawdatapath = ('/home/ycli/workspace/map_result/parkes/parkes_2008_09_12_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2008_09_12_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/flagged/parkes_2008_09_12_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_12_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/pol_selected/parkes_2008_09_12_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2008_09_13_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/flagged/parkes_2008_09_13_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2008_09_14_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/flagged/parkes_2008_09_14_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2008_09_11_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2008_09_11_east_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2008_09_12_east_P641.fits',)

#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_11_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_11_east_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_12_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_13_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_13_east_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_12_east_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_13_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_13_east_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_14_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_14_east_P641.fits',)

#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2008_09_13_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2008_09_13_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/flagged/parkes_2008_09_13_west_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2008_09_13_west_P641.fits',)

#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/parkes_2012_10_27_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/parkes_2012_10_27_P641.fits',)

#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/cal_parkes_2012_10_27_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/cal_parkes_2012_10_24_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/ncal_parkes_2012_10_24_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/rebinned/cal_new_parkes_2012_10_24_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/flagged/cal_new_parkes_2012_10_24_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/flagged/beamcal_parkes_2012_10_24_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/beamcal_parkes_2012_10_24_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/parkes/nobpcal_parkes_2012_10_24_P641.fits',)
#rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/flagged/nobpcal_parkes_2012_10_24_P641.fits',)
rawdatapath = ('/mnt/raid-project/gmrt/ycli/map_result/flagged/nobpcal_beamcal_parkes_2012_10_24_P641.fits',)

class CheckFitsFile(object):

    def __init__(self, datapath):
        try:
            self.hdulist = pyfits.open(datapath)
        except IOError:
            print 'Can not open file %s' % datapath
            exit()
        
        self.datapath = datapath
        
        self.tbdata = self.hdulist[1].data
        
        self.hdulist.close()

        self.reader = fitsGBT.Reader(datapath)

        print self.tbdata.field('TSYS').shape
        print self.tbdata.field('TSYS')[0:10]
        print self.tbdata.field('DATA').shape

    def printhead(self):
        print self.hdulist[1].header
        
        
    def printlabel(self):
        self.fieldlabel = []
        
        for i in range(self.hdulist[1].header['TFIELDS']):
            self.fieldlabel.append(self.hdulist[1].header['TTYPE%d'%(i+1)])
        
        #for i in range(len(tbdata)):
            #print tbdata[i][fieldlabel[3]], 

        for i in range(self.hdulist[1].header['TFIELDS']):
            print self.hdulist[1].header['TTYPE%d'%(i+1)]
            print sp.unique(self.tbdata.field(self.fieldlabel[i])).shape
            print self.tbdata.field(self.fieldlabel[i]).shape
            print self.tbdata.field(self.fieldlabel[i])
            print
        
        #print self.tbdata.field('AZIMUTH')[:13]
        #print self.tbdata.field(fieldlabel[6])[:200]
        #print self.tbdata.field(fieldlabel[6])[200:1000]

    def plottsys(self):
        tsys_x = self.tbdata.field('TSYS')[0::2]#[:10*90*13]
        tsys_y = self.tbdata.field('TSYS')[1::2]#[:10*90*13]

        x = range(tsys_x.shape[0]/13)

        plt.figure(figsize=(10, 6))
        for i in range(3):
            plt.plot(x, tsys_x[i::13], label='x tsys beam %d'%i)
            plt.plot(x, tsys_y[i::13], label='y tsys beam %d'%i)

        plt.legend(ncol=4, frameon=False)
        plt.xlabel('time ')
        plt.ylabel('Tsys')
        plt.ylim(ymin=13, ymax=17)
        plt.tick_params(length=6, width=1.)
        plt.tick_params(which='minor', length=3, width=1.)
        plt.savefig('./png/parkes_tsys_time.png', format='png')

    def plotT(self):
        spectrum_xx = self.tbdata.field('DATA')[0::2,:]#[:10*90*13,:]
        spectrum_yy = self.tbdata.field('DATA')[1::2,:]#[:10*90*13,:]

        spectrum_xx = np.ma.masked_where(np.isnan(spectrum_xx), spectrum_xx)
        spectrum_yy = np.ma.masked_where(np.isnan(spectrum_yy), spectrum_yy)

        x = range(spectrum_xx.shape[0]/13)
        #print spectrum_yy[0::13, 500]

        plt.figure(figsize=(10, 6))
        for i in range(3):
            plt.plot(x, spectrum_xx[i::13,500], label='x T beam %d'%i)
            plt.plot(x, spectrum_yy[i::13,500], label='y T beam %d'%i)

        plt.legend(ncol=4, frameon=False)
        plt.xlabel('time ')
        plt.ylabel('T')
        plt.ylim(ymin=-1, ymax=1)
        plt.tick_params(length=6, width=1.)
        plt.tick_params(which='minor', length=3, width=1.)
        plt.savefig('./png/parkes_T_time.png', format='png')

    def plotfreq_time(self):
        tsys_x = self.tbdata.field('TSYS')[0::2][0::13]
        tsys_y = self.tbdata.field('TSYS')[1::2][0::13]
        spectrum_xx = self.tbdata.field('DATA')[0::2,:][0::13,:]#[:900,:]
        spectrum_yy = self.tbdata.field('DATA')[1::2,:][0::13,:]#[:900,:]
        spectrum_xx = np.ma.masked_where(np.isnan(spectrum_xx), spectrum_xx)
        spectrum_yy = np.ma.masked_where(np.isnan(spectrum_yy), spectrum_yy)
        #spectrum_xx /= spectrum_xx
        #spectrum_yy /= spectrum_yy
        #spectrum_xx *= tsys_x[:,None]
        #spectrum_yy *= tsys_y[:,None]
        spectrum_xx_m = np.ma.mean(spectrum_xx, axis=0)
        spectrum_yy_m = np.ma.mean(spectrum_yy, axis=0)
        #spectrum_xx -= spectrum_xx_m
        #spectrum_yy -= spectrum_yy_m
        #spectrum_xx = np.repeat(spectrum_xx, 200, axis=1)
        #spectrum_yy = np.repeat(spectrum_yy, 200, axis=1)
        x = range(spectrum_xx.shape[1])
        y = range(spectrum_xx.shape[0])
        print spectrum_xx.shape
        print spectrum_yy.shape
        cmin = -0.5
        cmax = 0.5
        f = plt.figure(figsize=(30, 50))
        ax = ImageGrid(f, 111,
                       nrows_ncols = (1, 2),
                       direction = "row",
                       axes_pad = 0.05,
                       add_all = True,
                       label_mode = "L",
                       share_all = True,
                       cbar_location = "right",
                       cbar_mode = "single",
                       cbar_size = "5%",
                       cbar_pad = 0.05,
                       )
        im0 = ax[0].pcolormesh(spectrum_xx)
        im0.set_clim(cmin, cmax)
        ax[0].set_xlim(x[0], x[-1])
        ax[0].set_ylim(y[0], y[-1])
        ax[0].set_xlabel('freq id')
        ax[0].set_ylabel('time cycle')
        ax[0].set_title('X')

        ax[0].cax.colorbar(im0)

        im1 = ax[1].pcolormesh(spectrum_yy)
        im1.set_clim(cmin, cmax)
        ax[1].set_xlim(x[0], x[-1])
        ax[1].set_ylim(y[0], y[-1])
        ax[1].set_xlabel('freq id')
        ax[1].set_title('Y')

        ax[1].cax.colorbar(im1)

        plt.tick_params(length=6, width=1.)
        plt.tick_params(which='minor', length=3, width=1.)
        plt.savefig('./png/parkes_test_freq_time.png', format='png')

    def plotfreq(self):
        spectrum_xx = self.tbdata.field('DATA')[0::2,:][0::13,:]
        spectrum_yy = self.tbdata.field('DATA')[1::2,:][0::13,:]

        badfreq = []
        badfreq = [9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 22, 23,]
        if len(badfreq) != 0:
            mask = np.zeros(spectrum_xx.shape)
            mask[:,badfreq] = 1.
            spectrum_xx = np.ma.masked_array(spectrum_xx, mask = mask)
            spectrum_yy = np.ma.masked_array(spectrum_yy, mask = mask)

        x = range(spectrum_xx.shape[1])
        print spectrum_xx.shape
        print spectrum_yy.shape
        plt.figure(figsize=(8,5))
        #for i in range(100):
        for i in range(spectrum_xx.shape[0]):
            plt.plot(x, spectrum_xx[i], c='0.6')

        #plt.ylim(ymax=350,ymin=0)
        plt.savefig('./png/parkes_test_flag.png', format='png')

    def plotradec(self):
        scan_inds = self.reader.scan_set
        plt.figure(figsize=(33,4))
        ax = plt.gca()
        beamfwhp = 14.0/60.
        for thisscan in scan_inds:
            block = self.reader.read(thisscan)
            block.calc_pointing('W')
            print block.ra.shape
            for i in range(block.ra.shape[0]):
                for j in range(block.ra.shape[1]):
                    cir = plt.Circle((block.ra[i,j], 
                                      block.dec[i,j]),
                                      radius=beamfwhp/2., 
                                      fc='b', 
                                      ec="none",
                                      alpha=0.1)
                    ax.add_patch(cir)
            ax.autoscale_view()
        plt.xlabel('RA [deg]')
        plt.ylabel('DEC [deg]')
        plt.tick_params(length=6, width=1.)
        plt.tick_params(which='minor', length=3, width=1.)
        plt.savefig('./png/parkes_test_radec.png', format='png')

    def plotradec_one(self):
        scan_inds = self.reader.scan_set
        plt.figure(figsize=(6,6))
        beamfwhp = 14.0/60.
        ax = plt.gca()
        for thisscan in scan_inds[0:1]:
            block = self.reader.read(thisscan)
            block.calc_pointing()
            print block.ra.shape
            print block.dec.shape
            for i in range(13):
                cir = plt.Circle((block.ra[0,i],
                                  block.dec[0,i]),
                                  radius=beamfwhp/2., 
                                  fc="none", 
                                  edgecolor='k')
                ax.add_patch(cir)
            ax.autoscale_view()
        plt.xlabel('RA [deg]')
        plt.ylabel('DEC [deg]')
        plt.xlim(xmin=315.5, xmax=318.5)
        plt.ylim(ymin=-37.5, ymax=-34.5)
        plt.tick_params(length=6, width=1.)
        plt.tick_params(which='minor', length=3, width=1.)
        plt.savefig('./png/parkes_test_radec_one.png', format='png')

    def plotelaz(self):
        scan_inds = self.reader.scan_set
        plt.figure(figsize=(15,3))
        ax = plt.gca()
        beamfwhp = 14.0/60.
        for thisscan in scan_inds:
            block = self.reader.read(thisscan)
            for i in range(block.field['CRVAL2'].shape[0]):
                for j in range(block.field['CRVAL2'].shape[1]):
                    cir = plt.Circle((block.field['CRVAL2'][i,j], 
                                      block.field['CRVAL3'][i,j]),
                                      radius=beamfwhp/2., 
                                      fc='b', 
                                      ec="none",
                                      alpha=0.003)
                    ax.add_patch(cir)
            ax.autoscale_view()
            #plt.scatter(block.field['CRVAL2'][:,:], block.field['CRVAL3'][:,:],
            #            c='w', alpha=0.3)
        plt.xlabel('Azimuth [deg]')
        plt.ylabel('Elevation [deg]')
        plt.tick_params(length=6, width=1.)
        plt.tick_params(which='minor', length=3, width=1.)
        plt.savefig('./png/parkes_test_elaz.png', format='png')

    def plotelaz_one(self):
        scan_inds = self.reader.scan_set
        plt.figure(figsize=(6,6))
        ax = plt.gca()
        beamfwhp = 14.0/60.
        for thisscan in scan_inds[0:1]:
            block = self.reader.read(thisscan)
            print block.field['CRVAL2'].shape
            print block.field['CRVAL3'].shape
            #plt.scatter(block.field['CRVAL2'][0,:], block.field['CRVAL3'][0,:],
            #            c='w', alpha=0.3)
            for i in range(13):
                cir = plt.Circle((block.field['CRVAL2'][0,i],
                                  block.field['CRVAL3'][0,i]),
                                  radius=beamfwhp/2., 
                                  fc='none', 
                                  ec='k')
                ax.add_patch(cir)
            ax.autoscale_view()
        plt.xlabel('Azimuth [deg]')
        plt.ylabel('Elevation [deg]')
        plt.tick_params(length=6, width=1.)
        plt.tick_params(which='minor', length=3, width=1.)
        plt.savefig('./png/parkes_test_elaz_one.png', format='png')

    def plotonepoint(self, scan=0, cycle=0):
        scan_inds = self.reader.scan_set
        beamfwhp = 14.0/60.
        #f = plt.figure(figsize=(10, 6))
        #ax = ImageGrid(f, 111,
        #               nrows_ncols = (1, 2),
        #               direction = "row",
        #               axes_pad = 1,
        #               add_all = True,
        #               label_mode = "all",
        #               share_all = False,
        #               cbar_location = "right",
        #               cbar_mode = "single",
        #               cbar_size = "5%",
        #               cbar_pad = 0.05,
        #               )

        f, ax = plt.subplots(1, 2, figsize=(13,6))
        block = self.reader.read(scan_inds[scan])
        block.calc_pointing()
        for i in range(13):
            print block.field['DATE-OBS'][cycle]
            cir0 = plt.Circle((block.field['CRVAL2'][cycle,i],
                              block.field['CRVAL3'][cycle,i]),
                              radius=beamfwhp/2., 
                              fc='none', 
                              ec='k')
            ax[0].add_patch(cir0)
            ax[0].text(block.field['CRVAL2'][cycle,i],
                       block.field['CRVAL3'][cycle,i],
                       '%d'%i)

            cir1 = plt.Circle((block.ra[cycle,i],
                              block.dec[cycle,i]),
                              radius=beamfwhp/2., 
                              fc="none", 
                              edgecolor='k')
            ax[1].add_patch(cir1)
            ax[1].text(block.ra[cycle,i], 
                       block.dec[cycle,i],
                       '%d'%i)
        ax[0].autoscale_view()
        ax[0].set_xlabel('Azimuth [deg]')
        ax[0].set_ylabel('Elevation [deg]')

        ax[0].axis('equal')
        ax[0].tick_params(length=6, width=1.)
        ax[0].tick_params(which='minor', length=3, width=1.)
        
        ax[1].autoscale_view()
        ax[1].set_xlabel('RA [deg]')
        ax[1].set_ylabel('DEC [deg]')

        ax[1].axis('equal')
        ax[1].tick_params(length=6, width=1.)
        ax[1].tick_params(which='minor', length=3, width=1.)

        plt.savefig('./png/parkes_test_one_point.png', format='png')
        
if __name__=="__main__":
    checkfits = CheckFitsFile(rawdatapath[0])

    #checkfits.printhead()
    #checkfits.printlabel()

    checkfits.plotfreq_time()
    checkfits.plottsys()
    checkfits.plotT()
    #checkfits.plotfreq()
    #checkfits.plotradec()
    #checkfits.plotelaz()
    #checkfits.plotradec_one()
    #checkfits.plotelaz_one()

    #checkfits.plotonepoint()


