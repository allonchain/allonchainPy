from .common.datatype import *
from src.tool import ObjList2BytesList
from hashlib import sha3_256

class HeaderNode:
    def __init__(self):
        ## header info
        self.aipname    = VariStr()
        self.blocktype  = VariInt()
        self.preblock   = VariBytes()
        self.timestamp  = VariInt()
        self.ownerships = VariBytes() 
        self.payloads   = VariBytes()
        self.nonce      = VariInt()
        self.size       = VariInt()
        self.size_deuct = VariInt()
    
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)

    def parse(self, bkobj):
        self.aipname    = bkobj.aipname
        self.blocktype  = bkobj.blocktype
        self.preblock   = bkobj.preblock
        self.timestamp  = bkobj.timestamp
        self.ownerships = VariBytes().parse(bkobj.MerkleRoot(ObjList2BytesList(bkobj.ownerships.value)))
        self.payloads   = VariBytes().parse(bkobj.MerkleRoot(ObjList2BytesList(bkobj.payloads.value)))
        self.nonce      = bkobj.nonce
        self.size       = VariInt().parse(bkobj.GetSize())
        self.size_deuct = VariInt().parse(bkobj.GetSizeDeduction())
        return self

    def GetSize(self):
        return self.size.value
    
    def GetSizeDeduction(self):
        return self.size_deuct.value

    def serialize(self):
        return  self.aipname.serialize() + self.blocktype.serialize() +  self.preblock.serialize() + \
                self.timestamp.serialize() + self.ownerships.serialize() + self.payloads.serialize() +\
                self.nonce.serialize() + self.size.serialize() + self.size_deuct.serialize()

    def deserialize(self, stream):
        self.aipname.deserialize(stream)
        self.blocktype.deserialize(stream)
        self.preblock.deserialize(stream)
        self.timestamp.deserialize(stream)
        self.ownerships.deserialize(stream)
        self.payloads.deserialize(stream)
        self.nonce.deserialize(stream)
        self.size.deserialize(stream)
        self.size_deuct.deserialize(stream)
        return self

    def Hash(self):
        return sha3_256(self.serialize()).digest()

    def POW(self):
        hashbytes = self.hash if hasattr(self, 'hash') else self.Hash()
        maxdiff = int('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',16)
        diff    = int.from_bytes(hashbytes, byteorder='big')
        return diff/maxdiff




'''
class HeaderChains:
    def __init__(self):
        self.chains     = [{'size':0, 'chain':[]}]
        self.chainid    = 0
        self.chainmax   = 0
        
    def Latest100HeaderList(self, headerlist):
        end   = len(headerlist)
        start = 0 if end > 100 else (end-100)
        return headerlist[start:end]

    def AveBlockInfo(self, headerlist):
        lens = len(headerlist)
        if lens == 0:
            return 0.001, 100, 200
        elif lens > 100:
            return None, None, None
        avesize = avepow = avetime = 0
        for bkheader in headerlist:
            avepow   +=  bkheader.POW()
            avesize  +=  bkheader.size.value
        avepow    = avepow/lens
        avesize   = avesize/lens
        avetime   = (headerlist[lens-1].timestamp.value - headerlist[0].timestamp.value)/(lens-1) if lens > 1 else 200.0
        return avepow, avesize, avetime

    def GetNextPow(self, headerlist, blocksize):
        avepow, avesize, avetime = self.AveBlockInfo(headerlist)
        print("powinfo: ", avepow, avetime, avesize, blocksize)
        ratiosize = blocksize/avesize
        ratiosize = ratiosize**1.2 if ratiosize > 1 else ratiosize**0.6
        ratiotime = (avetime/200.0)**1.2
        targetpowp = avepow*ratiotime/ratiosize
        return targetpowp

    def VerifyBlockObj(self, blockobj, pos_block, headerlist):
        #verify a new block, POS and POW
        #blockobj could be header or block
        #already latest 100 block headerlist
        blocktype = blockobj.blocktype.value
        if blocktype == 0 and pos_block < 1*1000000000*1000000:
            return False, "Chain POW/POS, item 1, False"
        if blocktype == 1 and pos_block < 0.62*1000000000*1000000:
            return False, "Chain POW/POS, item 2, False"
        if blocktype == 2:
            blocksize   = blockobj.GetSize() - blockobj.GetSizeDeduction()
            if blockobj.POW() > self.GetNextPow(headerlist, blocksize):
                return False, "Chain POW/POS, item 3, False"
        return True, "Chain POW/POS, True"

    def AddHeaderNode(self, node, pos_node):
        assert isinstance(node, HeaderNode)
        for index, chain in enumerate(self.chains):
            lens = len(chain['chain'])
            for indexnode, inode in enumerate(chain['chain']):
                if inode.Hash() == node.preblock.value:
                    if indexnode == lens -1: ##at the same chain
                        ## verify pos and pow
                        chainlist = self.Latest100HeaderList(chain['chain'])
                        re, msg =  self.VerifyBlockObj(node, pos_node, chainlist)
                        if not re:
                            return False, msg
                        self.chains[index]['chain'].append(node)
                        self.chains[index]['size'] += node.size.value
                        ## add node into the end of longest chain
                        if self.chains[index]['size'] > self.chains[self.chainid]['size']:
                            self.chainmax = index
                        ## add node on the end of another chain
                    elif chain['chain'][indexnode + 1].Hash() == node.Hash(): ##ALREADY INSIDE
                        return False, "Already Inside"
                    else:## need copy to another chain
                        chaint = {'size':0, 'chain':[]}
                        chaint['chain'].extend((self.chains[index]['chain'][:indexnode+1]).copy())
                        ## verify pos and pow
                        chainlist = self.Latest100HeaderList(chaint['chain'])
                        re, msg =  self.VerifyBlockObj(node, pos_node, chainlist)
                        if not re:
                            return False, msg
                        chaint['chain'].append(node)
                        for tt in chaint['chain']:
                            chaint['size'] += tt.size.value
                        self.chains.append(chaint)
                        if chaint['size'] > self.chains[self.chainid]['size']:
                            self.chainmax = index
                    return True
        return False, "no matched previous block"
'''




    
