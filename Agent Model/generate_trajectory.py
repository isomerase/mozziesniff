"""
Created on Mon Mar 23 15:07:40 2015

@author: rkp, rbd

Generate "mosquito" trajectories (class object) using harmonic oscillator 
equations.
"""

import numpy as np
from numpy.linalg import norm
import matplotlib.pyplot as plt

## define params
m = 2.5e-6  # mass (kg) =2.6 mg


def random_force(f0, dim=2):
    """Generate random-direction force vector at each timestep from double-
    exponential distribution given exponent term f0.

    Args:
        f0: random force distribution exponent (float)

    Returns:
        random force x and y components (array)
    """
    if dim == 2:
        return np.random.laplace(0, f0, size=dim)
    else:
        raise NotImplementedError('Too many dimensions!')


def upwindBiasForce(wf0, upwind_direction=np.pi, dim=2):
    """Biases the agent to fly upwind. Constant push with strength wf0
    
    [formerly]: Picks the direction +- pi/2 rads from
    the upwind direction and scales it by accelList constant magnitude, "wf0".

    Args:
        wf0: bias distribution exponent
        upwind_direction: direction of upwind (in radians)

    Returns:
        upwind bias force x and y components as an array
    """
    if dim == 2:
        if wf0 == 0:
            return [0, 0]
        else:
            return [-wf0, 0]  # wf is constant, directly to left
    else:
        raise NotImplementedError('wind bias only works in 2D right now!')


def wall_force_field(current_pos, wallF, wallF_exp, wallX_pos=[0., 1.5], wallY_pos=[-0.5, 0.5]):  # TODO: make these the actual dims of Sharri's wind tunnel -rd
    """If agent gets too close to wall, inflict it with repulsive forces as a
    function of how close it is to the wall.
    
    Args:
        current_pos: (x,y) coords of agent right now (array)
        wallF: how scary the wall is (float)
        wallF_exp: the exponential term in the wall force field (float)
        wallX_pos: Wall X coords (array)
        wallY_pos: Wall Y coords (array)
    
    Returns:
        wall_force: (array)
    """
    pass

def stimulusDrivingForce():
    """[PLACEHOLDER]
    Force driving agegent towards stimulus source, determined by
    temperature-stimulus at the current position at the current time: b(timeList(x,timeList))

    TODO: Make two biased functions for this: accelList spatial-context dependent 
    bias (e.g. to drive mosquitos away from walls), and accelList temp 
    stimulus-dependent driving force.
    """
    pass


class Trajectory:
    """Generate single trajectory, forbidding agent from leaving bounds

    Args:
        r0: initial position (list/array)
        v0_stdev: stdev of initial velocity distribution (float)
        target_pos: source position (list/array) (set to None if no source)
        Tmax: max length of accelList trajectory (float)
        dt: length of timebins to divide Tmax by (float)
        k: spring constant, disabled (float)
        beta: damping force (kg/s) (float) NOTE: if beta is too big, things blow up
        f0: random driving force exp term for exp distribution (float)
        wf0: upwind bias force magnitude (float) # TODO units
        detect_thresh: distance mozzie can detect target (float) (m) =2 cm
        boundary: specify where walls are (float) (leftx, rightx, bottomy, topy)
        

    All args are in SI units and based on behavioral data:
    Tmax, dt: seconds (data: <control flight duration> = 4.4131 +- 4.4096
    

    Returns:
        trajectory object
    """
    def __init__(self, r0=[1., 0.], v0_stdev=0.01, Tmax=4., dt=0.01, target_pos=None, k=0., beta=2e-5, f0=3e-6, wf0=5e-6, detect_thresh=0.02, boundary=[0.0, 1.1, -0.05, 0.05], bounded=True, plotting = False):
        """ Initialize object with instant variables, and trigger other funcs. 
        """        
        self.Tmax = Tmax
        self.dt = dt
        self.v0_stdev = v0_stdev
        self.k = k
        self.beta = beta
        self.f0 = f0
        self.wf0 = wf0
        self.target_pos = target_pos
        self.dim = len(r0)  # get dimension
        
        self.target_found = False
        self.t_targfound = np.nan
        
        ## initialize all arrays
        ts_max = int(np.ceil(Tmax / dt))  # maximum time step
        self.timeList = np.arange(0, Tmax, dt)
        self.positionList = np.zeros((ts_max, self.dim), dtype=float)
        self.veloList = np.zeros((ts_max, self.dim), dtype=float)
        self.accelList = np.zeros((ts_max, self.dim), dtype=float)
        self.wallFList = np.zeros((ts_max, self.dim), dtype=float)
        
        # generate random intial velocity condition    
        v0 = np.random.normal(0, self.v0_stdev, self.dim)
    
        ## insert initial position and velocity into positionList,veloList arrays
        self.positionList[0] = r0
        self.veloList[0] = v0
        
        self.fly(ts_max, detect_thresh, boundary, bounded)
        
        if plotting is True:
            self.plot()
        
    def fly(self, ts_max, detect_thresh, boundary, bounded):
        """Run the simulation using Euler's method"""
        ## loop through timesteps
        for ts in range(ts_max-1):
            # calculate current force
            force = -self.k*self.positionList[ts] - self.beta*self.veloList[ts] + random_force(self.f0) + upwindBiasForce(self.wf0) #+ wall_force_field(self.positionList[ts])
            # calculate current acceleration
            self.accelList[ts] = force/m
    
            # update velocity in next timestep  # velo wall component not changed? -rd
            self.veloList[ts+1] = self.veloList[ts] + self.accelList[ts]*self.dt
            # update position in next timestep
            candidate_pos = self.positionList[ts] + self.veloList[ts+1]*self.dt  # why not use veloList[ts]? -rd
            
            if bounded is True:  # if walls are enabled
                ## forbid mosquito from going out of bounds
                # check x dim
                if candidate_pos[0] < boundary[0]:  # too far left
                    candidate_pos[0] = boundary[0] + 1e-3
                elif candidate_pos[0] > boundary[1]:  # too far right
                    candidate_pos[0] = boundary[1] - 1e-3
                # check y dim
                if candidate_pos[1] < boundary[2]:  # too far down
                    candidate_pos[1] = boundary[2] + 1e-3
                elif candidate_pos[1] > boundary[3]:  # too far up
                    candidate_pos[1] = boundary[3] - 1e-3
                
            self.positionList[ts+1] = candidate_pos
    
            # if there is a target, check if we are finding it
            if self.target_pos is None:
                self.target_found = False
                self.t_targfound = np.nan
            else:
                if norm(self.positionList[ts+1] - self.target_pos) < detect_thresh:
                # TODO: pretty sure norm is malfunctioning. only credible if
                #the trajectory is directly under the target -rd
                    self.target_found = True
                    self.t_targfound = self.timeList[ts]  # should this be timeList[ts+1]? -rd  
                    # trim excess timebins in arrays
                    self.timeList = self.timeList[:ts+1]
                    self.positionList = self.positionList[:ts+1]
                    self.veloList = self.veloList[:ts+1]
                    self.accelList = self.accelList[:ts+1]
                    break  # stop flying at source         
         
    def plot(self):
        plt.plot(self.positionList[:, 0], self.positionList[:, 1], lw=2, alpha=0.5)
        plt.scatter(self.target_pos[0], self.target_pos[1], s=150, c='r', marker="*")


if __name__ == '__main__':
    target_pos = [0.3, 0.03]
    mytraj = Trajectory(target_pos=target_pos, plotting = True)