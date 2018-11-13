import socket
from src.common.datatype import VariBytes, VariStr, VariInt, MsgHeader, MsgHeader_SIZE
from hashlib import sha3_256
import time
from io import BytesIO
from src.tool     import *
import json
from src.p2p import p2p_client
from aip.aip0.aip0_0 import *
from aip.aip1.aip1_0 import *
from src.blockheader import HeaderNode
from wallet.WalletClient import WalletClient

a = VariInt()
a.parse(32)
print(a.serialize())
stream   = BytesIO(a.serialize())
a.deserialize(stream)
print(a.value)

w = WalletClient("IamWill,ICreatedThisAocBlockchain,IWishItSuccess.余大利DaliYu")
print(0,w.address)
print(0, w.GetUTXOs())
print(1, w.SendLaw("Law","I love this coin", 1))
print(1, w.SendLaw("Law","I love this guy", 0))
print(2, w.SendOwnership(b'\x12'))
print(4, w.SendTxGate("A2uKN7Xc94sNSf9Jumj5fUZ6AMtN1TyzTr2ieYgQgdxYaRm4Amw",amount=10, token="eur"))
print(3, w.IntegratTokenPay(1,"aoc"))



#


wl = Wallet()




wl.LoginWithSeedStr("IamWill,ICreatedThisAocBlockchain,IWishItSuccess.余大利DaliYu")
print(wl.address)
bl = Block()
cli = p2p_client()

#
print(cli.Connect())
pp = VariStr("aoc").serialize() + VariStr(wl.address).serialize()

func, payload = cli.SendMsg(msgname="GetUTXOs", payload = pp, MyNode = True)

if payload is not None:
    stream   = BytesIO(payload)
    utxolist = json.loads(VariStr().deserialize(stream).value)
    print(utxolist)



print(cli.Connect())
print(1, cli.SendMsg())


print(cli.Connect())
print(2, cli.SendMsg(msgname="GetLedgerInfo"))



print(cli.Connect())
ll1 = Law()
ll1.LawName.parse("aip1.aip1_0.Input")
ll1.LawContent.parse("Ilikesssssss中文thislddaw")
ll1.LawType.parse(1)
ll1.expiretime.parse(int(time.time())+1000)
print(3, cli.SendMsg(msgname="LawIn", payload = ll1.serialize()))

print(cli.Connect())
ll2 = Law()
ll2.LawName.parse("aip1.aip1_0.Output")
ll2.LawContent.parse("Ilisssksse中文thislaw22222222")
ll2.LawType.parse(1)
ll2.expiretime.parse(int(time.time())+1000)
print(3, cli.SendMsg(msgname="LawIn",payload=ll2.serialize()))

print(cli.Connect())
ll3 = Law()
ll3.LawName.parse("aip2.aip2_0.Transaction_Gate")
ll3.LawContent.parse("Ilisssksse中文thislaw22222222")
ll3.LawType.parse(1)
ll3.expiretime.parse(int(time.time())+1000)
print(3, cli.SendMsg(msgname="LawIn",payload=ll3.serialize()))

bl.payloads.parse([ll1, ll2, ll3])
stream   = BytesIO(bl.payloads.serialize())
bl.payloads.deserialize(stream)
print(bl)

osmsg =  VariBytes().parse(bl.MerkleRoot(ObjList2BytesList(bl.payloads.value)))


cli.Connect()
os = Ownership()
os.msg.parse(osmsg.serialize())
os.pubkey = VariBytes().parse(wl.vk.to_string())
os.sig    = VariBytes().parse(wl.SignMsg(os.msg.value))
bl.ownerships.parse([os])
print(4, cli.SendMsg(msgname="OwnershipIn",payload=os.serialize()))


print(cli.Connect())
#
bl.preblock.parse(b'%\xa9<\xa2\xed\xec\x99\x03\x04\xcd\x8c|yK\x00Yq\xa1\x9cuX\xb5\x16\xb8YB\xa1C\xfb\xd5U\xed')
bl.timestamp.parse(int(time.time()))

#print(HeaderNode().parse(bl).serialize())
#print(bl.serialize())
print(5, cli.SendMsg(msgname="BlockIn", payload=bl.serialize()))


'''
func, payload = UnPackMsg(sock.recv(1024))

if func == "LedgerInfo":
    stream  = BytesIO(payload)
    bb = VariStr().deserialize(stream).value


print("Sent:     {}".format(data.value))
print("Received: {}".format(json.loads(bb)))
'''
