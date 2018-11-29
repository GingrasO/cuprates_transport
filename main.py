import time

from numpy import pi
from band import BandStructure, Pocket
from admr import ADMR
from chambers import Conductivity
##<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#


## CLASSIC Bandstructure //////////////////////////////////////////////////////#
bandObject = BandStructure(mu = -0.825)
# bandObject.setMuToDoping(0.21)
bandObject.discretize_FS()
bandObject.densityOfState()
bandObject.doping()
# bandObject.figMultipleFS2D()

condObject = Conductivity(bandObject, Bamp=45, gamma_0=15, gamma_k=65, power=12, a0=0)


start_total_time = time.time()
ADMRObject = ADMR(condObject)
ADMRObject.runADMR()
print("ADMR time : %.6s seconds" % (time.time() - start_total_time))

ADMRObject.fileADMR()
ADMRObject.figADMR()


## AF reconstruction //////////////////////////////////////////////////////////#
# holePkt = Pocket()
# holePkt.discretize_FS()
# holePkt.densityOfState()
# holePkt.doping()
# dataPoint = Conductivity(holePkt, 45, 0, 0)#, gamma_0=15, gamma_k=65, power=12, a0=0)
# dataPoint.solveMovementFunc()
# dataPoint.figOnekft()


# bandObject = BandStructure(mu = -0.825)
# # bandObject.setMuToDoping(0.21)
# bandObject.discretize_FS()
# bandObject.densityOfState()
# bandObject.doping()
# # bandObject.figMultipleFS2D()


# start_total_time = time.time()
# ADMRObject = ADMR(bandObject, Bamp=45, gamma_0=15, gamma_k=65, power=12, a0=0)
# ADMRObject.runADMR()
# print("ADMR time : %.6s seconds" % (time.time() - start_total_time))

# ADMRObject.fileADMR()
# ADMRObject.figADMR()

# # bandObject2 = BandStructure()
# bandObject2 = Pocket(M=0.8)
# bandObject2.mu=-0.9
# bandObject2.mesh_ds=pi/20
# # bandObject2.electronPocket=True
# bandObject2.doping()
# bandObject2.discretize_FS()
# bandObject2.densityOfState()
# # bandObject2.figMultipleFS2D()

# start_total_time = time.time()
# ADMRObject2 = ADMR(bandObject2, Bamp=45, gamma_0=50, gamma_k=0, power=12, a0=0)
# ADMRObject2.runADMR()
# print("ADMR time : %.6s seconds" % (time.time() - start_total_time))

# ADMRObject2.fileADMR()
# ADMRObject2.figADMR()









