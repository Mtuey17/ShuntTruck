'''
Matthew Tuer, April 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com
'''
from utime import sleep


def TM4Bootup(operationRequest,operationalMode,RPM,TM4Init,highPowerVoltage,prechargeVoltageMet,driveMotorInit):
    
    requiredPrechargeVoltage=250 #V
    prechargeVoltageMet=False
    
    if highPowerVoltage>=requiredPrechargeVoltage:
        prechargeVoltageMet=True 
        
    if not prechargeVoltageMet:
        TM4init=False
        operationRequest=0
        RPM=0
        driveMotorInit=1      
    else:
    
        if driveMotorInit<100:
            operationRequest=0
            RPM=0
        elif driveMotorInit<150:
            operationRequest=1
            RPM=0
            #print("tm4 init 2")
        elif driveMotorInit<200:
            operationalMode=3
            RPM=0
            #print("tm4 init 3")
        else:
            TM4Init=True
        if not TM4Init:
            driveMotorInit+=1
    return TM4Init,prechargeVoltageMet,driveMotorInit,operationRequest,operationalMode,RPM

def packCommandSafety(safetyRPM,rollingCount,refCommandMode=2):
    
    
    offset=32767
    refSpeed=offset+safetyRPM
    
    
    SpeedBytes=[refSpeed & 0xFF ,(refSpeed >> 8) & 0xFF]
    ModeCountByte= ((rollingCount & 0xF) << 4) | (refCommandMode & 0x3)
    packed=[0x00,0x00,SpeedBytes[0],SpeedBytes[1],ModeCountByte]
    toSend=bytearray(packed)
    return toSend

def unpackMCUInfo1(payload):
    
    try:
        auxVoltage=(payload[0]&0xFF)*0.25
        Data=payload[1]|(payload[2]<<8)
        highPowerVoltage=Data&0x7FF
        return highPowerVoltage
    except:
        print("TM4 error unpacking info1")
        return 0
    
def packCommandOne(operationRequest,MaxChargeCurrent,maxDischargeCurrent,MaxBatteryVoltage,minBatteryVoltage,rollingCount,
                   minBatterVoltageStatus=0,maxDischargeCurrentStatus=0,maxChargeCurrentStatus=0,maxbatteryVoltageStatus=0):
        #bytes 0 and 1
    maxChargeAndOperaytion=(((operationRequest*2) & 0x3) << 12) | (MaxChargeCurrent & 0xFFF)
    maxChargeAndOperaytion=[maxChargeAndOperaytion & 0xFF,(maxChargeAndOperaytion >> 8) & 0xFF]

    #bytes 2 and 3
    dischargeCurrentByte=[maxDischargeCurrent & 0xFF,(maxDischargeCurrent >> 8) & 0xF]

    #bytes 4 and 5
    statusBit=((maxDischargeCurrentStatus)|(maxbatteryVoltageStatus<<1)|(minBatterVoltageStatus<<2)|(maxChargeCurrentStatus<<3))
    StatusandMaxVoltage=((statusBit & 0xF) << 12) | (MaxBatteryVoltage & 0xFFF)
    StatusandMaxVoltage=[StatusandMaxVoltage & 0xFF,(StatusandMaxVoltage >> 8) & 0xFF]

    #bytes 6 and 7
    #mask term with number of bits that term is. shift however many bits the next term is, repeate 
    CountandMinVoltage = ((rollingCount & 0xF) << 12) | (minBatteryVoltage & 0xFFF)
    CountandMinVoltage = [CountandMinVoltage & 0xFF,(CountandMinVoltage >> 8) & 0xFF]

    packed=[maxChargeAndOperaytion[0],maxChargeAndOperaytion[1],dischargeCurrentByte[0],dischargeCurrentByte[1],
            StatusandMaxVoltage[0],StatusandMaxVoltage[1],CountandMinVoltage[0],CountandMinVoltage[1]]
    toSend=bytearray(packed)
    return toSend

def packCommandTwo(operationalMode,commandMode,speedCommandStatus,RPM,rollingCount):
    offset=32767
  
    speedCommand=offset+RPM
    byteOne = ((operationalMode & 0x7) << 0) | \
             ((commandMode & 0x3) << 3) | \
             ((speedCommandStatus & 0x1) << 5)
    


    
    
    byteTwo=0x00 #not used when in speed mode (commandMode=2)
    byteThree=0x00 #also not used wehn in speed mode

    byteFourFive=[speedCommand&0xFF,(speedCommand>>8)&0xFF]
   

    byteSix=[(rollingCount&0xF)<<4]
    
    
    packed=[byteOne,byteTwo,byteThree,byteFourFive[0],byteFourFive[1],byteSix[0]]
    toSend=bytearray(packed)
    return toSend
    
    
    
    
    
    
    
    
    
