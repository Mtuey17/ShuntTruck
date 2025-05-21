'''
Matthew Tuer, April 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com
'''
import time 
import machine
from machine import ADC




class PT05:
    def __init__(self,adcPin=None):
        self.errorHistory=[]
        if adcPin==None:
            print("\033[93mWARNING 310: No ADC pin specified! Assuming pin 6\033[0m")
            #self.errorHistory.append(310)
            adcPin=6  
        self.ADC=ADC(adcPin)
        self.ADC.width(machine.ADC.WIDTH_12BIT)
        self.ADC.atten(ADC.ATTN_11DB)
        self.pressurePSI=0
        self.pressureMPA=0
        self.maxPinReading=3.33
        self.maxAdcReading=4095
        self.maxSensorPressureReading=4
        self.maxVoltage=3.119
        self.conversionFactor=int((self.maxVoltage/self.maxPinReading)*self.maxAdcReading)
            
    def read(self):
        analogValue=self.ADC.read()
        self.pressureMPA=(analogValue/self.conversionFactor)*self.maxSensorPressureReading
        self.pressurePSI=self.pressureMPA*145.038
        return self.pressurePSI
    


class PT010:
    def __init__(self,adcPin=None):
        self.errorHistory=[]
        if adcPin==None:
            print("\033[93mWARNING 310: No ADC pin specified! Assuming pin 7\033[0m")
            #self.errorHistory.append(310)
            adcPin=7  
        self.ADC=ADC(adcPin)
        self.ADC.width(machine.ADC.WIDTH_12BIT)
        self.ADC.atten(ADC.ATTN_11DB)
        self.Pressure=0
        self.pressurePSI=0
        self.maxPinReading=3.33
        self.maxAdcReading=4095
        self.maxSensorPressureReading=300
        self.maxVoltage=3.12
        self.conversionFactor=int((self.maxVoltage/self.maxPinReading)*self.maxAdcReading)
        
    def read(self):
        analogValue=self.ADC.read()
        self.pressurePSI=(analogValue/self.conversionFactor)*self.maxSensorPressureReading
        return self.pressurePSI
    

        
     
    
        
    
        
        
