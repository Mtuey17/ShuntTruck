'''
Matthew Tuer, April 2025
mtuer@uwaterloo.ca/matthewjtuer@gmail.com
'''
import time

def crc16(data):
        crc = 0xFFFF
        for c in data:
            crc = crc ^ c
            for j in range(8):
                if (crc & 1) == 0:
                    crc = crc >> 1
                else:
                    crc = crc >> 1
                    crc = crc ^ 0xA001
        return crc


class RelayTypeD:
    def __init__(self,Port,id=None,shuntTruckLayout=True):
        if id==None:
            print("No Modbus ID specified! assuming 0x01")
            id=0x01
            
        self.id=id
        self.serial=Port
        self.inputs=[0,0,0,0,0,0,0,0]
        
        if shuntTruckLayout:
            self.shuntTruckLayout=True
            self.fanAndPump=0
            self.remoteSignal=0
            self.brakesOff=0
            self.dumpAirDryer=0
            self.notUsed1=0
            self.notUsed2=0
            self.notUsed3=0
            self.notUsed4=0
            self.relays=[self.fanAndPump,self.remoteSignal,self.brakesOff,self.dumpAirDryer,self.notUsed1,self.notUsed2,self.notUsed3,self.notUsed4]
        else:
            self.relays=[0,0,0,0,0,0,0,0]
        
        
        self.previousRelays=[1,1,1,1,1,1,1,1]
        self.flipRelays()

    
    def flipRelays(self, debug=False):
        #could check responses to verify each relay is in correct state
        if self.shuntTruckLayout:
            self.relays=[self.fanAndPump,self.remoteSignal,self.brakesOff,self.dumpAirDryer,self.notUsed1,self.notUsed2,self.notUsed3,self.notUsed4]
            
        i=0
        time.sleep(0.002)
        while i!=8:
            if debug:
                    print("cur %s: prev: %s"%(self.relays[i],self.previousRelays[i]))
            if self.relays[i]!=self.previousRelays[i]:
                relay=i
                if self.relays[i]:
                    flip=[self.id,0x05,0x00,relay,0xFF,0x00]
                else:
                    flip=[self.id,0x05,0x00,relay,0x00,0x00]
                if debug:
                    print("relay %s: %s"%(relay,flip[4]))
                crc=crc16(flip)
                highCRC = bytes([((crc>>8)& 0xff)])
                lowCRC = bytes([(crc)& 0xff])
                self.serial.write(bytes(flip)+lowCRC+highCRC)
                time.sleep(0.002)
            i+=1             
        self.previousRelays=self.relays.copy()#make sure it refers to a copy of self.relays!!
        #cleaning up serial buffer 
        while self.serial.any():
            self.serial.read(1)
        '''
        --------why do we need the .copy?--------
        so we dont have to re define the list every time we modify a relay status.
        ex, 
        self.previousRelays=self.relays
        this means that both lists point to the same place in memory 
        when one list is updated, the other automatically is aswell  
        
        RelayCardOne.relays=[0,0,0,0,0,1,0,0]
        this worked since you are completely redefining the list! it gets a new spot in memory that
        the other list has no refrence to!
            
        RelayCardOne.relays[5]= 1
        on the other hand this is modifying the existing list, so its place in memory is the same!
        this means the other list will see the change aswell since it has a refrence to that memory location!
        '''
        
        

    def updateInputs(self,timeoutms=10):
        readInputs=[self.id,0x02,0x00,0x00,0x00,0x08]
        crc=crc16(readInputs)
        highCRC = bytes([((crc>>8)& 0xff)])
        lowCRC = bytes([(crc)& 0xff])
        self.serial.write(bytes(readInputs)+lowCRC+highCRC)
        time.sleep(0.003)
        startTime=time.ticks_ms()
        while self.serial.any()==0:
            if (time.ticks_ms())>startTime+timeoutms:
                self.inputs=[0,0,0,0,0,0,0,1]
                return 
                
            
            wait=1
        payload=bytearray(self.serial.read(7))
        #print(payload.hex())
        inputData=payload[3]
     
        
        i=0
        while i!=8:
            self.inputs[i]=(inputData>>i)&0x01
            i+=1
       
       
       
       
    def setAddress(self,ID):
        self.id=ID
        setAddress=[0x00,0x06,0x40,0x00,0x00,self.id]
        crc=crc16(setAddress)
        highCRC = bytes([((crc>>8)& 0xff)])
        lowCRC = bytes([(crc)& 0xff])
        self.serial.write(bytes(setAddress)+lowCRC+highCRC)
        time.sleep(0.005)
        
        print("device address set to %s" %self.id)
    
    
    
    def setbaud(self, baudrate=0x05):
        '''
        0x00: 4800
        0x01: 9600
        0x02: 19200
        0x03: 38400
        0x04: 57600
        0x05: 115200
        0x06: 128000
        0x07: 256000
        '''
        setBaud=[0x00,0x06,0x20,0x00,0x00,baudrate]
        crc=crc16(setBaud)
        highCRC = bytes([((crc>>8)& 0xff)])
        lowCRC = bytes([(crc)& 0xff])
        self.serial.write(bytes(setBaud)+lowCRC+highCRC)
        print("baud set!")
        
     
    def findAddress(self):#not working :( doesnt really matter tho
        readAddress=[0x00,0x03,0x40,0x00,0x00,0x01,0x90,0x1B]
        self.serial.write(bytes(readAddress))
        time.sleep(0.005)
        while self.serial.any()==0:
            wait=1
        response=bytearray(self.serial.read(7))
        print(response.hex())
        id=response[5]
        print("RTU ID: %s" %hex(id))
        
        
        
        
    
    
    
