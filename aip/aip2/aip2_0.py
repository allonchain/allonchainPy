from src.common.datatype import *
from src.common import aiptool


class Transaction_Gate:# be in list, size GetSizeDeduction
    def __init__(self):
        self.aipname     = VariStr("aip2.aip2_0.Transaction_Gate")
        self.expiretime  = VariInt()
        self.withdraw    = VariList() ##utxo inputs , aip1.aip1_0.Input
        self.deposit     = VariList() ##utxo outputs, aip1.aip1_0.Output
        self.token       = VariStr()
        self.fee         = VariInt()
        self.txrealid    = VariStr()
        self.agreement   = VariStr("this service is offered by aocpay, the ownerpubkey is responsible for any real law issue caused by this record")
        self.ownerpubkey = VariBytes()
        self.sig         = VariBytes()
        self.ownerships  = VariList()#IF ownership is not null, need to change the ownership of aocpay
        
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)

    def serialize(self):
        data = self.aipname.serialize() + self.expiretime.serialize() + self.withdraw.serialize() + self.deposit.serialize()\
               + self.token.serialize() + self.fee.serialize() + self.txrealid.serialize() + self.agreement.serialize()\
               + self.ownerpubkey.serialize() + self.sig.serialize() + self.ownerships.serialize()
        return data
    
    def deserialize(self, stream):
        self.aipname      =  VariStr("aip2.aip2_0.Transaction_Gate")
        self.expiretime.deserialize(stream)
        self.withdraw.deserialize(stream)
        self.deposit.deserialize(stream)
        self.token.deserialize(stream)
        self.fee.deserialize(stream)
        self.txrealid.deserialize(stream)
        self.agreement.deserialize(stream)
        self.ownerpubkey.deserialize(stream)
        self.sig.deserialize(stream)
        self.ownerships.deserialize(stream)
        return self
    
    def GetMsgSig(self):
        data1 = self.aipname.serialize() + self.expiretime.serialize() + self.withdraw.serialize() + self.deposit.serialize()\
               + self.token.serialize() + self.fee.serialize() + self.txrealid.serialize() + self.agreement.serialize()
        data2 = data1 + self.ownerpubkey.serialize() + self.sig.serialize()
        return VariBytes().parse(data1).serialize(), VariBytes().parse(data2).serialize()

    def GetSizeDeduction(self):
        return len(self.deposit.serialize() + self.agreement.serialize())

    def Verification(self, currentheight, aipdic):
        if self.aipname.value != "aip2.aip2_0.Transaction_Gate":
            return False, "aip2.aip2_0.Transaction_Gate, item 1, False"
        if not aiptool.IsAipLegalForCurrentHeight(self.aipname.value, currentheight, aipdic):
            return False, "aip2.aip2_0.Transaction_Gate, item 1.1, False"

        for inputi in self.withdraw:
            if inputi.aipname.value != "aip1.aip1_0.Input":
                return False, "aip2.aip2_0.Transaction_Gate, item 2, False"
            if inputi.pubkey.value  != self.ownerpubkey.value:
                return False, "aip2.aip2_0.Transaction_Gate, item 2.1, False"
            re, msg = inputi.Verification(currentheight, aipdic)
            if not re:
                return False, "aip1.aip1_0.Transaction_Pay, item 2.2, False"
        
        for outputi in self.deposit:
            if outputi.aipname.value != "aip1.aip1_0.Output":
                return False, "aip2.aip2_0.Transaction_Gate, item 3, False"
            re, msg = outputi.Verification(currentheight, aipdic)
            if not re:
                return False, "aip2.aip2_0.Transaction_Gate, item 3.1, False"
        
        if self.token.value.lower() == "aoc":
            return False, "aip2.aip2_0.Transaction_Gate, item 4, False"

        if self.agreement.value != "this service is offered by aocpay, the ownerpubkey is responsible for any real law issue caused by this record":
            return False, "aip2.aip2_0.Transaction_Gate, item 5, False"
        
        msg1, msg2 = self.GetMsgSig()
        
        wallet = aiptool.GetObj("aip0.aip0_0.Wallet")
        try:
            re = wallet.VerifyMsg(self.ownerpubkey.value, msg1, self.sig.value)
        except:
            re = False
        if not re:
            return False, "aip2.aip2_0.Transaction_Gate, item 6, False"

        for os in self.ownerships:
            if os.aipname.value != "aip0.aip0_0.Ownership":
                return False, "aip2.aip2_0.Transaction_Gate, item 7.1, False"
            if msg2 != os.msg.value:
                return False, "aip2.aip2_0.Transaction_Gate, item 7.2, False"
            re, msg = os.Verification(currentheight, aipdic)
            if not re:
                return False, "aip2.aip2_0.Transaction_Gate, item 7.3, False " + msg
        
        return True, "aip2.aip2_0.Transaction_Gate, True"
