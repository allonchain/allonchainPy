#!/usr/bin/env python
# -*- coding: utf-8 -*-
import struct
from io import BytesIO
from codecs import encode, decode
from . import aiptool
#32-bit little-endian integer field
#datatype = "<i"

#32-bit little-endian unsigned integer field
#datatype = "<I"

#64-bit little-endian integer field
#datatype = "<q"

#64-bit little-endian unsigned integer field
#datatype = "<Q"

#16-bit little-endian integer field
#datatype = "<h"

#16-bit little-endian unsigned integer field
#datatype = "<H"

#16-bit big-endian unsigned integer field
#datatype = ">H"
MsgHeader_SIZE = 20

class VariInt:
    """A variable size integer field."""
    def __init__(self, intin = 0):
        self.value = intin

    def parse(self, value):
        self.value = value
        return self

    def __eq__(self, other):
        return (self.value == other.value)

    def deserialize(self, stream):
        int_id_raw = stream.read(struct.calcsize("<B"))
        int_id = struct.unpack("<B", int_id_raw)[0]
        if int_id == 0xFD:
            data  = stream.read(2)
            int_id  = struct.unpack("<H", data)[0]
        elif int_id == 0xFE:
            data = stream.read(4)
            int_id  = struct.unpack("<I", data)[0]
        elif int_id == 0xFF:
            data = stream.read(8)
            int_id = struct.unpack("<Q", data)[0]
        self.value = int_id
        return self
    
    def serialize(self):
        if self.value < 0xFD:
            return struct.pack("<B", self.value)
        if self.value <= 0xFFFF:
            return bytes([0xFD]) + struct.pack("<H", self.value)
        if self.value <= 0xFFFFFFFF:
            return bytes([0xFE]) + struct.pack("<I", self.value)
        return bytes([0xFF]) + struct.pack("<Q", self.value)

class VariStr:
    def __init__(self, strin = ""):
        self.value    = strin
        self.var_int  = VariInt(len(encode(self.value, 'utf-8')))

    def parse(self, value):
        self.value    = value
        self.var_int.parse(len(encode(self.value, 'utf-8')))
        return self

    def __eq__(self, other):
        return (self.value == other.value)

    def deserialize(self, stream):
        string_length = self.var_int.deserialize(stream).value
        string_data   = stream.read(string_length)
        self.value    = decode(string_data,'utf-8')
        return self

    def serialize(self):
        return self.var_int.serialize() + encode(self.value, 'utf-8')

    def __len__(self):
        return len(self.serialize())

class MsgHeader:
    ##used for p2p network
    ##Check maximum msg header should < 20 bytes
    def __init__(self, msgname = "" , lenght = 0):
        self.var_msgname = VariStr(msgname)
        self.var_length  = VariInt(lenght)

    def deserialize(self, stream):
        self.var_msgname.deserialize(stream)
        self.var_length.deserialize(stream)
        return self
    
    def serialize(self):
        return self.var_msgname.serialize() + self.var_length.serialize()

    def __len__(self):
        return len(self.serialize())

class VariBytes:
    def __init__(self, bytesin = b""):
        self.value    = bytesin
        self.var_int  = VariInt(len(self.value))
    
    def parse(self, value):
        self.value    = value
        self.var_int.parse(len(self.value))
        return self

    def __eq__(self, other):
        return (self.value == other.value)

    def deserialize(self, stream):
        string_length = self.var_int.deserialize(stream).value
        self.value   = stream.read(string_length)
        return self

    def serialize(self):
        return b''.join([self.var_int.serialize() , self.value])

    def __len__(self):
        return len(self.serialize())

class VariList:
    """A List field."""
    def __init__(self, value = []):
        self.value    = value
        self.var_int  = VariInt(len(self.value))
    
    def Append(self, valuein):
        self.value.append(valuein)
        self.var_int.parse(len(self.value))
        return self

    def parse(self, valuein):
        self.value    = valuein
        self.var_int.parse(len(self.value))
        return self

    def deserialize(self, stream, objclass = None):
        self.var_int.deserialize(stream)
        self.value    = []
        for i in range(self.var_int.value):
            if objclass is None:
                obj = aiptool.GetObj(VariStr().deserialize(stream).value)()
            else:
                obj = objclass()
            obj.deserialize(stream)
            self.value.append(obj)
        return self
    
    def serialize(self):
        byteslist = [obj.serialize() for obj in self.value]
        return self.var_int.serialize() + b''.join(byteslist)
    
    def __eq__(self, other):
        return (self.value == other.value)
        
    def __iter__(self):
        return iter(self.value)
    
    def __len__(self):
        return len(self.value)