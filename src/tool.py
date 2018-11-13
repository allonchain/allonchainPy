from src.common.datatype import MsgHeader
from hashlib import sha3_256
from io import BytesIO

def ObjList2BytesList(objlist):
    return [a.serialize() for a in objlist]


def PackMsg(msgname , data):
    checksum = sha3_256(data).digest()[:4]
    payload  = checksum + data
    length   = len(payload)
    msgh = MsgHeader(msgname, length)
    return msgh.serialize() + payload

def UnPackMsg(rec):
    msgh    = MsgHeader()
    stream  = BytesIO(rec)
    try:
        msgh.deserialize(stream)
    except:
        return None, None
    try:
        payload = stream.read(msgh.var_length.value)
        # Check if the checksum is valid
        msgchecksum = payload[:4]
        checksum    = sha3_256(payload[4:]).digest()[:4]
        if msgchecksum != checksum:
            return (msgh, None)
    except:
        return (msgh, None)
    #.var_msgname.value
    return (msgh, payload[4:])
