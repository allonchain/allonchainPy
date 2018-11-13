from src.common import aiptool
from src.common.base58   import *
from src.common.datatype import *
from src.tool import ObjList2BytesList
from src.blockheader import HeaderNode
from src.ecdsa import SigningKey, VerifyingKey, SECP256k1
from codecs import encode, decode
from hashlib import sha3_256
import copy


class Chain():
    def __init__(self):
        self.headerlist = []

    def AddHeaderObj(self, bhobj):
        if len(self.headerlist) == 0 or self.headerlist[len(self.headerlist)-1].Hash() == bhobj.preblock.value:
            self.headerlist.append(bhobj)
            return True
        return False
    
    def Latest100HeaderList(self):
        end   = len(self.headerlist)
        start = 0 if end < 100 else (end-100)
        return self.headerlist[start:end]
    
    def AveBlockInfo(self):
        headerlist100 = self.Latest100HeaderList()
        lens = len(headerlist100)
        if lens == 0:
            return 0.001, 100, 200
        elif lens > 100:
            return None, None, None
        size_total, pow_total = 0, 0
        for bkheader in headerlist100:
            pow_total   +=  bkheader.POW()
            size_total  +=  bkheader.GetSize()
        avesize = size_total/lens
        avepow  = pow_total/lens
        avetime = (headerlist100[lens-1].timestamp.value - headerlist100[0].timestamp.value)/lens
        if lens <= 1:
            avetime = 10000
        return avepow, avesize, avetime
    
    def GetNextPow(self, blocksize):
        avepow, avesize, avetime = self.AveBlockInfo()
        print("powinfo: ", avepow, avetime, avesize, blocksize)
        ratiosize = blocksize/avesize
        ratiosize = ratiosize**1.2 if ratiosize > 1 else ratiosize**0.6
        ratiotime = (avetime/100.0)
        ratiotime = ratiotime**1.2 if ratiotime > 1 else ratiotime**0.6
        return avepow*ratiotime/ratiosize
    
    def Verification(self, bhobj, POS):##verify header, POS and POW and PRE_BLOCK, timestamp
        if len(self.headerlist) == 0:
            if POS >= 100*1000000_000000:
                return True, "aip0.aip0_0.Chain, First Block, True"
            else:
                return False, "aip0.aip0_0.Chain, First Block, False"
        elif self.headerlist[len(self.headerlist)-1].Hash() != bhobj.preblock.value:
            return False, "aip0.aip0_0.Chain, item 1.1, False"
        if bhobj.timestamp.value <= self.headerlist[len(self.headerlist)-1].timestamp.value:
            return False, "aip0.aip0_0.Chain, item 1.2, False"
        if bhobj.blocktype.value  == 0:
            if POS < 100*1000000_000000:
                return False, "aip0.aip0_0.Chain, item 2, False"
        elif bhobj.blocktype.value == 1:
            if POS < 62*1000000_000000:
                return False, "aip0.aip0_0.Chain, item 3, False"
        elif bhobj.blocktype.value == 2:
            blocksize   = bhobj.GetSize() - bhobj.GetSizeDeduction()
            targetpowp  = self.GetNextPow(blocksize)
            if bhobj.POW() > targetpowp:
                return False, "aip0.aip0_0.Chain, item 4, False"
        return True, "aip0.aip0_0.Chain, True"


class Wallet: # general
    def LoginWithSeedStr(self, seedstr):
        seedbytes    = encode(seedstr,'utf-8')
        self.sk      = SigningKey.from_string(sha3_256(seedbytes).digest(),curve = SECP256k1, hashfunc=sha3_256)
        self.vk      = self.sk.get_verifying_key()
        self.address = Wallet.AddressFromPubKey(self.vk.to_string())
        return self

    def __eq__(self, other):
        return (self.address == other.address)

    def SignMsg(self, msg_bytes):
        return self.sk.sign(msg_bytes)

    @staticmethod
    def VerifyMsg(pubkey_bytes, msg_bytes, sig_bytes):
        return VerifyingKey.from_string(pubkey_bytes,curve = SECP256k1, hashfunc=sha3_256).verify(sig_bytes, msg_bytes)

    @staticmethod
    def AddressFromPubKey(pubkey_bytes):
        pubkeyhash = sha3_256(pubkey_bytes).digest()
        checksum   = sha3_256(pubkeyhash).digest()[:4]
        address_bytes = checksum + pubkeyhash
        return 'A' + encode58(int.from_bytes(address_bytes, byteorder='big'))
    
    @staticmethod
    def VerifyAddress(basestr):
        if len(basestr)<1 or basestr[0] != 'A':
            return False
        address_int   = decode58(basestr[1:])
        address_bytes = address_int.to_bytes((address_int.bit_length() + 7) // 8,byteorder='big')
        checksum      = address_bytes[:4]
        pubkeyhash    = address_bytes[4:]
        checksum2     = sha3_256(pubkeyhash).digest()[:4]
        return True if checksum == checksum2 else False


class Ownership: 
    def __init__(self):
        self.aipname  = VariStr("aip0.aip0_0.Ownership")
        self.pubkey   = VariBytes(b"")
        self.msg      = VariBytes(b"")
        self.sig      = VariBytes(b"")
    
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)
    
    def serialize(self):
        return self.aipname.serialize() + self.pubkey.serialize() + self.msg.serialize() + self.sig.serialize()

    def deserialize(self, stream):
        self.aipname    =  VariStr("aip0.aip0_0.Ownership")
        self.pubkey.deserialize(stream)
        self.msg.deserialize(stream)
        self.sig.deserialize(stream)
        return self
        
    def Verification(self, currentheight, aipdic):
        ##1 the protocol name should be the same
        if self.aipname.value != "aip0.aip0_0.Ownership":
            return False, "aip0.aip0_0.Ownership, item 1, False"

        if not aiptool.IsAipLegalForCurrentHeight(self.aipname.value, currentheight, aipdic):
            return False, "aip0.aip0_0.Ownership, item 1.1, False"

        #2 the msg should be verified
        wallet = aiptool.GetObj("aip0.aip0_0.Wallet")
        try:
            re = wallet.VerifyMsg(self.pubkey.value, self.msg.value, self.sig.value)
        except:
            re = False
        if not re:
            return False, "aip0.aip0_0.Ownership, item 2, False"

        return True, "aip0.aip0_0.Ownership, True"


class Law: # be in list, size GetSizeDeduction
    def __init__(self):
        self.aipname    =  VariStr("aip0.aip0_0.Law")
        self.LawName    =  VariStr()
        self.LawType    =  VariInt() #0 constitution law, 1, normal law
        self.LawContent =  VariStr()
        self.expiretime =  VariInt()
    
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)

    def serialize(self):
        return self.aipname.serialize() + self.LawName.serialize() + self.LawType.serialize() + self.LawContent.serialize() + self.expiretime.serialize()

    def deserialize(self, stream):
        self.aipname    =  VariStr("aip0.aip0_0.Law")
        self.LawName.deserialize(stream)
        self.LawType.deserialize(stream)
        self.LawContent.deserialize(stream)
        self.expiretime.deserialize(stream)
        return self
    
    def GetSizeDeduction(self):
        return 0
    
    def Verification(self, currentheight, aipdic):
        ##1. the protocol name should be the same
        if self.aipname.value != "aip0.aip0_0.Law":
            return False, "aip0.aip0_0.Law, item 1, False"

        if not aiptool.IsAipLegalForCurrentHeight(self.aipname.value, currentheight, aipdic):
            return False, "aip0.aip0_0.Law, item 1.1, False"

        if self.LawName.value.rstrip() == "" or self.LawContent.value.rstrip() == "":
            return False, "aip0.aip0_0.Law, item 2, False"

        print(self.LawName.value)
        ##2. The law name should obey the rule
        if not aiptool.VerifyAipPathRule(self.LawName.value):
            return False, "aip0.aip0_0.Law, item 3, False"
        ##3. law type
        if self.LawType.value not in (0 ,1):
            return False, "aip0.aip0_0.Law, item 4, False"
        return True, "aip0.aip0_0.Law, True"


class Block:
    def __init__(self):
        self.aipname    = VariStr("aip0.aip0_0.Block") ##use protocol to explain
        self.blocktype  = VariInt() #0: protocol, 1: normal protocol, 2:transactionblock
        self.preblock   = VariBytes()
        self.timestamp  = VariInt()
        self.ownerships = VariList() ## msg_ownership is payload
        self.payloads   = VariList() ## if blocktype == 0, only the law type payload
        self.nonce      = VariInt()
        
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)
    
    def serialize(self):
        self._data  = b''.join([self.aipname.serialize() , self.blocktype.serialize() , self.preblock.serialize() ,
                      self.timestamp.serialize() , self.ownerships.serialize() , self.payloads.serialize() , self.nonce.serialize()])
        return self._data

    def deserialize(self, stream):
        self.aipname    =  VariStr("aip0.aip0_0.Block")
        self.blocktype.deserialize(stream)
        self.preblock.deserialize(stream)
        self.timestamp.deserialize(stream)
        self.ownerships.deserialize(stream)
        self.payloads.deserialize(stream)
        self.nonce.deserialize(stream)
        return self
    
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
    
    def Hash(self):
        self._data1 = self.aipname.serialize() + self.blocktype.serialize() +  self.preblock.serialize() + self.timestamp.serialize()
        self._osdata= VariBytes().parse(self.MerkleRoot(ObjList2BytesList(self.ownerships.value))).serialize()
        self._osmsg = VariBytes().parse(self.MerkleRoot(ObjList2BytesList(self.payloads.value))).serialize()
        
        self._data2 = VariInt().parse(self.GetSize()).serialize() + VariInt().parse(self.GetSizeDeduction()).serialize()
        self._hash  = sha3_256(self._data1 + self._osdata + self._osmsg + self.nonce.serialize() + self._data2).digest()
        return self._hash

    def GetData(self):
        return self.serialize()
    
    def GetSize(self):
        return len(self.serialize())
    
    def GetSizeDeduction(self):
        self._sizededuction = 0
        for payload in self.payloads:
            self._sizededuction += payload.GetSizeDeduction()
        return self._sizededuction
    
    def POW(self):
        return int.from_bytes(self.Hash(), byteorder='big')/int('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',16)
    
    def Verification(self, currentheight, aipdic):
        ##1 the protocol name should be the same
        if self.aipname.value != "aip0.aip0_0.Block":
            return False, "aip0.aip0_0.Block, item 1, False"
        ##1.1 the protocol valid range
        if not aiptool.IsAipLegalForCurrentHeight(self.aipname.value, currentheight, aipdic):
            return False, "aip0.aip0_0.Block, item 1.1, False"

        ##2 protocol type
        if self.blocktype.value not in (0, 1, 2):
            return False, "aip0.aip0_0.Block, item 2, False"

        ##3 check payloads
        for payload in self.payloads:
            if self.blocktype.value in (0, 1):
                if payload.aipname.value != "aip0.aip0_0.Law":
                    return False, "aip0.aip0_0.Block, item 3.1.1, False"
                if self.blocktype.value == 1 and payload.LawType.value == 0:
                    return False, "aip0.aip0_0.Block, item 3.1.2, False"
            if payload.expiretime.value <= self.timestamp.value:
                return False, "aip0.aip0_0.Block, item 3.2, False"
            re, msg = payload.Verification(currentheight, aipdic)
            if not re:
                return False, "aip0.aip0_0.Block, item 3.3, False " + msg
        
        ##4 check ownership
        osmsg = self._osmsg if hasattr(self, '_osmsg') else VariBytes().parse(self.MerkleRoot(ObjList2BytesList(self.payloads.value))).serialize()
        if len(self.ownerships) == 0:
            return False, "aip0.aip0_0.Block, item 4.0, False"
        for os in self.ownerships:
            if os.aipname.value != "aip0.aip0_0.Ownership":
                return False, "aip0.aip0_0.Block, item 4.1, False"
            if osmsg != os.msg.value:
                return False, "aip0.aip0_0.Block, item 4.2, False"
            re, msg = os.Verification(currentheight, aipdic)
            if not re:
                return False, "aip0.aip0_0.Block, item 4.3, False " + msg
        
        return True, "aip0.aip0_0.Block, True"

     
        
