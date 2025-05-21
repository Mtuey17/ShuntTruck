'''
Matthew Tuer, April 24, 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com

Shunt Truck V0.3

version notes:

-added timers from hydraulic truck
hardware interupt for sending CAN
timer for reading pressure sensors
timer for prints

-added pressure sensors



'''

from mcp2515.canio import Message, RemoteTransmissionRequest
from mcp2515.config import spi, CS_PIN
from mcp2515 import MCP2515 as CAN
import gc
import time
import machine
from machine import Pin,UART,ADC
from Modbus.waveshareRelayModules import RelayTypeD
from otherFunctions.remoteLogic import calculateControls
from CanFunctions.NiMotionFunctions import packPositionData,unPackPostionFeedback
from CanFunctions.ctsBMS import unPackPowerLimits,unPackBMSInfoOne
from analogSensors.pressureSensor import PT05,PT010

def CANReceive():
    global powerDischargePeak,PowerDischargeContinue,PowerChargePeak,powerChargeContinue
    global BmsVolBat,BmsCurBat,BmsSoc
    global feedBackSteeringPos
    with can_bus.listen(timeout=0.005) as listener:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg = listener.receive()
            if not isinstance(msg,Message):
                continue
                 
            #CAN messages work weird for Nimotion motor, cant just go by ID 
            if msg.id==1409 and hex(msg.data[0])=="0x43" and hex(msg.data[1])=="0x64" and hex(msg.data[2])=="0x60":
                feedBackSteeringPos=unPackPostionFeedback(msg.data)
            if hex(msg.id)=="0x1e1":#BMS Info 1 message
                
                BmsVolBat,BmsCurBat,BmsSoc=unPackBMSInfoOne(msg.data,debug=False)
                   
            if hex(msg.id)=="0x1f3":# BMSpower limits 
                powerDischargePeak,PowerDischargeContinue,PowerChargePeak,powerChargeContinue=unPackPowerLimits(msg.data,debug=False)

            

def sendCanMessages(timer):
    global previousTurnSpeed,turnSpeed,NiMotion#steering variables
    if previousTurnSpeed!=turnSpeed:
        packedData=packPositionData(turnSpeed)
        CANSend(NiMotion,packedData)    
    CANSend(NiMotion,feedbackPosition)#requesting feedback position from steering motor
    
                
def CANSend(messageinfo,data):
    toSend=bytearray(data)
    message = Message(id=messageinfo, data=toSend, extended=False)
    send_success = can_bus.send(message)
#------------------------------------------------------------------------
    
    
#init Canbus 
can_bus = CAN(spi, CS_PIN,baudrate=250_000, loopback=False, silent=False)


#------init for NiMotion motor (steering)-------
motorID=0x601
NiMotion=motorID
feedbackPosition=[0x40,0x64,0x60,0x00,0x00,0x00,0x00,0x00]
accelTimeMs=[0x23,0x83,0x60,0x00,0x75,0x30,0x00,0x00]
deAccelTimeMs=[0x23,0x84,0x60,0x00,0xEA,0x60,0x00,0x00]
initialSpeed=[0x23,0x08,0x20,0x00,0x0A,0x00,0x00,0x00]
ProfileVelocityMode=[0x2F,0x60,0x60,0x00,0x03,0x00,0x00,0x00]#turn to velocity mode
init1=[0x2B,0x40,0x60,0x00,0x00,0x00,0x00,0x00]
init2=[0x2B,0x40,0x60,0x00,0x06,0x00,0x00,0x00]#switch driver state machine 1
init3=[0x2B,0x40,0x60,0x00,0x07,0x00,0x00,0x00]#switch driver state machine 2
init4=[0x2B,0x40,0x60,0x00,0x0F,0x00,0x00,0x00]#switch driver state machine 4
CANSend(NiMotion,init1)
CANSend(NiMotion,accelTimeMs)
CANSend(NiMotion,deAccelTimeMs)
CANSend(NiMotion,initialSpeed)
CANSend(NiMotion,ProfileVelocityMode)
CANSend(NiMotion,init2)
CANSend(NiMotion,init3)
CANSend(NiMotion,init4)


#init relays
RS485=UART(1, baudrate=256000, tx=17, rx=18)
#Waveshare Relays
RelayCard=RelayTypeD(RS485,0x01)#will not change address if you set it to the wrong one
RelayCard.fanAndPump=0
RelayCard.remoteSignal=1
RelayCard.brakesOff=0
RelayCard.dumpAirDryer=0


#ESP relays
airDryer=Pin(1, Pin.OUT)#relay1
notUsed=Pin(2,Pin.OUT)#relay2
steeringPump=Pin(41, Pin.OUT)#relay3
highVBattEnab=Pin(42, Pin.OUT)#relay4
airCompressor=Pin(45,Pin.OUT)#relay5
notUsed2=Pin(46, Pin.OUT)#relay6
airDryer.off()
notUsed.off()
steeringPump.off()
highVBattEnab.off()
notUsed2.off()
time.sleep(2)


#BMS Setup
powerDischargePeak=0
PowerDischargeContinue=0
PowerChargePeak=0
powerChargeContinue=0
BmsVolBat=0
BmsCurBat=0
BmsSoc=0


#pressure sensor setup
rearTank=PT05(6)#0-5V sensor 
frontTank=PT010(7)#0-10V sensor 


#----variables for Remote and steering------
turnSpeed=0
feedBackSteeringPos=0
speedCount=0
toSendSpeed=0
previousTurnSpeed=0
forward=False
controlErrorFlag=False
pumpDelay=False
pumpDelayTimer=0
pumpDelayMs=500


#-------Timing-----------
#hardware interupt for sending CAN messages at same time interval
timer1 = machine.Timer(0)
timer1.init(period=20, mode=machine.Timer.PERIODIC, callback=sendCanMessages) #was 20
loopSpeedMS=30 #45ms=22.2 Hz


#print timer 
updatePrints=0
updatRate=0.5 #second(s)
updateInterval=int(1/(loopSpeedMS/1000)*updatRate)


#sensor timer 
updateSensors=0
sensorUpdatRate=0.2 #second(s)
sensorUpdateInterval=int(1/(loopSpeedMS/1000)*sensorUpdatRate)


startTime = time.ticks_ms()/1000
lastSteeringUpdate=startTime

while 1:
    currentTime=time.ticks_ms()/1000
    
    
    if currentTime>=startTime:

        while RS485.any():
            #if there is data here find where is coming from and fix there!
            print("BAD DATA: %s" %(RS485.read()))
        
    
        #---TEST turning on air compressor with button 7---
        if RelayCard.inputs[6]==1:
            airCompressor.on()
        else:
            airCompressor.off()
        
        
        #------relay card and remote logic-------

        #highVBattEnab.on()
        if RelayCard.inputs[7]==1:
            controlErrorFlag=True
            speedCount=0
            toSendSpeed=0
        else:
            controlErrorFlag=False
            previousTurnSpeed=turnSpeed
            turnSpeed,speedCount,toSendSpeed,forward=calculateControls(RelayCard.inputs,feedBackSteeringPos,speedCount)
            
            
            
        #-------steering logic---------
        #keeping pump on 500ms after requesting 0 speed 
        if (abs(previousTurnSpeed)>0 and turnSpeed==0):
            pumpDelay=True
            pumpDelayTimer=time.ticks_ms()/1000
        if time.ticks_ms()/1000>pumpDelayTimer+((pumpDelayMs)/1000):
            pumpDelay=False    
        if turnSpeed!=0 or pumpDelay:
            steeringPump.on()
        else:
            steeringPump.off()
        
        
        #-------Sensor Logic--------
        updateSensors+=1
        if updateSensors==sensorUpdateInterval:
            rearTank.read()
            frontTank.read()
            updateSensors=0
            
        
        #-----------Prints---------------
        updatePrints+=1
        if updatePrints==updateInterval:
            steeringMessages=False
            bmsMessages=False
            analogSensorMessages=True
            
            if steeringMessages:
                print("-------Steering Messages-------")
                print("controller error: %s" %controlErrorFlag)
                print("requested steering speed: %s" %turnSpeed)
                print("steering position:    %s" %feedBackSteeringPos)
                print("Speed: %s rpm" %toSendSpeed)
                print("Forward: %s" %forward)
                print(" ")
            if bmsMessages:
                print("---------BMS Messages----------")
                print("BMS PDP: %s" %powerDischargePeak) #to tm4?
                print("BMS PDC: %s" %PowerDischargeContinue)
                print("BMS PCP: %s" %PowerChargePeak)#to tm4?
                print("BMS PCC: %s" %powerChargeContinue)
                print("Battery Voltage: %s" %BmsVolBat)
                print("Battery curBat: %s" %BmsCurBat)
                print("Battery SOC: %s" %BmsSoc)
                print(" ")
            if analogSensorMessages:
                print("---------Sensor Messages----------")
                print("Rear Tank: %s PSI" %rearTank.pressurePSI)
                print("Front Tank: %s PSI" %frontTank.pressurePSI) 
                print(" ")
                
            print("ComputeTime:%sms" %computeTime)
            updatePrints=0
            
             
        
        
        CANReceive()
        RelayCard.updateInputs()
        RelayCard.flipRelays()
        
        
        
        endTime = time.ticks_ms()/1000
        computeTime=(endTime-currentTime)*1000
        extraTime=(loopSpeedMS/1000-computeTime/1000)
        startTime=endTime+extraTime
        
        
        
    



