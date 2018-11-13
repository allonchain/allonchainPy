from src.common.datatype import VariBytes, VariStr, VariInt, VariList
from src.database import DatabaseMain
from src.common   import aiptool
from src.tool     import *
from io import BytesIO
import time
import json


class AocRPC:
    def __init__(self):
        self.db             = DatabaseMain()
        self.TxsPool        = []
        self.LawsPool       = []
        self.OwnershipsPool = []

        self.record = [] #for record information to write report

    def ReadRecord(self):
        with open('record.json', 'r') as f:
            node = json.load(f)
            return node
    
    def SaveRecord(self):
        with open('record.json', 'w') as f:
            json.dump(self.record, f)
            return

    def PING_AOC(self, payload = None):
        return PackMsg("PONG_AOC", VariBytes(b'').serialize())
    
    def GetLedgerInfo(self, payload = None):
        poolinfo    = [len(self.TxsPool), len(self.LawsPool), len(self.OwnershipsPool)]
        chaininfo   = self.db.Chain.AveBlockInfo()
        bkobj       = self.db.LoadBlock(self.db.bkheight)
        chash       = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
        tstamp      = int(time.time())
        if bkobj is not None:
            chash   = bkobj.Hash().hex()
            tstamp  = bkobj.timestamp.value
        aocpayowner = self.db.API_GetAocpayOwner()
        ledgermsg   = {'AipDic':self.db.aipdic, 'BlockHeight': self.db.bkheight, 'PoolInfo':poolinfo, \
                     'ChainInfo':chaininfo, 'CurrentHash':chash, 'timestamp': tstamp, 'AocpayOwner':aocpayowner}
        msg         = VariStr(json.dumps(ledgermsg)).serialize()
        return PackMsg("GetLedgerInfo_r", msg)
    
    def GetBlock(self, payload = None):
        height   = VariInt().deserialize(BytesIO(payload)).value
        bkobj    = self.db.LoadBlock(height)
        return PackMsg("GetBlock_r", bkobj.serialize())

    def GetUTXOs(self, payload = None):
        stream   = BytesIO(payload)
        tok      = VariStr().deserialize(stream)
        addr     = VariStr().deserialize(stream)
        listutxo = self.db.API_GetUtxoAmount(token = tok.value, address = addr.value, ListMode = True)
        if len(listutxo) == 0:
            utxomsg = []
        else:
            utxomsg  = [{'bh':ut[0], 'th':ut[1], 'oh':ut[2], 'am':ut[3], 'status':1} for ut in listutxo]
        msg      = VariStr(json.dumps(utxomsg)).serialize()
        return PackMsg("GetUTXOs_r", msg)
    
    def GetPool(self, payload = None):
        ptype    = VariStr().deserialize(BytesIO(payload)).value
        if ptype == 'Law':
            return PackMsg("GetPool_r", VariList(self.LawsPool).serialize())
        if ptype == 'Tx':
            return PackMsg("GetPool_r", VariList(self.TxsPool).serialize())
    
    def BlockIn(self, payload = None):
        stream   = BytesIO(payload)
        objc     = aiptool.GetObj(VariStr().deserialize(stream).value)
        if objc is not None:
            obj  = objc().deserialize(stream)
            if type(obj).__name__ != "Block":
                return PackMsg("BlockIn_r", VariStr("Wrong Block").serialize())
            re, msg  = obj.Verification(self.db.bkheight+1, self.db.aipdic)
            if re:
                re1, msg1 = self.db.VerifyBlockOnChain(obj)
                msg       = msg + "--" + msg1
                ###clear the useless txs
                if re1:
                    if obj.blocktype.value in (0,1):
                        poollaw, self.LawsPool = self.LawsPool, []
                        for law in poollaw:
                            if law not in obj.payloads.value:
                                self.LawsPool.append(law)
                    if obj.blocktype.value == 2:
                        pooltx, self.TxsPool = self.TxsPool, []
                        for tx in pooltx:
                            if tx not in obj.payloads.value:
                                self.TxsPool.append(tx)
                    
                    ##for some report
                    self.record = self.ReadRecord()
                    self.record.append([obj.timestamp.value, len(obj.payloads), len(self.TxsPool),\
                    obj.POW(), obj.GetSize()])
                    self.SaveRecord()
                    ##
                ###clear the useless txs
            print(msg)
            return PackMsg("BlockIn_r", VariStr(msg).serialize())
        else:
            return PackMsg("BlockIn_r", VariStr("Wrong Block").serialize())
    
    def TxIn(self, payload = None):
        stream   = BytesIO(payload)
        objc     = aiptool.GetObj(VariStr().deserialize(stream).value)
        if objc is not None:
            obj  = objc().deserialize(stream)
            if type(obj).__name__ not in ("Transaction_Pay" , "Transaction_Gate"):
                return PackMsg("TxIn_r", VariStr("Wrong Tx Class").serialize())
            re, msg  = obj.Verification(self.db.bkheight+1, self.db.aipdic)
            if re and obj not in self.TxsPool:
                txs = list(self.TxsPool)
                txs.append(obj)
                ret, msgt = self.db.API_CheckTxsIfValid(txs)
                msg += "--"+msgt
                if ret:
                    self.TxsPool.append(obj)
            return PackMsg("TxIn_r", VariStr(msg).serialize())
        else:
            return PackMsg("TxIn_r", VariStr("Wrong Tx").serialize())
    

    def LawIn(self, payload = None):
        stream   = BytesIO(payload)
        objc     = aiptool.GetObj(VariStr().deserialize(stream).value)
        if objc is not None:
            obj  = objc().deserialize(stream)
            if type(obj).__name__ != "Law":
                return PackMsg("LawIn_r", VariStr("Wrong Law").serialize())
            re, msg  = obj.Verification(self.db.bkheight+1, self.db.aipdic)
            if re and obj not in self.LawsPool:
                self.LawsPool.append(obj)
            return PackMsg("LawIn_r", VariStr(msg).serialize())
        else:
            return PackMsg("LawIn_r", VariStr("Wrong Law").serialize())
    
    def OwnershipIn(self, payload = None):
        stream   = BytesIO(payload)
        objc     = aiptool.GetObj(VariStr().deserialize(stream).value)
        if objc is not None:
            obj  = objc().deserialize(stream)
            if type(obj).__name__ != "Ownership":
                return PackMsg("OwnershipIn_r", VariStr("Wrong Ownership").serialize())
            re, msg  = obj.Verification(self.db.bkheight+1, self.db.aipdic)
            if re and obj not in self.OwnershipsPool:
                self.OwnershipsPool.append(obj)
            return PackMsg("OwnershipIn_r", VariStr(msg).serialize())
        else:
            return PackMsg("OwnershipIn_r", VariStr("Wrong Ownership").serialize())

