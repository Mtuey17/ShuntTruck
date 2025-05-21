'''
Matthew Tuer, April 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com
'''
from utime import sleep



def unPackPowerLimits(payload, debug=False):
    BMSPowerLimits=[0,0,0,0]
    Byte=0
    index=0
    if debug:
        print("Raw data:%s" %payload)
        print("Data length:%s" %len(payload))
    
    while index!=len(BMSPowerLimits):
        BMSPowerLimits[index]=((payload[Byte] << 8) | payload[(Byte+1)])*0.1
        index+=1
        Byte+=2
    return BMSPowerLimits[0],BMSPowerLimits[1],BMSPowerLimits[2],BMSPowerLimits[3]


def unPackBMSInfoOne(payload, debug=False):
    offset=-1000
    BMSInfoOne=[0,0,0]
    Byte=0
    index=0
    if debug:
        print("Raw data:%s" %payload)
        print("Data length:%s" %len(payload))
    
    while index!=len(BMSInfoOne):
        BMSInfoOne[index]=((payload[Byte] << 8) | payload[(Byte+1)])*0.1
        index+=1
        Byte+=2
    return BMSInfoOne[0],offset+BMSInfoOne[1],BMSInfoOne[2]

'''
backup shiiiit
BMSPowerLimits=[0,0,0,0]
PLData=bytearray(b'\t\xc4\x00\x00\x00\xc8\x00\xc8')
powerDischargePeak= ((PLData[0] << 8) | PLData[1])*0.1
print("powerDischargePeak:%s"%powerDischargePeak)
PowerDischargeContinue= ((PLData[2] << 8) | PLData[3])*0.1
print("powerDischargePeak:%s"%PowerDischargeContinue)
PowerChargePeak= ((PLData[4] << 8) | PLData[5])*0.1
print("PowerChargePeak:%s"%PowerChargePeak)
powerChargeContinue= ((PLData[6] << 8) | PLData[7])*0.1
print("powerChargeContinue:%s"%powerChargeContinue)
Byte=0
index=0
while index!=len(BMSPowerLimits):
    BMSPowerLimits[index]=((PLData[Byte] << 8) | PLData[(Byte+1)])*0.1
    index+=1
    Byte+=2
print(BMSPowerLimits)




'''