#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kivy.app import App
from os.path import dirname, join
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivy.config import Config
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from wallet_inter import WalletInter
import os
from datetime import datetime
import time
import copy
from hashlib import sha3_256
from aip.aip0.aip0_0 import *
import pyperclip
import _thread
from wallet.miner import miner


class ShowcaseScreen(Screen):
    fullscreen = BooleanProperty(False)
    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(ShowcaseScreen, self).add_widget(*args)

class tpstx:
    token = ""
    w = 0
    d = 0
    address = ""
    amount = 0

class aocdesktopApp(App):
    curdir = dirname(__file__)
    icon = join(curdir,"aoc.ico")
    title = 'Aoc Wallet'
    screen_names   = ListProperty([])
    screenindex    = ListProperty([])
    index          = NumericProperty(0)
    mainwalletaddr = StringProperty()
    current_title  = StringProperty()
    
    sendlaw_1 = NumericProperty(-1)
    
    wi     = WalletInter()
    mr     = miner()
    
    tpssending = False
    tps = 0
    tpstx1 = tpstx()

    def build(self):
        self.lawlist = {}
        
        self.screens = {}
        self.screenindex = []
        self.screen_names = ['Message', 'Operation','Wallet', 'Account', 'SendLaw', \
                            'SendOwnership','LedgerInfo','Mining','PayToken','WithdrawDepositToken',\
                            'TradeBroadcast','Test']
        curdir = dirname(__file__)
        self.available_screens = [join(curdir,'AocDesktop','data', 'screen',fn.lower()+'.kv') for fn in self.screen_names]
        self.goto_screen(0)
        self.widthmain = 100
        def win_cb(window, width, height):
            Config.set('graphics', 'width', str(width))
            Config.set('graphics', 'height', str(height))
            Config.write()
            if self.widthmain != width:
                self.widthmain = width
                Window.size = (self.widthmain, int(self.widthmain/0.75))
        Window.bind(on_resize=win_cb)
    
    def MiningFunc_m(self):
        self.mr.Update_Wallet(self.wi.wc)
        self.mr.hashing = True
        while self.mr.hashing:
            if self.mr.StartMing():
                pass
            else:
                self.mr.Update_Wallet(self.wi.wc)
                time.sleep(10)
    
    def MiningFunc(self, down = 0):
        if down == 1:
            self.mr.hashing = False
            gminer = _thread.start_new_thread(self.MiningFunc_m,())
        else:
            self.mr.hashing = False
        return
    
    def tps_m(self):
        while self.tpssending:
            a = time.monotonic()
            for i in range(self.tps):
                self.wi.SendWithdrawDeposit(self.tpstx1.token,self.tpstx1.w,self.tpstx1.d,self.tpstx1.address,self.tpstx1.amount)
            b = time.monotonic()
            if (b-a) < 1:
                time.sleep(1-b+a)
    ####
    def testtps(self, tps):
        self.tpssending = False
        self.tps = int(tps)
        time.sleep(1)
        self.tpssending = True
        _thread.start_new_thread(self.tps_m,())
    ####

    def loginwallet(self):
        for i, wci in enumerate(self.wi.wclist): 
            if self.mainwalletaddr.strip() == wci.address:
                self.wi.SetMainWallet(i)
                return
    
    def createwallet(self, seedstr, login = 0):
        if seedstr != "":
            self.wi.addWallet(seedstr)
        wallist = self.root.ids.sm.get_screen('Wallet').ids.walletlist
        wallist.clear_widgets()

        def btnclick(*args):
            self.mainwalletaddr = args[0].text
            pyperclip.copy(self.mainwalletaddr.strip())
        
        for i, wci in enumerate(self.wi.wclist):
            button = ToggleButton(text = wci.address,font_size='12dp',size_hint_y=None,  group="wal",height=40, \
                                 on_press=lambda *args: btnclick(*args))
            wallist.add_widget(button)
        self.root.ids.sm.get_screen('Wallet').ids.walheight.height = i*40 + 320
    
    
    def LedgerInfoText(self):
        str1  = "NO Info"
        if self.wi.GetLedgerInfo():
            str1  = ""
            str1 += "Block Height: "+ str(self.wi.wc.ledgerinfo['BlockHeight']) +"\n"
            str1 += "Chain info: "+ str(self.wi.wc.ledgerinfo['ChainInfo']) +"\n"
            str1 += "Pool info: "+ str(self.wi.wc.ledgerinfo['PoolInfo']) +"\n"
            str1 += "AipInfo: \n"
            for item in self.wi.wc.ledgerinfo['AipDic']:
                str1 += str(item) +"\n"
        return str1


    def SendToken(self, txid):
        def Confrim(*arg):
            backstr    = "feedback@ "+ datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
            popup.dismiss()
            if txid == 1:
                backstr    += str(self.wi.SendToken(address, amount, token = token, txid = 1))
            if txid == 2:
                backstr    += str(self.wi.SendToken(token = token, txid = 2))
            self.root.ids.sm.get_screen('PayToken').ids.feedback.text = backstr
            return
        def Cancel(*arg):
            popup.dismiss()
            return
        token   = self.root.ids.sm.get_screen('PayToken').ids.btn.text
        if txid == 1:
            try:
                address = self.root.ids.sm.get_screen('PayToken').ids.addrinput.text.strip()
                amount  = int(1000000*float(self.root.ids.sm.get_screen('PayToken').ids.aminput.text.strip()))
                status  = True
            except:
                backstr = "feedback@ "+ datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"+ str("input is not correct.") 
                status  = False
            if not Wallet.VerifyAddress(address):
                backstr = "feedback@ "+ datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"+ str("Address is not valid.") 
                status  = False
            if not status:
                self.root.ids.sm.get_screen('PayToken').ids.feedback.text = backstr
                return
        box = BoxLayout(orientation="vertical")
        if txid == 1:
            lb = Label(text = 'From address: \n' + self.wi.wc.address +"\n"+ "To address: \n"+address+"\n"+"amount: "+str(amount/1000000)+" "+token)
        if txid == 2:
            lb = Label(text = 'From address: \n' + self.wi.wc.address +"\n"+ "Integrating token\n")
        buttonok = Button(text="Confirm", on_press=Confrim, size_hint_y=None, height=40)
        buttonca = Button(text="Cancel", on_press=Cancel, size_hint_y=None, height=40)
        lb.font_size = str(max(10, int(buttonok.width*0.07 + 6)))+"dp"
        box.add_widget(lb)
        box.add_widget(buttonok)
        box.add_widget(buttonca)
        box.add_widget(Widget(size_hint=(0.8, 0.8)))
        popup = Popup(title='Payment Confirm',content=box,size_hint = (1.0, 0.7))
        popup.open()
        return

    def SendWithdrawDeposit(self, times = 1):
        token  = self.root.ids.sm.get_screen('WithdrawDepositToken').ids.btn.text
        if token not in ('eur','usd','rmb'):
            return "token is wrong"
        w, d = 0,0
        if self.root.ids.sm.get_screen('WithdrawDepositToken').ids.withdraw.state == "down":
            w = 1 
        if self.root.ids.sm.get_screen('WithdrawDepositToken').ids.deposit.state == "down":
            d = 1
            address = self.root.ids.sm.get_screen('WithdrawDepositToken').ids.addrinput.text.strip()
            try:
                amount  = int(1000000*float(self.root.ids.sm.get_screen('WithdrawDepositToken').ids.aminput.text.strip()))
            except:
                amount  = -1
            
            str1 = ""
            self.tpstx1.token = token
            self.tpstx1.w = w
            self.tpstx1.d = d
            self.tpstx1.address = address
            self.tpstx1.amount  = amount
            for i in range(times):
                str1 += str(i)+":"+str(self.wi.SendWithdrawDeposit(token,w,d,address,amount))
            return str1
        return str(self.wi.SendWithdrawDeposit(token,w,d))


    def SelectTokenToPay(self, token, scr = "PayToken"):
        self.root.ids.sm.get_screen(scr).ids.btn.text = token.lower()
        uolist = self.wi.GetUTXOs(token.lower())
        amount = 0
        if uolist is not None:
            for uo in uolist:
                if uo['am'] is not None:
                    amount += uo['am']
        amount = "{:.6f}".format(amount/1000000)
        self.root.ids.sm.get_screen(scr).ids.tokenamount.text = "[b]{}[/b]".format(amount)
        self.root.ids.sm.get_screen(scr).ids.tokenamount.font_size = str(max(5, 22 - int(len(amount)*0.35)))+"dp"
        return


    def send_ownership_lawblock(self, type):
        if self.wi.GetLedgerInfo():
           #bkobj = self.wi.GetBlock(self.wi.wc.ledgerinfo['BlockHeight'])
            CurrentHash = bytes.fromhex(self.wi.wc.ledgerinfo['CurrentHash'])
           #if bkobj is not None:
                #prehash = bkobj.Hash()
            bl = Block()
            bl.preblock.parse(CurrentHash)
            bl.timestamp.parse(int(time.time()))
            bl.payloads.parse([law for key, law in self.lawlist.items()])
            os = self.wi.BuildOwnershipObj(bl)
            if type == 0:
                return self.wi.wc.SendOwnership(os.msg.value)
            if type == 1:
                bl.ownerships.parse([os])
                return self.wi.wc.SendBlock(bl) 
        return
    
    def GetPayloadList(self):
        lawlist = self.wi.GetPayloadList(ltype = "Law")
        if lawlist is None:
            return
        def buttonpress(*args):
            lname = args[0].text.replace("\n", "").replace("\n", "")
            str1 = "Hash: "+ lname
            str2 = "Type: "+ str(self.lawlist[lname].LawType.value)
            str3 = "Name: "+self.lawlist[lname].LawName.value
            str4 = "Content: "+self.lawlist[lname].LawContent.value
            str5 = "Expire: "+datetime.fromtimestamp(self.lawlist[lname].expiretime.value).strftime('%Y-%m-%d %H:%M:%S') 
            self.root.ids.sm.get_screen('SendOwnership').ids.showpayload.text = str1+"\n"+str2+"\n"+str3+"\n"+str4+"\n"+str5

        self.root.ids.sm.get_screen('SendOwnership').ids.payloadlist.clear_widgets()
        self.lawlist = {}
        for i, law in enumerate(lawlist):
            name   = sha3_256(law.serialize()).hexdigest()
            self.lawlist[name] = law
            firstpart, secondpart = name[:int(len(name)/2)], name[int(len(name)/2):]
            nameb  = firstpart + '\n' + secondpart
            button = ToggleButton(text = nameb,font_size='12dp',size_hint_y=None, height=40, on_press=lambda *args: buttonpress(*args))
            self.root.ids.sm.get_screen('SendOwnership').ids.payloadlist.add_widget(button)
    

    def sendlaw(self):
        if self.sendlaw_1 in (0,1):
            lawtype = self.sendlaw_1
            lawname = self.root.ids.sm.get_screen('SendLaw').ids.lawnameinput.text
            lawcontent = self.root.ids.sm.get_screen('SendLaw').ids.lawcontentinput.text
            backstr    = "feedback@ "+ datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n"
            backstr    += str(self.wi.wc.SendLaw(lawname, lawcontent, lawtype))
            self.root.ids.sm.get_screen('SendLaw').ids.feedback.text = backstr
        return
    
    def go_next_screen(self):
        try:
            if self.index < len(self.screenindex) - 1:
                self.index = self.index + 1
                self.root.ids.sm.switch_to(self.load_screen(self.screenindex[self.index]), direction='left')
                self.showicon(self.screenindex[self.index])
        except:
            return
    
    def go_previous_screen(self):
        try:
            if self.index > 0:
                self.index = self.index - 1
                self.root.ids.sm.switch_to(self.load_screen(self.screenindex[self.index]), direction='left')
                self.showicon(self.screenindex[self.index])
        except:
            return

    def showicon(self, idx):
        self.root.ids.msgb.icon = 'AocDesktop/data/icon/msg.png'
        self.root.ids.opeb.icon = 'AocDesktop/data/icon/ope.png'
        self.root.ids.walb.icon = 'AocDesktop/data/icon/wal.png'
        self.root.ids.accb.icon = 'AocDesktop/data/icon/acc.png'
        if idx == 0:
            self.root.ids.msgb.icon = 'AocDesktop/data/icon/msg_c.png'
        elif idx == 1:
            self.root.ids.opeb.icon = 'AocDesktop/data/icon/ope_c.png'
        elif idx == 2:
            self.root.ids.walb.icon = 'AocDesktop/data/icon/wal_c.png'
        elif idx == 3:
            self.root.ids.accb.icon = 'AocDesktop/data/icon/acc_c.png'

    def goto_screen(self, idx):
        try:
            self.root.ids.sm.switch_to(self.load_screen(idx), direction='left')
            self.screenindex.append(idx)
            self.index = len(self.screenindex) - 1
        except:
            return
        self.showicon(idx)
    
    def load_screen(self, index):
        self.current_title = self.screen_names[index]
        if index in self.screens:
            return self.screens[index]
        screen = Builder.load_file(self.available_screens[index])
        self.screens[index] = screen
        return screen


if __name__ == "__main__":
    #curdir = dirname(__file__)
    #os.environ['KIVY_HOME'] = join(curdir,"configaoc.ini")
    #Config.read("configaoc.ini")

    #Window.borderless = True
    #Config.set('kivy','window_icon',join(curdir,"aoc.ico"))
    #Config.write()
    #os.environ['KIVY_IMAGE'] = 'sdl2'
    app = aocdesktopApp()
    app.run()
