import numpy as np
from numpy import cos, sin, pi, exp, sqrt, arctan2
from scipy.integrate import odeint
from numba import jit, prange
import matplotlib as mpl
import matplotlib.pyplot as plt
##<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

## Constant //////
hbar = 1.05e-34 # m2 kg / s
e = 1.6e-19 # C

## Units ////////
meVolt = 1.602e-22 # 1 meV in Joule
Angstrom = 1e-10 # 1 A in meters
picosecond = 1e-12 # 1 ps in seconds

## This coefficient takes into accound all units and constant to prefactor the movement equation
units_move_eq =  e * Angstrom**2 * picosecond * meVolt / hbar**2

## This coefficient takes into accound all units and constant to prefactor Chambers formula
units_chambers = 2 * e**2 / (2*pi)**3 * meVolt * picosecond / Angstrom / hbar**2


class Conductivity:
    def __init__(self, bandObject, Bamp, Bphi=0, Btheta=0, gamma_0=15, gamma_dos=0, gamma_k=0, power=2):

        # Band object
        self.bandObject = bandObject ## WARNING do not modify within this object

        # Magnetic field in degrees
        self._Bamp   = Bamp
        self._Btheta = Btheta
        self._Bphi   = Bphi
        self._B_vector = self.BFunc() # np array fo Bx,By,Bz

        # Scattering rate
        self.gamma_0 = gamma_0 # in THz
        self.gamma_dos = gamma_dos # in THz
        self.gamma_k = gamma_k # in THz
        self.power   = int(power)
        if self.power % 2 == 1:
            self.power += 1

        # Time parameters
        self.tau_0 = 1 / self.gamma_0 # in picoseconds
        self.tmax = 8 * self.tau_0 # in picoseconds
        self._Ntime = 500 # number of steps in time
        self.dt = self.tmax / self.Ntime
        self.t = np.arange(0, self.tmax, self.dt)
        self.dt_array = np.append(0, self.dt * np.ones_like(self.t))[:-1] # integrand for tau_function

        # Time-dependent kf, vf
        self.kft = None
        self.vft = None

        # Conductivity Tensor: x, y, z = 0, 1, 2
        self.sigma = np.empty((3,3), dtype= np.float64)

    ## Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#
    def _get_B_vector(self):
        return self._B_vector
    def _set_B_vector(self, B_vector):
        print("Cannot access B_vector directly, just change Bamp, Bphi, Btheta")
    B_vector = property(_get_B_vector, _set_B_vector)

    def _get_Bamp(self):
        return self._Bamp
    def _set_Bamp(self, Bamp):
        self._Bamp = Bamp
        self._B_vector = self.BFunc()
    Bamp = property(_get_Bamp, _set_Bamp)

    def _get_Bphi(self):
        return self._Bphi
    def _set_Bphi(self, Bphi):
        self._Bphi = Bphi
        self._B_vector = self.BFunc()
    Bphi = property(_get_Bphi, _set_Bphi)

    def _get_Btheta(self):
        return self._Btheta
    def _set_Btheta(self, Btheta):
        self._Btheta = Btheta
        self._B_vector = self.BFunc()
    Btheta = property(_get_Btheta, _set_Btheta)

    def _get_Ntime(self):
        return self._Ntime
    def _set_Ntime(self, Ntime):
        self._Ntime = Ntime
        self.dt = self.tmax / self._Ntime
        self.t = np.arange(0, self.tmax, self.dt) # integrand for tau_function
        self.dt_array = np.append(0, self.dt * np.ones_like(self.t))[:-1]
    Ntime = property(_get_Ntime, _set_Ntime)

    ## Special Methods >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#
    def __eq__(self, other):
        return (
                self._Bamp   == other._Bamp
            and self._Btheta == other._Btheta
            and self._Bphi   == other._Bphi
            and np.all(self.sigma == other.sigma)
        )

    def __ne__(self, other):
        return not self == other

    ## Methods >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#
    def BFunc(self):
        B = self._Bamp * \
            np.array([sin(self._Btheta*pi/180) * cos(self._Bphi*pi/180),
                      sin(self._Btheta*pi/180) * sin(self._Bphi*pi/180),
                      cos(self._Btheta*pi/180)])
        return B

    def crossProductVectorized(self, vx, vy, vz):
        # (- B) represents -t in vj(-t, k) in the Chambers formula
        # if integrated from 0 to +infinity, instead of -infinity to 0
        product_x = vy[:] * -self._B_vector[2] - vz[:] * -self._B_vector[1]
        product_y = vz[:] * -self._B_vector[0] - vx[:] * -self._B_vector[2]
        product_z = vx[:] * -self._B_vector[1] - vy[:] * -self._B_vector[0]
        return np.vstack((product_x, product_y, product_z))

    def solveMovementFunc(self):
        len_t = self.t.shape[0]
        len_kf = self.bandObject.kf.shape[1]
        # Flatten to get all the initial kf solved at the same time
        self.bandObject.kf.shape = (3 * len_kf,)
        # Sovle differential equation
        self.kft = odeint(self.diffEqFunc, self.bandObject.kf, self.t, rtol = 1e-4, atol = 1e-4).transpose()
        # Reshape arrays
        self.bandObject.kf.shape = (3, len_kf)
        self.kft.shape = (3, len_kf, len_t)
        # Velocity function of time
        self.vft = np.empty_like(self.kft, dtype = np.float64)
        self.vft[0, :, :], self.vft[1, :, :], self.vft[2, :, :] = self.bandObject.v_3D_func(self.kft[0, :, :], self.kft[1, :, :], self.kft[2, :, :])

    def diffEqFunc(self, k, t):
        len_k = int(k.shape[0]/3)
        k.shape = (3, len_k) # reshape the flatten k
        vx, vy, vz =  self.bandObject.v_3D_func(k[0,:], k[1,:], k[2,:])
        dkdt = ( - units_move_eq ) * self.crossProductVectorized(vx, vy, vz)
        dkdt.shape = (3*len_k,) # flatten k again
        return dkdt

    def tOverTauFunc(self, k, v):
        phi = arctan2(k[1,:], k[0,:])
        dos = 1 / sqrt(v[0,:]**2 + v[1,:]**2 + v[2,:]**2)
        dos_norm = 0.006 # value to normalize the DOS to a quantity without units
        # Integral from 0 to t of dt' / tau( k(t') ) or dt' * gamma( k(t') )
        t_over_tau = np.cumsum( self.dt_array * ( self.gamma_0 + self.gamma_dos * dos / dos_norm + self.gamma_k * cos(2*phi)**self.power ) )
        return t_over_tau

    # def tOverTauFunc(self, k, v):
    #     return optimized_tOverTauFunc(k, v, self.dt_array, self.gamma_0, self.gamma_dos, self.gamma_k, self.power)

    def solveMovementForPoint(self, kpoint):
        len_t = self.t.shape[0]
        kt = odeint(self.diffEqFunc, kpoint, self.t, rtol = 1e-4, atol = 1e-4).transpose() # solve differential equation
        kt = np.reshape(kt, (3, 1, len_t))
        return kt

    def VelocitiesProduct(self, i, j):
        """ Index i and j represent x, y, z = 0, 1, 2
            for example, if i = 0: vif = vxf """
        ## Velocity components
        vif  = self.bandObject.vf[i,:]
        vjft = self.vft[j,:,:]
        v_product = np.empty(vif.shape[0], dtype = np.float64)
        for i0 in range(vif.shape[0]):
            vj_sum_over_t = np.sum( vjft[i0,:] * exp( - self.tOverTauFunc(self.kft[:,i0,:], self.vft[:,i0,:]) ) * self.dt ) # integral over t
            v_product[i0] = vif[i0] * vj_sum_over_t
        return v_product

    # def VelocitiesProduct(self, i, j):
    #     return optimized_VelocitiesProduct(self.kft, self.bandObject.vf, self.vft, self.dt, self.dt_array, self.gamma_0, self.gamma_dos, self.gamma_k, self.power, i, j)

    def chambersFunc(self, i = 2, j = 2):
        """ Index i and j represent x, y, z = 0, 1, 2
            for example, if i = 0 and j = 1 : sigma[i,j] = sigma_xy """
        self.sigma[i, j] = units_chambers * np.sum(self.bandObject.dos * self.bandObject.dkf * self.VelocitiesProduct(i=i, j=j)) * \
                           (self.bandObject.particlesPerkVolume / 2) # if AF reconstructed, only 1 particule per FBZ instead of 2 (spins)

    ## Figures ////////////////////////////////////////////////////////////////#

    #///// RC Parameters //////#
    mpl.rcdefaults()
    mpl.rcParams['font.size'] = 24. # change the size of the font in every figure
    mpl.rcParams['font.family'] = 'Arial' # font Arial in every figure
    mpl.rcParams['axes.labelsize'] = 24.
    mpl.rcParams['xtick.labelsize'] = 24
    mpl.rcParams['ytick.labelsize'] = 24
    mpl.rcParams['xtick.direction'] = "in"
    mpl.rcParams['ytick.direction'] = "in"
    mpl.rcParams['xtick.top'] = True
    mpl.rcParams['ytick.right'] = True
    mpl.rcParams['xtick.major.width'] = 0.6
    mpl.rcParams['ytick.major.width'] = 0.6
    mpl.rcParams['axes.linewidth'] = 0.6 # thickness of the axes lines
    mpl.rcParams['pdf.fonttype'] = 3  # Output Type 3 (Type3) or Type 42 (TrueType), TrueType allows
                                        # editing the text in illustrator

    def figLifeTime(self, mesh_phi = 1000):
        fig, axes = plt.subplots(1, 1, figsize=(6.5, 5.6))
        fig.subplots_adjust(left=0.10, right=0.70, bottom=0.20, top=0.9)

        phi = np.linspace(0, 2*pi, 1000)
        ## tau_0
        tau_0_x = self.tau_0 * cos(phi)
        tau_0_y = self.tau_0 * sin(phi)
        line = axes.plot(tau_0_x / self.tau_0, tau_0_y / self.tau_0,
                             clip_on=False, label=r"$\tau_{\rm 0}$", zorder=10)
        plt.setp(line, ls="--", c='#000000', lw=3, marker="",
                 mfc='#000000', ms=5, mec="#7E2320", mew=0)
        ## tau_k
        tau_k_x = 1 / (self.gamma_0 + self.gamma_k * (sin(phi) **
                                            2 - cos(phi)**2)**self.power) * cos(phi)
        tau_k_y = 1 / (self.gamma_0 + self.gamma_k * (sin(phi) **
                                            2 - cos(phi)**2)**self.power) * sin(phi)
        line = axes.plot(tau_k_x / self.tau_0, tau_k_y / self.tau_0,
                             clip_on=False, zorder=20, label=r"$\tau_{\rm tot}$")
        plt.setp(line, ls="-", c='#00FF9C', lw=3, marker="",
                 mfc='#000000', ms=5, mec="#7E2320", mew=0)
        ## tau_k_min
        phi_min = 3 * pi / 2
        tau_k_x_min = 1 / \
            (self.gamma_0 + self.gamma_k * (sin(phi_min)**2 -
                                  cos(phi_min)**2)**self.power) * cos(phi_min)
        tau_k_y_min = 1 / \
            (self.gamma_0 + self.gamma_k * (sin(phi_min)**2 -
                                  cos(phi_min)**2)**self.power) * sin(phi_min)
        line = axes.plot(tau_k_x_min / self.tau_0, tau_k_y_min / self.tau_0,
                             clip_on=False, label=r"$\tau_{\rm min}$", zorder=25)
        plt.setp(line, ls="", c='#1CB7FF', lw=3, marker="o",
                 mfc='#1CB7FF', ms=8, mec="#1CB7FF", mew=2)
        ## tau_k_max
        phi_max = 5 * pi / 4
        tau_k_x_max = 1 / \
            (self.gamma_0 + self.gamma_k * (sin(phi_max)**2 -
                                  cos(phi_max)**2)**self.power) * cos(phi_max)
        tau_k_y_max = 1 / \
            (self.gamma_0 + self.gamma_k * (sin(phi_max)**2 -
                                  cos(phi_max)**2)**self.power) * sin(phi_max)
        line = axes.plot(tau_k_x_max / self.tau_0, tau_k_y_max / self.tau_0,
                             clip_on=False, label=r"$\tau_{\rm max}$", zorder=25)
        plt.setp(line, ls="", c='#FF8181', lw=3, marker="o",
                 mfc='#FF8181', ms=8, mec="#FF8181", mew=2)

        fraction = np.abs(np.round(self.tau_0 / tau_k_y_min, 2))
        fig.text(0.74, 0.21, r"$\tau_{\rm max}$/$\tau_{\rm min}$" +
                 "\n" + r"= {0:.1f}".format(fraction))

        axes.set_xlim(-1, 1)
        axes.set_ylim(-1, 1)
        axes.set_xticks([])
        axes.set_yticks([])

        plt.legend(bbox_to_anchor=[1.51, 1.01], loc=1,
                   frameon=False,
                   numpoints=1, markerscale=1, handletextpad=0.2)

        plt.show()

    def figOnekft(self, index_kf = 0, meshXY = 1001):
        mesh_graph = meshXY
        kx = np.linspace(-pi / self.bandObject.a, pi / self.bandObject.a, mesh_graph)
        ky = np.linspace(-pi / self.bandObject.b, pi / self.bandObject.b, mesh_graph)
        kxx, kyy = np.meshgrid(kx, ky, indexing = 'ij')

        fig, axes = plt.subplots(1, 1, figsize = (5.6, 5.6))
        fig.subplots_adjust(left = 0.24, right = 0.87, bottom = 0.29, top = 0.91)

        fig.text(0.39,0.84, r"$k_{\rm z}$ = 0", ha = "right", fontsize = 16)

        line = axes.contour(kxx*self.bandObject.a, kyy*self.bandObject.b, self.bandObject.e_3D_func(kxx, kyy, 0), 0, colors = '#FF0000', linewidths = 3)
        line = axes.plot(self.kft[0, index_kf,:]*self.bandObject.a, self.kft[1, index_kf,:]*self.bandObject.b)
        plt.setp(line, ls ="-", c = 'b', lw = 1, marker = "", mfc = 'b', ms = 5, mec = "#7E2320", mew= 0) # trajectory
        line = axes.plot(self.bandObject.kf[0, index_kf]*self.bandObject.a, self.bandObject.kf[1, index_kf]*self.bandObject.b)
        plt.setp(line, ls ="", c = 'b', lw = 3, marker = "o", mfc = 'w', ms = 4.5, mec = "b", mew= 1.5)  # starting point
        line = axes.plot(self.kft[0, index_kf, -1]*self.bandObject.a, self.kft[1, index_kf, -1]*self.bandObject.b)
        plt.setp(line, ls ="", c = 'b', lw = 1, marker = "o", mfc = 'b', ms = 5, mec = "#7E2320", mew= 0)  # end point

        axes.set_xlim(-pi, pi)
        axes.set_ylim(-pi, pi)
        axes.tick_params(axis='x', which='major', pad=7)
        axes.tick_params(axis='y', which='major', pad=8)
        axes.set_xlabel(r"$k_{\rm x}$", labelpad = 8)
        axes.set_ylabel(r"$k_{\rm y}$", labelpad = 8)

        axes.set_xticks([-pi, 0., pi])
        axes.set_xticklabels([r"$-\pi$", "0", r"$\pi$"])
        axes.set_yticks([-pi, 0., pi])
        axes.set_yticklabels([r"$-\pi$", "0", r"$\pi$"])

        plt.show()

    def figOnevft(self, index_kf = 0):
        fig, axes = plt.subplots(1, 1, figsize = (9.2, 5.6))
        fig.subplots_adjust(left = 0.17, right = 0.81, bottom = 0.18, top = 0.95)

        axes.axhline(y = 0, ls ="--", c ="k", linewidth = 0.6)

        line = axes.plot(self.t, self.vft[2, index_kf,:])
        plt.setp(line, ls ="-", c = '#6AFF98', lw = 3, marker = "", mfc = '#6AFF98', ms = 5, mec = "#7E2320", mew= 0)

        axes.tick_params(axis='x', which='major', pad=7)
        axes.tick_params(axis='y', which='major', pad=8)
        axes.set_xlabel(r"$t$", labelpad = 8)
        axes.set_ylabel(r"$v_{\rm z}$", labelpad = 8)
        axes.locator_params(axis = 'y', nbins = 6)

        plt.show()

    def figCumulativevft(self, index_kf = -1):
        fig, axes = plt.subplots(1, 1, figsize = (9.2, 5.6))
        fig.subplots_adjust(left = 0.17, right = 0.81, bottom = 0.18, top = 0.95)

        line = axes.plot(self.t, np.cumsum( self.vft[2, index_kf, :] * exp( - self.tOverTauFunc(self.kft[:, index_kf,:], self.vft[:, index_kf,:]) ) ))
        plt.setp(line, ls ="-", c = 'k', lw = 3, marker = "", mfc = 'k', ms = 8, mec = "#7E2320", mew= 0)  # set properties

        axes.tick_params(axis='x', which='major', pad=7)
        axes.tick_params(axis='y', which='major', pad=8)
        axes.set_xlabel(r"$t$", labelpad = 8)
        axes.set_ylabel(r"$\sum_{\rm t}$ $v_{\rm z}(t)$$e^{\rm \dfrac{-t}{\tau}}$", labelpad = 8)

        axes.locator_params(axis = 'y', nbins = 6)

        plt.show()
        #//////////////////////////////////////////////////////////////////////////////#


# @jit(nopython=True)
# def optimized_tOverTauFunc(k, v, dt_array, gamma_0, gamma_dos, gamma_k, power):
#     phi = arctan2(k[1, :], k[0,:])
#     dos = 1 / sqrt(v[0, :]**2 + v[1,:]**2 + v[2,:]**2)
#     dos_norm = 0.006  # value to normalize the DOS to a quantity without units
#     # Integral from 0 to t of dt' / tau( k(t') ) or dt' * gamma( k(t') )
#     t_over_tau = np.cumsum(dt_array * (gamma_0 + gamma_dos *
#                                             dos / dos_norm + gamma_k * cos(2*phi)**power))
#     return t_over_tau


# @jit(nopython=True, parallel=True)
# def optimized_VelocitiesProduct(kft, vf, vft, dt, dt_array, gamma_0, gamma_dos, gamma_k, power, i, j):
#     """ Index i and j represent x, y, z = 0, 1, 2
#         for example, if i = 0: vif = vxf
#     """
#     ## Velocity components
#     vif  = vf[i,:]
#     vjft = vft[j,:,:]
#     v_product = np.empty(vif.shape[0], dtype = np.float64)
#     for i0 in prange(vif.shape[0]):
#         vj_sum_over_t = np.sum(vjft[i0, :] * \
#                         exp(- optimized_tOverTauFunc(kft[:, i0, :], vft[:, i0, :], dt_array, gamma_0, gamma_dos, gamma_k, power)) * dt)  # integral over t
#         v_product[i0] = vif[i0] * vj_sum_over_t
#     return v_product
