import sqlite3
from io import BytesIO
from src.common import aiptool
from src.blockheader import HeaderNode
from src.common.datatype import VariBytes, VariStr, VariInt, VariList


class utxoclass:
    def __init__(self):
        self.bkheight = 0
        self.txheight = 0
        self.opheight = 0
        self.amount   = 0
        self.address  = ""
        self.token    = "aoc"
    def __eq__(self, other):
        return (self.__dict__ == other.__dict__)
    def parse(self, bk=0,tx=0,op=0,am=0,addr="", token="aoc"):
        self.bkheight, self.txheight, self.opheight, self.amount, self.address, self.token = bk,tx,op,am,addr,token
        return self

class DatabaseMain:
    def __init__(self, network = "mainnet"):
        ## 1. Connect Database
        self.conn_g = sqlite3.connect('globalinfo_'+network+'.db')
        self.conn_b = sqlite3.connect('blockDATA_' +network+'.db')
        
        ## 2. Database Status
        re, msg = self.OpenCreateDatabaseTable()
        
        ## 3. current height
        self.bkheight  = self.API_GetLatestBlockHeight()
        if self.bkheight == -1:
            with self.conn_g:
                aiplist = [("aip0.aip0_0.Block", "Block", 0), ("aip0.aip0_0.Law", "Law", 0),\
                            ("aip0.aip0_0.Ownership", "Ownership", 0),("aip0.aip0_0.Wallet", "Wallet", 0),\
                            ("aip0.aip0_0.Chain", "Chain", 0),("aip1.aip1_0.Input", "Input", 0),("aip1.aip1_0.Output", "Output", 0),\
                            ("aip1.aip1_0.Transaction_Pay", "Transaction_Pay", 0),("aip2.aip2_0.Transaction_Gate", "Transaction_Gate", 0)]
                self.conn_g.executemany("INSERT OR REPLACE INTO "+" aip_height_dic "+"(aippath, aip_head, height_creation)\
                VALUES(?,?,?)",(aiplist))
                self.conn_g.execute("INSERT OR REPLACE INTO "+" aocpay "+"(aocaddress, height_creation) VALUES(?,?)",("A2Qw5gKjX4k9SPSbZ4zmGS7EiQgfdrp86CHa58CpVhPkBYYoa2d", 0,))

            
            uc = utxoclass().parse(0,0,0,100_000000_000000,"A2Qw5gKjX4k9SPSbZ4zmGS7EiQgfdrp86CHa58CpVhPkBYYoa2d","aoc")
            self.SaveUtxo(uc)
        
        ## 4. aip dictionary, aocpay owner dic
        self.aipdic    = self.API_GetAipDic()
        self.aocpaydic = self.API_GetAocpayDic()
        print(self.aipdic, self.aocpaydic)
        
        ## 5. Get Latest Chain
        self.Chain  = aiptool.GetObjFromNameAndHeight("Chain",self.aipdic)()
        if self.Read100Blocks2Chain():
            print("Load Block Correct, height:",self.bkheight)
        else:
            print("Block Database is wrong")
    

    def SaveDeleteUtxos(self, ucs, save = 1):
        #utxoclass
        tables = {}
        for uc in ucs:
            tablename = "utxo_" + uc.token.lower()
            if tablename not in tables:
                tables[tablename] = []
            tables[tablename].append(uc)
        try:
            with self.conn_g:
                for tablename, ucs in tables.items():
                    if save == 1:
                        self.conn_g.executemany("INSERT OR REPLACE INTO "+ tablename + " (block_height, tx_height, out_height, amount, address) \
                        VALUES(?,?,?,?,?)",[(uc.bkheight,uc.txheight,uc.opheight,uc.amount,uc.address) for uc in ucs])
                    elif save == 0:
                        self.conn_g.executemany("DELETE FROM "+ tablename+" WHERE block_height = ? AND tx_height = ? \
                        AND out_height = ?", [(uc.bkheight,uc.txheight,uc.opheight) for uc in ucs])
            return True
        except:
            return False

    def SaveUtxo(self, uc):
        #utxoclass
        tablename = "utxo_" + uc.token.lower()
        try:
            with self.conn_g:
                self.conn_g.execute("INSERT OR REPLACE INTO "+ tablename + " (block_height, tx_height, out_height, amount, address) \
                 VALUES(?,?,?,?,?)",[uc.bkheight,uc.txheight,uc.opheight,uc.amount,uc.address])
            return True
        except:
            return False

    def API_GetUtxoAmount(self, token = "aoc", address = b"", pubkey = b"", ListMode = False):
        #"""get the total aoc amount of the address has"""
        if address == b"" and pubkey != b"":
            Wallet  = aiptool.GetObjFromNameAndHeight("Wallet",self.aipdic)
            address = Wallet.AddressFromPubKey(pubkey)
        tablename = "utxo_" + token
        utxolist  = self.conn_g.execute("SELECT block_height, tx_height, out_height, amount FROM "+ tablename+" WHERE address = ?",(address,)).fetchall()
        if ListMode:
            return utxolist
        amount    = 0
        for utxo in utxolist:
            amount = amount + utxo[3]
        return amount
    
    def Get1Utxo(self, token, input):
        ##for one Record
        tablename = "utxo_" + token #block_height, tx_height, out_height,
        record = self.conn_g.execute("SELECT amount, address FROM "+ tablename+" WHERE block_height = ? AND tx_height = ? \
        AND out_height = ?", (input.blockheight.value,input.txheight.value,input.opheight.value)).fetchall()
        return (record[0][0], record[0][1]) if len(record) == 1 else (0, "")
    
    def API_GetAocpayOwner(self):
        return aiptool.GetAocpayAddressFromHeight(self.aocpaydic, self.bkheight)

    def API_GetAocpayDic(self):
        return self.conn_g.execute("SELECT aocaddress, height_creation FROM aocpay").fetchall()

    def API_GetAipDic(self):
        return self.conn_g.execute("SELECT aippath, aip_head, height_creation FROM aip_height_dic").fetchall()

    def API_GetLatestBlockHeight(self):
        tables = self.conn_b.execute("SELECT name FROM sqlite_master WHERE type='table' ").fetchall()
        maxtable = 0
        for tablei in tables:
                table    = tablei[0]
                if table[0]  == 'b':
                    maxtable = max(int(table[1:]), maxtable)
        tablename = 'b' + str(maxtable)
        height    = self.conn_b.execute("SELECT height FROM " + tablename + " ORDER BY height DESC LIMIT 1").fetchone()
        return -1 if height is None else (height[0])

    def Read100Blocks2Chain(self):
        s = self.bkheight - 99
        s = 0 if s<0 else s
        for i in range(s, self.bkheight + 1):
            if not self.Chain.AddHeaderObj(self.LoadBlock(i, headermodel = True)):
                return False
        return True
    
    def CheckAocpayOwnership(self, bkheight, txs):
        wallet     = aiptool.GetObjFromNameAndHeight("Wallet", self.aipdic)
        aocpayaddr = aiptool.GetAocpayAddressFromHeight(self.aocpaydic, bkheight)
        for tx in txs:
            if tx.aipname.value == "aip2.aip2_0.Transaction_Gate":
                if len(tx.ownerships) > 0:
                    ##check aoc stakes
                    POS = 0
                    for os in tx.ownerships:
                        POS += self.API_GetUtxoAmount(pubkey = os.pubkey.value)
                    if POS < 62*1000000_000000:
                        return False, "no enough fund to depoist or withdraw real token"
                    else:
                        continue
                elif aocpayaddr != wallet.AddressFromPubKey(tx.ownerpubkey.value):
                    return False, "your address is not aocpay address"
        return True, "aocpay success"


    def _manage_utxo(self, owneraddr, payloads,bkheight):
        utxo_in   = []
        utxo_out  = []
        fees      = dict()
        for txh, pl in enumerate(payloads):
            token = pl.token.value.lower()
            if pl.aipname.value == "aip2.aip2_0.Transaction_Gate":
                inputs  = pl.withdraw
                outputs = pl.deposit
                fee,amounti,amounto = pl.fee.value,0,0
            if pl.aipname.value == "aip1.aip1_0.Transaction_Pay":
                inputs  = pl.inputs
                outputs = pl.outputs
                fee,amounti,amounto = 0,0,0
            for ip in inputs:
                (amount, addr) = self.Get1Utxo(token, ip)
                if addr != "":
                    ipu = utxoclass().parse(ip.blockheight.value, ip.txheight.value, ip.opheight.value, amount, addr, token)
                    if ipu in utxo_in:
                        return False, "Double spent found", utxo_in, utxo_out
                    utxo_in.append(ipu)
                    amounti += amount
            for oph, op in enumerate(outputs):
                opu = utxoclass().parse(bkheight+1, txh+1, oph, op.amount.value, op.aocaddress.value, token)
                utxo_out.append(opu)
                amounto += op.amount.value
            if pl.aipname.value == "aip1.aip1_0.Transaction_Pay":
                fee = amounti - amounto
            if fee < 1:
                return False, "Invalid TX inluded, no enough amount inputs", utxo_in, utxo_out
            if token not in fees.keys():
                fees[token] = 0
            fees[token] += fee
        for token, value in fees.items():
            ow  = utxoclass().parse(bkheight+1, 0, 0, value, owneraddr, token)
            utxo_out.append(ow)
        return True, "good txs", utxo_in, utxo_out
    

    def API_CheckTxsIfValid(self, txs):
        re,msg,uin,uout = self._manage_utxo("", txs, self.bkheight)
        if re:
            ##check aocpay onwership
            re, msga = self.CheckAocpayOwnership(self.bkheight, txs)
            msg     += msga 
        return re, msg


    def CheckUtxoList(self, bkheight, bkobj):
        wallet    = aiptool.GetObjFromNameAndHeight("Wallet",self.aipdic)
        owneraddr = wallet.AddressFromPubKey(bkobj.ownerships.value[0].pubkey.value)
        return self._manage_utxo(owneraddr, bkobj.payloads, bkheight)
    

    def VerifyBlockOnChain(self, bkobj, addheader = True):
        POS = 0
        if bkobj.blocktype.value <= 1:
            for os in bkobj.ownerships.value:
                POS += self.API_GetUtxoAmount(pubkey = os.pubkey.value)
        header  = HeaderNode().parse(bkobj)
        re, msg = self.Chain.Verification(header, POS)
        if re:
            ##1. if is transaction block, check double spent
            utxo_in  = []
            utxo_out = []
            if bkobj.blocktype.value == 2:
                reu, msgu, utxo_in, utxo_out = self.CheckUtxoList(self.bkheight, bkobj)
                if reu:
                    print(msgu+"good utxo update")
                else:
                    print("False Block")
                    return reu, msgu
                ##2.if reality token, need check aocpay ownership
                rea, msga = self.CheckAocpayOwnership(self.bkheight, bkobj.payloads)
                msg += msga
                if not rea:
                    return rea, msg
            ##3.finally it can be saved
            if self.SaveBlock(self.bkheight, bkobj, utxo_in, utxo_out):
                self.bkheight += 1
                if addheader:
                    print("add header re: ", self.Chain.AddHeaderObj(header))
                print(bkobj.Hash())
        return re, msg
    
    def LoadBlock(self, heightin, headermodel = False):
        if heightin < 0:
            return None
        tablename = "b" + str(int(heightin/100000))
        with self.conn_b:
            bkdata = self.conn_b.execute("SELECT height, DATA FROM " + tablename + " WHERE height = ?", (heightin,)).fetchone()
            stream = BytesIO(bkdata[1])
            bkobj  = aiptool.GetObj(VariStr().deserialize(stream).value)().deserialize(stream)
            if headermodel:
                return HeaderNode().parse(bkobj)
            return bkobj
    
    def SaveAocpayDic(self, height, bkobj):
        wallet  = aiptool.GetObjFromNameAndHeight("Wallet",self.aipdic)
        addr    = ""
        for tx in bkobj.payloads:
            if tx.aipname.value == "aip2.aip2_0.Transaction_Gate":
                if len(tx.ownerships) > 0:
                    addr = wallet.AddressFromPubKey(tx.ownerpubkey.value)
        if addr != "" and wallet.VerifyAddress(addr):
            try:
                with self.conn_g:
                    self.conn_g.execute("INSERT OR REPLACE INTO "+" aocpay "+"(aocaddress, height_creation)\
                            VALUES(?,?)",(addr, height,))
            except:
                return False

    
    def SaveBlock(self, height, bkobj, utxo_in, utxo_out):
        height += 1 
        try:
            with self.conn_b:
                tablename = "b" + str(int(height/100000))
                if height % 100000 == 0:
                    self.conn_b.execute("CREATE TABLE IF NOT EXISTS " + tablename + "(height INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, DATA BLOB)")
                self.conn_b.execute("INSERT OR REPLACE INTO "+ tablename + "(height, DATA) VALUES(?,?)", (height, bkobj.serialize()))
            if bkobj.blocktype.value <= 1:
                with self.conn_g:
                    aiplist = [(la.LawName.value, la.LawName.value.split(".")[2], self.bkheight + 1) for la in bkobj.payloads]
                    self.conn_g.executemany("INSERT OR REPLACE INTO "+" aip_height_dic "+"(aippath, aip_head, height_creation)\
                                VALUES(?,?,?)",(aiplist))
                self.aipdic = self.API_GetAipDic()
            if bkobj.blocktype.value == 2:
                self.SaveDeleteUtxos(utxo_in,save=0)
                self.SaveDeleteUtxos(utxo_out,save=1)
                self.SaveAocpayDic(height, bkobj)
                self.aocpaydic = self.API_GetAocpayDic()
            return True
        except:
            return False

    def OpenCreateTokenTable(self, token_name):
        tablename = "utxo_"+token_name
        with self.conn_g:
            self.conn_g.execute("CREATE TABLE IF NOT EXISTS " + tablename + " (block_height INTEGER, tx_height INTEGER,\
                                out_height INTEGER, amount INTEGER, address TEXT, unique (block_height, tx_height, out_height) )")

    def OpenCreateDatabaseTable(self):
        try:
            #create the block database
            with self.conn_b:
                self.conn_b.execute("CREATE TABLE IF NOT EXISTS " + "b0" + "(height INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, DATA BLOB)")
            #create the globalinfo aip_height_dic table
            with self.conn_g:
                self.conn_g.execute("CREATE TABLE IF NOT EXISTS " + "aip_height_dic"+ "(aippath TEXT PRIMARY KEY UNIQUE,\
                                        aip_head TEXT, height_creation INTEGER)")
                self.conn_g.execute("CREATE TABLE IF NOT EXISTS " + "aocpay"+ "(aocaddress TEXT PRIMARY KEY UNIQUE, height_creation INTEGER)")
            #create the globalinfo token table
            self.OpenCreateTokenTable("aoc")
            self.OpenCreateTokenTable("eur")
            self.OpenCreateTokenTable("usd")
            self.OpenCreateTokenTable("rmb")
        except sqlite3.IntegrityError:
            return False, "DATABASE CREATE TABLE IF NOT EXISTS False!"
        return True, "DATABASE CREATE TABLE IF NOT EXISTS True!"
            
  
