import os
import time
import json
from hashlib import sha3_256
import socket
import socketserver
from src.common.datatype import *
from src.RPC import AocRPC
from src.tool import *


def _handlerecv(request):
    msgh, payload = None, None
    # self.request is the TCP socket connected to the client
    try:
        data = request.recv(1024*2)
        msgh, payload = UnPackMsg(data)
    except:
        #request.sendall(PackMsg("unknown", VariStr("bad data").serialize()))
        return False , msgh, payload
    if msgh is None:
        #request.sendall(PackMsg("unknown", VariStr("msg wrong").serialize()))
        return False , msgh, payload
    elif payload is None:
        total = (len(msgh.serialize()) + msgh.var_length.value)
        if total > 0:
            recvd = total-len(data)
            while(recvd>0):
                msgh, payload = None, None
                data += request.recv(recvd)
                recvd = total-len(data)
            #print("double recev data ",len(data))
            try:
                msgh, payload = UnPackMsg(data)
            except:
                #request.sendall(PackMsg("unknown", VariStr("bad data").serialize()))
                return False , msgh, payload
    if msgh is None or payload is None:
        #request.sendall(PackMsg("unknown", VariStr("bad data").serialize()))
        return False , msgh, payload
    return True , msgh, payload

def handle(request, rpc):
    re, msgh, payload = _handlerecv(request)
    #print(re, msgh, payload)
    if not re:
        request.sendall(PackMsg("unknown", VariStr("bad data").serialize()))
        return
    func = msgh.var_msgname.value
    # just send the padyload
    #print("good msg: ", func)
    handle_func = getattr(rpc, func, None)
    if handle_func:
        try:
            res = handle_func(payload)
            request.sendall(res)
            #print(str("handle,"+func), len(res))
            return
        except Exception as e:
            print(str(e))
            request.sendall(PackMsg(func, VariStr("handle msg wrong").serialize()))
            return
    else:
        request.sendall(PackMsg(func, VariStr("rpc don't support this msg").serialize()))
        return


class p2p_client:
    def __init__(self, addr = "localhost", port = 4242):
        self.node = [{'address': addr, 'port': port}]
        self.node.extend(self.ReadNode())
        self.sockpool = []
    
    def ReceiveMsg(self, sock):
        re, msgh, payload = _handlerecv(sock)
        #print(re, msgh, payload)
        if not re:
            return None, None
        return msgh.var_msgname.value, payload
        
    
    def SendMsg(self, msgname = "PING_AOC", payload = None, broadcast = False, MyNode = False):
        #if not broadcast, need receive feedback
        if payload is None:
            payload = VariBytes(b'').serialize()
        return self._SendData(PackMsg(msgname, payload), broadcast, MyNode)
    
    def _SendData(self, data, broadcast = False, MyNode = False):
        #if not broadcast, need receive feedback
        total  = len(data)
        ifsend = False
        sendnodenum = 0
        for i, sock in enumerate(self.sockpool):
            try:
                if MyNode and i>0:
                    return None, None
                sendcounts = 0
                while sendcounts < total:
                    sendcounts += sock.send(data[sendcounts:])
                #print(str("send data,"), total)
                #sendcounts += sock.sendall(data)
                ifsend = True
                sendnodenum += 1
                try:
                    return self.ReceiveMsg(sock)
                except:
                    continue
            except:
                continue
        return sendnodenum, None
    
    def Connect(self, nodecount = 1, MyNode = False):
        self.sockpool = []
        ifconn  = False
        for i, nodei in enumerate(self.node):
            if (not MyNode) and i ==0:
                continue
            try:
                if MyNode and i>0:
                    return ifconn, len(self.sockpool)
                print("try to connect node: ", nodei['address'], nodei['port'])
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((nodei['address'], nodei['port']))
                ifconn  = True
                self.sockpool.append(sock)
            except:
                time.sleep(0.2)
            if len(self.sockpool) >= nodecount:
                return ifconn, len(self.sockpool)
        return ifconn, len(self.sockpool)

    def ReadNode(self):
        with open('node.json', 'r') as f:
            node = json.load(f)
            return node
    
    def SaveNode(self):
        with open('node.json', 'w') as f:
            json.dump(self.node, f)
            return



class p2p_node(socketserver.TCPServer):
    def __init__(self, addr = "0.0.0.0", port = 4242):
        super().__init__((addr, port), RequestHandlerClass = None, bind_and_activate=True)
        print("server is on ", addr , " ", port)
        self.rpc = AocRPC()
        self.run = True
        while self.run:
            request_socket, address_port_tuple = self.get_request()
            try:
                handle(request_socket, self.rpc)
            except:
                pass
