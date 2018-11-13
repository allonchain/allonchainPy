from wallet.WalletClient import WalletClient
from wallet.miner import miner
from aip.aip0.aip0_0 import *

def ObjList2BytesList(objlist):
    return [a.serialize() for a in objlist]

class WalletInter():
    def __init__(self):
        self.wclist = []
        #self.wc = WalletClient("IamWill,ICreatedThisAocBlockchain,IWishItSuccess.余大利DaliYu")
        self.MyNode = True
        
        self.wclist.append(WalletClient(fullstr="I love aoc", MyNode = self.MyNode))

        self.wc = self.wclist[0]
        self.height = 0
        #self.mr = miner()
        #self.mr.Update_Wallet(self.wc)
        
        #self.wc.LoginWithSeedStr("IamWill,ICreatedThisAocBlockchain,IWishItSuccess.余大利DaliYu")
    
    def SendWithdrawDeposit(self, token, withdraw, deposit, address = "", amount = 1):
        if withdraw == 0 and deposit == 0:
            return "no operation"
        if deposit == 1 and (address == "" or amount ==0):
            return "deposit part is not well inputed"
        return self.wc.SendTxGate(address, amount = amount, token = token, fee = 100000, txrealid = "none", ifwithdraw = withdraw)

    def addWallet(self, seedstr):
        wc = WalletClient(seedstr.strip(), MyNode = self.MyNode)
        if wc not in self.wclist:
            self.wclist.append(wc)

    def SendToken(self, add_to = None, amount = 1, fee = 10000, txid = 1, token = 'aoc'):
        if token not in self.wc.utxos:
            return "you dont have this token or token is invalid"
        if txid == 1:
            return self.wc.SendTokenPay(add_to, amount, fee, txid, token)
        elif txid == 2:
            return self.wc.IntegratTokenPay(fee, token)

    def BuildOwnershipObj(self, bl):
        osmsg =  VariBytes().parse(bl.MerkleRoot(ObjList2BytesList(bl.payloads.value))).serialize()
        os = Ownership()
        os.msg.parse(osmsg)
        os.pubkey.parse(self.wc.GetPubKey())
        os.sig.parse(self.wc.SignMsg(os.msg.value))
        return os
    
    def SetMainWallet(self, index):
        if index < len(self.wclist):
            self.wc = self.wclist[index]
            #self.mr.Update_Wallet(self.wc)
        return
    
    def GetUTXOs(self,token="aoc", forcerefresh = False):
        if self.wc.GetLedgerInfo():
            height = self.wc.ledgerinfo['BlockHeight']
            if height != self.height:
                self.height  = height
                self.wc.UpdateMyWallet()
        if (token not in self.wc.utxos) or forcerefresh:
            if self.wc.GetUTXOs(token):
                return self.wc.utxos[token]
            else:
                return None
        else:
             return self.wc.utxos[token]

    def GetBlock(self, height):
        return self.wc.GetBlock(height)
    
    def GetLedgerInfo(self):
        return self.wc.GetLedgerInfo()

    def MerkleRoot(self, payload):
        length = len(payload)
        if length == 0:
            return b""
        if length == 1:
            return payload[0]
        if length%2 == 1:
            payload.append(copy.deepcopy(payload[length-1]))
            length += 1
        payloadnew = [sha3_256(sha3_256(payload[2*idd]+payload[2*idd+1]).digest()).digest() for idd in range(int(length/2))]
        return self.MerkleRoot(payloadnew)
    
    def GetPayloadList(self, ltype = "Law"):
        plist = self.wc.GetPool(ltype)
        if plist is None:
            return None
        #for p in plist:
        #    print(p.LawName.value)
        return plist
        
    

