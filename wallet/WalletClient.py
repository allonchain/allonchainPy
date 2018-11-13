from src.common import aiptool
from src.common.datatype import *
from aip.aip0.aip0_0 import *
from aip.aip1.aip1_0 import *
from aip.aip2.aip2_0 import *
from src.p2p import p2p_client
import json
import time


class WalletClient(Wallet):
      def __init__(self, fullstr = None, MyNode = True):
            Wallet.__init__(self)
            self.MyNode = MyNode
            self.login  = False
            self.p2p    = p2p_client()
            self.utxos  = {}
            if fullstr != None:
                  if self.LoginWithSeedStr(fullstr):
                        self.login = True
            return
      
      def UpdateMyWallet(self):
            for token in self.utxos:
                  self.GetUTXOs(token)
      
      def BuildOwnershipObjForAocpay(self, msg2):
            os    = Ownership()
            os.msg.parse(msg2)
            os.pubkey.parse(self.GetPubKey())
            os.sig.parse(self.SignMsg(os.msg.value))
            return os

      def BuildOwnershipObj(self, bl):
            osmsg = VariBytes().parse(bl.MerkleRoot(ObjList2BytesList(bl.payloads.value))).serialize()
            os    = Ownership()
            os.msg.parse(osmsg)
            os.pubkey.parse(self.GetPubKey())
            os.sig.parse(self.SignMsg(os.msg.value))
            return os
      
      def GetPubKey(self):
            if self.login:
                  return self.vk.to_string()
      
      def GetUTXOs(self, token = "aoc"):
            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  pp = VariStr(token.lower()).serialize() + VariStr(self.address).serialize()
                  func, payload = self.p2p.SendMsg(msgname="GetUTXOs", payload = pp, MyNode = self.MyNode)
            else:
                  return False
            if payload is not None:
                  utxo = json.loads(VariStr().deserialize(BytesIO(payload)).value)
                  if len(utxo) == 0:
                        return False
                  self.utxos[token] = utxo
                  return True
            return False
      
      def GetLedgerInfo(self):
            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  pp = VariBytes(b'').serialize()
                  func, payload = self.p2p.SendMsg(msgname="GetLedgerInfo", payload = pp, MyNode = self.MyNode)
            else:
                  return False
            if payload is not None:
                  self.ledgerinfo = json.loads(VariStr().deserialize(BytesIO(payload)).value)
                  return True
            return False

      def GetBlock(self, height):
            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  pp = VariInt(height).serialize()
                  func, payload = self.p2p.SendMsg(msgname="GetBlock", payload = pp, MyNode = self.MyNode)
            else:
                  return None
            if payload is not None:
                  stream   = BytesIO(payload)
                  return aiptool.GetObj(VariStr().deserialize(stream).value)().deserialize(stream)
      
      def GetPool(self, ltype = "Law"):
            pp = VariStr(ltype).serialize()
            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  func, payload = self.p2p.SendMsg(msgname="GetPool", payload = pp, MyNode = self.MyNode)
            else:
                  return None
            if payload is not None:
                  plist = VariList().deserialize(BytesIO(payload)).value
                  return plist
            return None

      def SendOwnership(self, msg):
            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  os = Ownership()
                  os.msg.parse(msg)
                  os.pubkey.parse(self.GetPubKey())
                  os.sig.parse(self.SignMsg(os.msg.value))
                  return self.p2p.SendMsg(msgname = "OwnershipIn", payload = os.serialize(), MyNode = self.MyNode)
            else:
                  return None, None
      
      def SendBlock(self, bkobj):
            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  return self.p2p.SendMsg(msgname = "BlockIn", payload = bkobj.serialize(), broadcast = True, MyNode = self.MyNode)
            else:
                  return None, None
      
      def SendLaw(self, LawName, LawContent, LawType):
            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  la = Law()
                  la.LawName.parse(LawName)
                  la.LawContent.parse(LawContent)
                  la.LawType.parse(LawType)
                  la.expiretime.parse(int(time.time()) + 200000)
                  return self.p2p.SendMsg(msgname = "LawIn", payload = la.serialize(), MyNode = self.MyNode)
            else:
                  return None, None

      
      def SendTxGate(self, add_to, amount = 1, token = "aoc", fee = 1, txrealid = "none", ifwithdraw = False):
            if amount <=0 or fee <=0 or token.lower() == "aoc":
                  return False
            pubkey = self.vk.to_string()
            tg = Transaction_Gate()
            tg.expiretime.parse(int(time.time()) + 200000)
            tg.token.parse(token.lower())
            tg.fee.parse(fee)
            tg.txrealid.parse(txrealid)
            tg.ownerpubkey.parse(pubkey)
            
            wdlist = [] #withdraw list
            if ifwithdraw:
                  for utoxi in self.utxos[token.lower()]:
                        if utoxi['status'] == 1:
                              #total += utoxi['am']
                              ainput  = Input()
                              ainput.blockheight.parse(utoxi['bh'])
                              ainput.txheight.parse(utoxi['th'])
                              ainput.opheight.parse(utoxi['oh'])
                              ainput.pubkey.parse(pubkey)
                              wdlist.append(ainput)
            tg.withdraw.parse(wdlist)
            
            oplist  = []
            if add_to !="":
                  aoutput = Output()
                  aoutput.amount.parse(amount)
                  aoutput.aocaddress.parse(add_to)
                  oplist.append(aoutput)
            tg.deposit.parse(oplist)
            
            msg1, msg2 = tg.GetMsgSig()
            tg.sig.parse(self.SignMsg(msg1))
            
            ##remind after sig updated, msg2 should be changed
            msg1, msg2 = tg.GetMsgSig()
            tg.ownerships.parse([self.BuildOwnershipObjForAocpay(msg2)])

            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  return self.p2p.SendMsg(msgname = "TxIn", payload = tg.serialize(), MyNode = self.MyNode)
            else:
                  return None, None

      def IntegratTokenPay(self, fee, token):
            return self.SendTokenPay(self.address, fee = fee, txid = 2, token = token)
      
      def SendTokenPay(self, add_to, amount = 1, fee = 1, txid = 1, token = 'aoc'):
            if amount <= 0 or fee <= 0 or txid <= 0:
                  return False
            amount, fee = int(amount), int(fee)
            aoctx  = Transaction_Pay()
            aoctx.expiretime.parse(int(time.time()) + 200000)
            aoctx.token.parse(token.lower())
            
            total  = 0
            idlist = []
            for i, utoxi in enumerate(self.utxos[token]):
                  if utoxi['status'] == 1:
                        if total <= (amount + fee) or txid == 2:
                              total += utoxi['am']
                              idlist.append(i)
            if len(idlist) < 1:
                  return False
            if total < (amount + fee):
                  return False
            
            ainputlist = []
            for idd in idlist:
                  ainput  = Input()
                  ainput.blockheight.parse(self.utxos[token][idd]['bh'])
                  ainput.txheight.parse(self.utxos[token][idd]['th'])
                  ainput.opheight.parse(self.utxos[token][idd]['oh'])
                  ainput.pubkey.parse(self.vk.to_string())
                  ainputlist.append(ainput)
                  self.utxos[token][idd]['status'] = 0
            aoctx.inputs.parse(ainputlist)
            
            aoutputlist = []
            if txid == 2:
                  aoutput = Output()
                  aoutput.amount.parse(int(total - fee))
                  aoutput.aocaddress.parse(self.address)
                  aoutputlist.append(aoutput)
            elif txid == 1:
                  aoutput = Output()
                  aoutput.amount.parse(int(amount))
                  aoutput.aocaddress.parse(add_to)
                  aoutputlist.append(aoutput)
                  if total > (amount + fee):
                        a1output = Output()
                        a1output.amount.parse(int(total - amount - fee))
                        a1output.aocaddress.parse(self.address)
                        aoutputlist.append(a1output)
            aoctx.outputs.parse(aoutputlist)

            ##add sig
            msgsig = aoctx.GetMsgSig()
            sigslist = []
            if txid == 2:
                  sigslist.append(VariBytes().parse(self.SignMsg(msgsig)))  
            elif txid == 1:
                  for i in range(len(aoctx.inputs)):
                        sigslist.append(VariBytes().parse(self.SignMsg(msgsig)))
            aoctx.sigs.parse(sigslist)
            
            # send msg
            #print("inputlength: ", len(aoctx.inputs))
            #print("outputslength: ", len(aoctx.outputs))
            #print("sigslength: ", len(aoctx.sigs))
            if self.p2p.Connect(MyNode = self.MyNode)[0]:
                  return self.p2p.SendMsg(msgname = "TxIn", payload = aoctx.serialize(), MyNode = self.MyNode)
            else:
                  return None, None
      