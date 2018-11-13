from src.common.datatype import *
from src.common import aiptool

class Input:
    def __init__(self):
        self.aipname      = VariStr("aip1.aip1_0.Input")
        self.blockheight  = VariInt() ## block height
        self.txheight     = VariInt() ## tansaction in payload
        self.opheight     = VariInt() ## output height
        self.pubkey       = VariBytes(b"")
    
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)
    
    def serialize(self):
        return self.aipname.serialize() + self.blockheight.serialize() + self.txheight.serialize() + self.opheight.serialize() + self.pubkey.serialize()
    
    def deserialize(self, stream):
        self.aipname      =  VariStr("aip1.aip1_0.Input")
        self.blockheight.deserialize(stream)
        self.txheight.deserialize(stream)
        self.opheight.deserialize(stream)
        self.pubkey.deserialize(stream)
        return self

    def Verification(self, currentheight, aipdic):
        ##1 the protocol name should be the same
        if self.aipname.value != "aip1.aip1_0.Input":
            return False, "aip1.aip1_0.Input, item 1, False"
        if not aiptool.IsAipLegalForCurrentHeight(self.aipname.value, currentheight, aipdic):
            return False, "aip1.aip1_0.Input, item 1.1, False"
        return True, "aip1.aip1_0.Input, True"

class Output:
    def __init__(self):
        self.aipname    = VariStr("aip1.aip1_0.Output")
        self.amount     = VariInt()
        self.aocaddress = VariStr()
        
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)
    
    def serialize(self):
        return self.aipname.serialize() + self.amount.serialize() + self.aocaddress.serialize()

    def deserialize(self, stream):
        self.aipname      =  VariStr("aip1.aip1_0.Output")
        self.amount.deserialize(stream)
        self.aocaddress.deserialize(stream)
        return self
    
    def Verification(self, currentheight, aipdic):
        if self.aipname.value != "aip1.aip1_0.Output":
            return False, "aip1.aip1_0.Output, item 1, False"
        if not aiptool.IsAipLegalForCurrentHeight(self.aipname.value, currentheight, aipdic):
            return False, "aip1.aip1_0.Output, item 1.1, False"
        ##verify aoc address
        if not aiptool.GetObj("aip0.aip0_0.Wallet").VerifyAddress(self.aocaddress.value):
            return False, "aip1.aip1_0.Output, item 2, False"
        return True, "aip1.aip1_0.Output, True"


class Transaction_Pay:# be in list, size GetSizeDeduction
    def __init__(self):
        self.aipname     = VariStr("aip1.aip1_0.Transaction_Pay")
        self.expiretime  = VariInt()
        self.inputs      = VariList()
        self.outputs     = VariList()
        self.token       = VariStr("aoc")
        self.sigs        = VariList()
    
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)

    def serialize(self):
        return self.aipname.serialize() + self.expiretime.serialize() + self.inputs.serialize() + self.outputs.serialize() + self.token.serialize() + self.sigs.serialize()

    def deserialize(self, stream):
        self.aipname      =  VariStr("aip1.aip1_0.Transaction_Pay")
        self.expiretime.deserialize(stream)
        self.inputs.deserialize(stream)
        self.outputs.deserialize(stream)
        self.token.deserialize(stream)
        self.sigs.deserialize(stream, objclass = VariBytes)
        return self
    
    def GetMsgSig(self):
        data = self.aipname.serialize() + self.expiretime.serialize() + self.inputs.serialize() + self.outputs.serialize() + self.token.serialize()
        return VariBytes().parse(data).serialize()

    def GetTxType(self):
        #"""
        #id=0:fail
        #id=1: normal transaction
        #id=2: integration transaction, the total transaction length is leninput
        #"""
        if (len(self.inputs) == len(self.sigs) and len(self.outputs) > 0):
            return 1
        elif (len(self.sigs) == 1 and len(self.outputs) == 1):
            return 2
        return 0
    
    def GetSizeDeduction(self):
        if self.GetTxType() != 2:
            return 0
        else:
            return len(self.inputs.serialize())
    
    def Verification(self, currentheight, aipdic):
        if self.aipname.value != "aip1.aip1_0.Transaction_Pay":
            return False, "aip1.aip1_0.Transaction_Pay, item 1, False"
        if not aiptool.IsAipLegalForCurrentHeight(self.aipname.value, currentheight, aipdic):
            return False, "aip1.aip1_0.Transaction_Pay, item 1.1, False"
        ##3 Length of inputs and sigs should equal, integration or normal transaction
        txid = self.GetTxType()
        if txid == 0:
            return False, "aip1.aip1_0.Transaction_Pay, item 2, False"
        ##4
        for outputi in self.outputs:
            if outputi.aipname.value != "aip1.aip1_0.Output":
                return False, "aip1.aip1_0.Transaction_Pay, item 3, False"
            re, msg = outputi.Verification(currentheight, aipdic)
            if not re:
                return False, "aip1.aip1_0.Transaction_Pay, item 3.1, False"
        ##5
        msgsig = self.GetMsgSig()
        wallet = aiptool.GetObj("aip0.aip0_0.Wallet")
        #"""if is normal transaction or integration transaction"""
        for idd, inputi in enumerate(self.inputs):
            if inputi.aipname.value != "aip1.aip1_0.Input":
                return False, "aip1.aip1_0.Transaction_Pay, item 4, False"
            re, msg = inputi.Verification(currentheight, aipdic)
            if not re:
                return False, "aip1.aip1_0.Transaction_Pay, item 4.1, False"
            if txid == 1:
                sig = self.sigs.value[idd].value
            elif txid == 2:
                sig = self.sigs.value[0].value
            try:
                rew = wallet.VerifyMsg(inputi.pubkey.value, msgsig, sig)
            except:
                rew = False
            if not rew:
                return False, "aip1.aip1_0.Transaction_Pay, item 4.2, False"
            
        return True, "aip1.aip1_0.Transaction_Pay, True"
