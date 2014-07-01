'''
Created on Nov 6, 2013

@author: marco
'''
import numpy
from CsvReader import CsvReader
import Strings
import pyfmi

class InOutVar():
    """
    This class either represent an input or output variable.
    Both are variable with associated a data series contained in a .csv file
    """
    
    def __init__(self, object = None):
        """
        Initialization method. This constructor defines the object (PyFmiVariable) that contains the
        information about the variable, the CsvReader class associated to the input (that contains the data), 
        a dictionary called dataSeries = {"time": [], "data": []} that contains the two arrays that represent
        the data series (that are read from the csv file).
        The integer index is used when the data values are read using the function ReadFromDataSeries, while
        cov is the covariance associated to the data series.
        """
        self.object = object
        self.CsvReader = CsvReader()
        self.dataSeries = {}
        self.index = 0
        self.cov = 1.0
        self.measOut = False
    
    def ReadValueInFMU(self, fmu):
        """
        Given an FMU model, this method reads the value of the variable/parameter
        """
        type = self.object.type
        if type == pyfmi.fmi.FMI_REAL:
            val = fmu.get_real(self.object.value_reference)
        elif type == pyfmi.fmi.FMI_INTEGER:
            val = fmu.get_integer(self.object.value_reference)
        elif type == pyfmi.fmi.FMI_BOOLEAN:
            val = fmu.get_boolean(self.object.value_reference)
        elif type == pyfmi.fmi.FMI_ENUMERATION:
            val = fmu.get_int(self.object.value_reference)
        elif type == pyfmi.fmi.FMI_STRING:
            val = fmu.get_string(self.object.value_reference)
        else:
            print "OnSelChanged::FMU-EXCEPTION :: The type is not known"
            return None
        return val[0]
    
    def SetMeasuredOutput(self, flag = True):
        self.measOut = flag
    
    def IsMeasuredOutput(self):
        return self.measOut
    
    def SetCovariance(self, cov):
        if cov > 0.0:
            self.cov = cov
            return True
        else:
            print "The covariance must be positive"
            self.cov = cov
            return False
    
    def GetCovariance(self):
        """
        This method returns the covariance of the variable
        """
        return self.cov
     
    def SetObject(self, object):
        """
        Set the object <<pyfmi.ScalarVariable>> associated to the input/output
        """
        self.object = object
        
    def GetObject(self):
        """
        Get the object <<pyfmi.ScalarVariable>> associated to the input/output
        """
        return self.object
    
    def SetCsvReader(self, reader):
        """
        Set the CsvReader class associated to the input/output
        """
        self.CsvReader = reader
        
    def GetCsvReader(self):
        """
        Get the CsvReader class associated to the input/output
        """
        return self.CsvReader
    
    def ReadDataSeries(self):
        """
        This method reads the data series contained in the CSV file
        """
        self.dataSeries = self.CsvReader.GetDataSeries()
        if self.dataSeries == {}:
            return False
        else:
            return True
        
    def GetDataSeries(self):
        """
        This method returns the data series read from the csv file
        """
        return self.dataSeries
    
    def SetDataSeries(self, time, data):
        """
        This function sets a data series instead of reading it from the CSV file
        """
        self.dataSeries[Strings.TIME_STRING] = numpy.array(time).astype(numpy.float)
        self.dataSeries[Strings.DATA_STRING] = numpy.matrix(data).astype(numpy.float)
        
    def ReadFromDataSeries(self, t):
        """
        This function returns the value of the data series at the given time. It performs a linear interpolation between the points
        """
        time = self.dataSeries[Strings.TIME_STRING]
        data = numpy.squeeze(numpy.asarray(self.dataSeries[Strings.DATA_STRING]))
        
        
        if t < time[0] or t > time[-1]:
            #print "Time t="+str(t)+" is outside the range of the data series ["+str(time[0])+","+str(time[1])+"]"
            return False
        else:
            # identify the position of the time closest time steps
            # Since it is a sequential access, store the last position to reduce the access time for the next iteration
            index = self.index
            N = len(time)
            
            # if len(time) = 10 and index was 2, indexes is [2, 3, 4, 5, 6, 7, 8, 9, 0, 1]
            indexes = numpy.concatenate((numpy.arange(index,N), numpy.arange(index+1)))
            
            
            #print "\n========="
            #print "Indexes = ",indexes
            for i in range(N):
                j = indexes[i]
                #print "j=",j
                T_a = time[indexes[i]]
                T_b = time[indexes[i+1]]
                T_0 = min(T_a, T_b)
                T_1 = max(T_a, T_b)
                #print "time ",t," and [",T_0,",",T_1,"]"
                
                if j!=N-1 and t >= T_0 and t <= T_1:
                    break
                
                j += 1
            
            
            if j < N-1: 
                index_0 = indexes[j]
                index_1 = indexes[j+1]
            else:
                index_1 = indexes[j]
                index_0 = indexes[j-1]
            
            
            deltaT = time[index_1] - time[index_0]
            dT0 = t - time[index_0]
            dT1 = time[index_1] - t
            interpData = (dT0*data[index_1] + dT1*data[index_0])/deltaT
            
            # save the index
            self.index = j
            
            return interpData

if __name__ == "__main__":
    
    var = InOutVar()
    timeSeries = numpy.linspace(0.0, 20.0, 5)
    dataSeries = numpy.linspace(0.0, 20.0, 5)
    
    var.SetDataSeries(timeSeries, dataSeries)
    print var.ReadFromDataSeries(0)
    print var.ReadFromDataSeries(0.1)
    print var.ReadFromDataSeries(0.5)
    print var.ReadFromDataSeries(0.7)
    print var.ReadFromDataSeries(5.0)
    print var.ReadFromDataSeries(5.1)
    print var.ReadFromDataSeries(5.6)
    print var.ReadFromDataSeries(8.6)
    print var.ReadFromDataSeries(10.6)
    print var.ReadFromDataSeries(11.6)
    print var.ReadFromDataSeries(5.6)
    print var.ReadFromDataSeries(17.6)
    print var.ReadFromDataSeries(0.6)