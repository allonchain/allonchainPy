import time
from src.common import aiptool
from hashlib import sha3_256

class miner:
    def __init__(self, height = 0):
        self.height  = height
        self.wc      = None
        self.hashing = False
        self.Block   = None
        self.bkobj   = None
        self.chinfo  = None
        self.hashing = False
    
    def Update_Wallet(self, wc):
        self.wc = wc
    
    def PackBlock(self):
        if self.wc is None:
            return False
        if self.wc.GetLedgerInfo():
            self.height = self.wc.ledgerinfo['BlockHeight']
            self.aipdic = self.wc.ledgerinfo['AipDic']
            txsnum      = self.wc.ledgerinfo['PoolInfo'][0]
            self.chinfo = self.wc.ledgerinfo['ChainInfo']
            
            if txsnum < 1:
                #print("no txs in the pool")
                return False
            self.Block  = aiptool.GetObjFromNameAndHeight("Block",self.aipdic)
            self.bkobj = self.Block()
            self.bkobj.blocktype.parse(2)
            
            bytespre = bytes.fromhex(self.wc.ledgerinfo['CurrentHash'])
            self.bkobj.preblock.parse(bytespre)
            self.bkobj.timestamp.parse(max(int(time.time()), self.wc.ledgerinfo['timestamp']+1)) 
            txs = self.wc.GetPool(ltype = "Tx")
            if txs is not None:
                self.bkobj.payloads.parse(txs)
                self.bkobj.ownerships.parse([self.wc.BuildOwnershipObj(self.bkobj)])
                ##smart miner does below
                avepow, avesize, avetime = self.chinfo
                tr = (100/avetime)**0.1
                sr = avesize/self.bkobj.GetSize()
                smartr = max(int(tr*sr*len(txs)*1.5),1)
                if smartr < len(txs):
                    self.bkobj.payloads.parse(txs[:smartr])
                    self.bkobj.ownerships.parse([self.wc.BuildOwnershipObj(self.bkobj)])
                ##
                return True
        return False
    
    def StartMing(self):
        if self.PackBlock():
            avepow, avesize, avetime = self.chinfo
            blocksize = 4 + self.bkobj.GetSize() - self.bkobj.GetSizeDeduction()
            ratiosize = blocksize/avesize
            ratiosize = ratiosize**1.2 if ratiosize > 1 else ratiosize**0.6
            ratiotime = (avetime/100.0)
            ratiotime = ratiotime**1.2 if ratiotime > 1 else ratiotime**0.6
            nextpow   = avepow*ratiotime/ratiosize
            
            print(avepow, avetime , avesize, blocksize)
            print("Mining is ongoing, target pow is", nextpow)
            
            while (self.hashing):
                POW = self.bkobj.POW()
                if POW < nextpow:
                    print("good block",POW)
                    self.wc.SendBlock(self.bkobj)
                    return True
                else:
                    self.bkobj.nonce.parse(self.bkobj.nonce.value + 1)
        return False
            
        


