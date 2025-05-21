'''
Matthew Tuer, April 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com
'''

#doesnt really need to be a function/ in a seperate file, but wanting to keep the same format as the other CAN devices 
def packPositionData(pos):
    toBytes=[(pos>>24)&0xFF,(pos>>16)&0xFF, (pos>>8)&0xFF, pos&0xFF]
    packedData=[0x23,0xFF,0x60,0x00,toBytes[3],toBytes[2],toBytes[1],toBytes[0]]
    return packedData

def unPackPostionFeedback(payload):
    data=payload[4]|payload[5]<<8|payload[6]<<16|payload[7]<<24
    if data >= 2**31:  # If the value is greater than max positive int32
        data -= 2**32  
    return data
        
    
  