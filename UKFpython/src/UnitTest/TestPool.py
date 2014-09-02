'''
Created on Jul 7, 2014

@author: marco
'''
import unittest
import platform
import os
import pandas as pd
import numpy as np

from datetime import datetime
from FmuUtils import Model
from FmuUtils import FmuPool

class Test(unittest.TestCase):


    def setUp(self):
        """
        Initialize the class for testing the Model
        """
        # Assign an existing FMU to the model, depending on the platform identified
        dir_path = os.path.dirname(__file__)
        
        # Define the path of the FMU file
        if platform.architecture()[0]=="32bit":
            print "32-bit architecture"
            self.filePath = os.path.join(dir_path, "..","..", "modelica", "FmuExamples", "Resources", "FMUs", "FirstOrder.fmu")
        else:
            print "64-bit architecture"
            self.filePath = os.path.join(dir_path, "..","..", "modelica", "FmuExamples", "Resources", "FMUs", "FirstOrder_64bit.fmu")
            
        # Path of the CSV data
        self.csv_inputPath = os.path.join(dir_path, "..","..", "modelica", "FmuExamples", "Resources", "data", "SimulationData_FirstOrder.csv")


    def tearDown(self):
        pass


    def test_run_model_pool_data_series(self):
        """
        This function tests if the model can be run using a pool of processes when loading data form a pandas
        data series
        """
        
        # Initialize the FMU model empty
        m = Model.Model()
    
        # ReInit the model with the new FMU
        m.ReInit(self.filePath)
        
        # Create a pandas.Series for the input u
        ind = pd.date_range('2000-1-1', periods = 31, freq='s')
        ds = pd.Series(np.ones(31), index = ind)
        
        # Set the CSV file associated to the input
        inp = m.GetInputByName("u")
        inp.SetDataSeries(ds)
    
        # Set parameters a, b, c, d of the model
        par_a = m.GetVariableObject("a")
        m.SetReal(par_a, -1.0)
        par_b = m.GetVariableObject("b")
        m.SetReal(par_b, 4.0)
        par_c = m.GetVariableObject("c")
        m.SetReal(par_c, 6.0)
        par_d = m.GetVariableObject("d")
        m.SetReal(par_d, 0.0)
        
        # Select the states to be modified
        m.AddVariable(m.GetVariableObject("x"))
        
        # Initialize the model for the simulation
        m.InitializeSimulator()
        
        # Instantiate the pool
        pool = FmuPool.FmuPool(m, debug = False)

        # Define the vector of initial conditions for which the simulations
        # have to be performed.
        # values has to be a list of state vectors
        # values = [ [x0_0], [x0_1], ... [x0_n]]
        Nsims = 10
        vectorValues = np.linspace(1.0, 5.0, 10)
        values = []
        for v in vectorValues:
            temp = {"state":np.array([v]), "parameters":[]}
            values.append(temp)
    
        # Run simulations in parallel
        t0 = datetime(2000, 1, 1, 0, 0, 0)
        t1 = datetime(2000, 1, 1, 0, 0, 30)
        poolResults = pool.Run(values, start = t0, stop = t1)
        
        # Verify that the number of results is equal to the number of different initial conditions specified
        self.assertEqual(Nsims, len(poolResults), "The number of simulation results must be equal to the number of initial conditions specified")
        
        # For every result make sure that initial conditions have been set correctly
        # and the simulations converge to the exact final value
        i = 0
        for res in poolResults:
            
            # Get the results of a worker of the pool
            time, results = res[0]
            
            # Read the simulation time vector
            self.assertEqual(t0, time[0], "The initial time does not correspond")
            self.assertEqual(t1, time[-1], "The final time does not correspond")
            
            # Verify that the initial conditions were assigned correctly
            self.assertAlmostEqual(vectorValues[i], results["x"][0], 7, "The initial condition of the state \
            variable x is not %.8f but %.8f" % (results["x"][0], vectorValues[i]))
            
            # Read the results of the simulation
            # x' = -1*x + 4*u
            # y  = +6*x + 0*u
            # Given the input u = 1, at steady state
            # x ~ 4 and y ~ 24
            self.assertAlmostEqual(4.0, results["x"][-1], 3, "The steady state value of the \
            state variable x is not 4.0 but %.8f" % (results["x"][-1]))
            self.assertAlmostEqual(24.0, results["y"][-1], 2, "The steady state value of \
            the output variable y is not 24.0 but %.8f" % (results["y"][-1]))
            
            i += 1

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()