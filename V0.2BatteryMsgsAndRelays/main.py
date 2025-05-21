'''
Matthew Tuer, April 24, 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com

Shunt Truck V0.2

version notes:

-added all relays
logic for most relays has not been added

-reading BMS messages
highVBattEnab relay must be on to receive messages


'''

from mcp2515.canio import Message, RemoteTransmissionRequest
from mcp2515.config import spi, CS_PIN
from mcp2515 import MCP2515 as CAN
import gc
import time
from machine import Pin,UART
from Modbus.waveshareRelayModules import RelayTypeD
from otherFunctions.remoteLogic import calculateControls
from CanFunctions.NiMotionFunctions import packPositionData,unPackPostionFeedback
from CanFunctions.ctsBMS import unPackPowerLimits,unPackBMSInfoOne

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
airCompressor.off()
notUsed2.off()


#BMS Setup
powerDischargePeak=0
PowerDischargeContinue=0
PowerChargePeak=0
powerChargeContinue=0
BmsVolBat=0
BmsCurBat=0
BmsSoc=0



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




loopSpeedMS=25 #45ms=22.2 Hz
startTime = time.ticks_ms()/1000
lastSteeringUpdate=startTime

while 1:
    currentTime=time.ticks_ms()/1000
    
    
        
    if currentTime>=startTime:

        while RS485.any():
            #if there is data here find where is coming from and fix there!
            print("BAD DATA: %s" %(RS485.read()))
        
        
        #------relay card and remote logic-------
        if 	RelayCard.inputs[7]==1:
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
        packedData=packPositionData(turnSpeed)
        
        if previousTurnSpeed!=turnSpeed:
            CANSend(NiMotion,packedData)
        
        
        
        '''
        print("-------")
        print("controller error: %s" %controlErrorFlag)
        print("requested steering speed: %s" %turnSpeed)
        print("steering position:    %s" %feedBackSteeringPos)
        print("Speed: %s rpm" %toSendSpeed)
        print("Forward: %s" %forward)
        '''
        '''
        print("BMS PDP: %s" %powerDischargePeak)
        print("BMS PDC: %s" %PowerDischargeContinue)
        print("BMS PCP: %s" %PowerChargePeak)
        print("BMS PCC: %s" %powerChargeContinue)
        
        print("BMS volbat: %s" %BmsVolBat)
        print("BMS curBat: %s" %BmsCurBat)
        print("BMS SOC: %s" %BmsSoc)
        '''
        
        
        
    
       
        
        CANSend(NiMotion,feedbackPosition)#requesting feedback position from steering motor
        CANReceive()
        RelayCard.updateInputs()
        RelayCard.flipRelays()
        endTime = time.ticks_ms()/1000
        computeTime=(endTime-currentTime)*1000
        extraTime=(loopSpeedMS/1000-computeTime/1000)
        startTime=endTime+extraTime
        print("ComputeTime:%sms" %computeTime)
        
        
    



