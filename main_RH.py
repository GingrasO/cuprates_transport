import time
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, MultipleLocator, FormatStrFormatter

from band import BandStructure
from admr import ADMR
from chambers import Conductivity
##<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

e = 1.6e-19 # C
a = 3.74e-10 #m
c = 13.3e-10 # m

Bmin = 2
Bmax = 150
Bstep = 2
B_array = np.arange(Bmin, Bmax, Bstep)


t = 533.616
bandObject = BandStructure(t=t, mu=-693.7/t, tp=-113.561/t,
                           tpp=23.2192/t, tz=8.7296719/t, tz2=-0.89335299/t)

# condObject = Conductivity(bandObject, Bamp=45, Bphi=0, Btheta=0, gamma_0 = 25, gamma_k = 0, power = 0)
# condObject.solveMovementFunc()
# condObject.figOnekft()


# Data = np.vstack((bandObject.kf[0], bandObject.kf[1], bandObject.kf[2]))
# Data = Data.transpose()

# np.savetxt("FS_kx_ky_kz.dat", Data, fmt='%.7e',
# header = "kx\tky\tkz", comments = "#")

# bandObject.figMultipleFS2D()
# bandObject.figDiscretizeFS2D()

rhoxx_array = np.empty_like(B_array, dtype = np.float64)
rhoxy_array = np.empty_like(B_array, dtype = np.float64)
RH_array = np.empty_like(B_array, dtype = np.float64)
for i, B in enumerate(B_array):

    condObject = Conductivity(bandObject, Bamp=B, Bphi=0, Btheta=0, gamma_0=25, gamma_k=0, power=0)
    condObject.solveMovementFunc()
    condObject.chambersFunc(0, 0)
    condObject.chambersFunc(0, 1)
    sigma_xx = condObject.sigma[0,0]
    sigma_xy = condObject.sigma[0,1]

    rhoxx = sigma_xx / ( sigma_xx**2 + sigma_xy**2) # Ohm.m
    rhoxy = sigma_xy / ( sigma_xx**2 + sigma_xy**2) # Ohm.m
    RH = rhoxy / B # m^3/C

    rhoxx_array[i] = rhoxx
    rhoxy_array[i] = rhoxy
    RH_array[i] = RH

nH = 1 / ( RH_array[-1] * e )
d = c / 2
V = a**2 * d
n = V * np.abs(nH)
p = 1 - n
print("1 - n = ", np.round(p, 3) )

## Plot Parameters #################################

fig, axes = plt.subplots(1, 1, figsize = (9.2, 5.6)) # (1,1) means one plot, and figsize is w x h in inch of figure

fig.subplots_adjust(left = 0.18, right = 0.82, bottom = 0.18, top = 0.95) # adjust the box of axes regarding the figure size

axes.axhline(y=0, ls ="--", c ="k", linewidth=0.6)

#############################################
fig.text(0.79,0.86, r"$p$ = " + "{0:.3f}".format(bandObject.p), ha = "right")
fig.text(0.79,0.80, r"$1 - n$ = " + "{0:.3f}".format(p) , ha = "right")
#############################################

#############################################
axes.set_xlim(Bmin,Bmax)   # limit for xaxis
# axes.set_ylim(-3.5,1.2) # leave the ymax auto, but fix ymin
axes.set_xlabel(r"$H$ ( T )", labelpad = 8)
axes.set_ylabel(r"$R_{\rm H}$ ( mm$^3$ / C )", labelpad = 8)
#############################################

## Allow to shift the label ticks up or down with set_pad
for tick in axes.xaxis.get_major_ticks():
    tick.set_pad(7)
for tick in axes.yaxis.get_major_ticks():
    tick.set_pad(8)


line = axes.plot(B_array, RH_array * 1e9)
plt.setp(line, ls ="-", c = '#46FFA1', lw = 3, marker = "o", mfc = '#46FFA1', ms = 7, mec = '#46FFA1', mew= 0)
######################################################

######################################################
# plt.legend(loc = 0, fontsize = 12, frameon = False, numpoints=1, markerscale = 1, handletextpad=0.1)
######################################################


## Set ticks space and minor ticks space ############
#####################################################.

xtics = 30 # space between two ticks
mxtics = xtics / 2.  # space between two minor ticks
# ytics = 1
# mytics = ytics / 2. # or "AutoMinorLocator(2)" if ytics is not fixed, just put 1 minor tick per interval
majorFormatter = FormatStrFormatter('%g') # put the format of the number of ticks

axes.xaxis.set_major_locator(MultipleLocator(xtics))
axes.xaxis.set_major_formatter(majorFormatter)
axes.xaxis.set_minor_locator(MultipleLocator(mxtics))

# axes.yaxis.set_major_locator(MultipleLocator(ytics))
# axes.yaxis.set_major_formatter(majorFormatter)
# axes.yaxis.set_minor_locator(MultipleLocator(mytics))

######################################################

# script_name = os.path.basename(__file__)
# figurename = script_name[0:-3] + ".pdf"

plt.show()
# fig.savefig(figurename, bbox_inches = "tight")
# plt.close()



#///////////////////////////////////////////////////////////////////////////////
## Plot Parameters #################################

fig, axes = plt.subplots(1, 1, figsize = (9.2, 5.6)) # (1,1) means one plot, and figsize is w x h in inch of figure

fig.subplots_adjust(left = 0.18, right = 0.82, bottom = 0.18, top = 0.95) # adjust the box of axes regarding the figure size

axes.axhline(y=0, ls ="--", c ="k", linewidth=0.6)

#############################################
fig.text(0.79,0.86, r"$p$ = " + "{0:.3f}".format(bandObject.p), ha = "right")
fig.text(0.79,0.80, r"$1 - n$ = " + "{0:.3f}".format(p) , ha = "right")
#############################################

#############################################
axes.set_xlim(Bmin,Bmax)   # limit for xaxis
# axes.set_ylim(-3.5,1.2) # leave the ymax auto, but fix ymin
axes.set_xlabel(r"$H$ ( T )", labelpad = 8)
axes.set_ylabel(r"$\rho_{\rm xy}$ ( $\mu\Omega$ cm )", labelpad = 8)
#############################################

## Allow to shift the label ticks up or down with set_pad
for tick in axes.xaxis.get_major_ticks():
    tick.set_pad(7)
for tick in axes.yaxis.get_major_ticks():
    tick.set_pad(8)


line = axes.plot(B_array, rhoxy_array * 1e8)
plt.setp(line, ls ="-", c = '#DCB500', lw = 3, marker = "o", mfc = '#DCB500', ms = 7, mec = '#DCB500', mew= 0)
######################################################

######################################################
# plt.legend(loc = 0, fontsize = 12, frameon = False, numpoints=1, markerscale = 1, handletextpad=0.1)
######################################################


## Set ticks space and minor ticks space ############
#####################################################.

xtics = 30 # space between two ticks
mxtics = xtics / 2.  # space between two minor ticks
# ytics = 1
# mytics = ytics / 2. # or "AutoMinorLocator(2)" if ytics is not fixed, just put 1 minor tick per interval
majorFormatter = FormatStrFormatter('%g') # put the format of the number of ticks

axes.xaxis.set_major_locator(MultipleLocator(xtics))
axes.xaxis.set_major_formatter(majorFormatter)
axes.xaxis.set_minor_locator(MultipleLocator(mxtics))

# axes.yaxis.set_major_locator(MultipleLocator(ytics))
# axes.yaxis.set_major_formatter(majorFormatter)
# axes.yaxis.set_minor_locator(MultipleLocator(mytics))

######################################################

# script_name = os.path.basename(__file__)
# figurename = script_name[0:-3] + ".pdf"

plt.show()
# fig.savefig(figurename, bbox_inches = "tight")
# plt.close()


#///////////////////////////////////////////////////////////////////////////////
## Plot Parameters #################################

fig, axes = plt.subplots(1, 1, figsize = (9.2, 5.6)) # (1,1) means one plot, and figsize is w x h in inch of figure

fig.subplots_adjust(left = 0.18, right = 0.82, bottom = 0.18, top = 0.95) # adjust the box of axes regarding the figure size

#############################################
fig.text(0.79,0.28, r"$p$ = " + "{0:.3f}".format(bandObject.p), ha = "right")
fig.text(0.79,0.22, r"$1 - n$ = " + "{0:.3f}".format(p) , ha = "right")
#############################################

## Allow to shift the label ticks up or down with set_pad
for tick in axes.xaxis.get_major_ticks():
    tick.set_pad(7)
for tick in axes.yaxis.get_major_ticks():
    tick.set_pad(8)


line = axes.plot(B_array, rhoxx_array * 1e8)
plt.setp(line, ls ="-", c = '#5B22FF', lw = 3, marker = "o", mfc = '#5B22FF', ms = 7, mec = '#5B22FF', mew= 0)

#############################################
axes.set_xlim(Bmin,Bmax)   # limit for xaxis
axes.set_ylim(bottom = 0)
axes.set_xlabel(r"$H$ ( T )", labelpad = 8)
axes.set_ylabel(r"$\rho_{\rm xx}$ ( $\mu\Omega$ cm )", labelpad = 8)
#############################################

## Set ticks space and minor ticks space ############
#####################################################.

xtics = 30 # space between two ticks
mxtics = xtics / 2.  # space between two minor ticks
majorFormatter = FormatStrFormatter('%g') # put the format of the number of ticks

axes.xaxis.set_major_locator(MultipleLocator(xtics))
axes.xaxis.set_major_formatter(majorFormatter)
axes.xaxis.set_minor_locator(MultipleLocator(mxtics))
######################################################

# script_name = os.path.basename(__file__)
# figurename = script_name[0:-3] + ".pdf"

plt.show()
# fig.savefig(figurename, bbox_inches = "tight")
# plt.close()





