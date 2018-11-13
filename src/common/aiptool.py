import importlib

def GetObj(aippath):
    aippathlist = aippath.split('.')
    modelpath   = ''.join(['aip.', aippathlist[0],'.', aippathlist[1]])
    try:
        aipmodule = importlib.import_module(modelpath)
        aipobj = getattr(aipmodule, aippathlist[2])
    except ImportError:
        print("need update aip", modelpath)
        return None
    return aipobj

def GetObjFromNameAndHeight(aip_head, aipdic, height = -1):
    aiplist = [aip for aip in aipdic if aip[1] == aip_head]
    aiplist.sort(key=lambda tup: tup[2])
    if height == -1:
        return GetObj(aiplist[len(aiplist)-1][0])
    for id, aip in enumerate(aiplist):
        if height < aip[2]:
            id = id -1
            break
    return GetObj(aiplist[id][0]) if id >=0 else None

def VerifyAipPathRule(aippath):
    ## "aip0.aip0_0.Law"
    try:
        namelist = aippath.split(".")
        if len(namelist) != 3:
            return False
        if namelist[0][:3] != "aip":
            return False
        if int(namelist[0][3:]) < 0: 
            return False
        name2list = namelist[1].split("_")
        if len(name2list) != 2:
            return False
        if  name2list[0] != namelist[0]:
            return False
        if int(name2list[1]) < 0:
            return False
        if namelist[2] == "":
            return False
    except:
        return False
    return True


def IsAipLegalForCurrentHeight(aippath, currentblockheight, aipdic1):
    aippathstrlist = aippath.split('.')
    aippathstr = aippath #aippathstrlist[0]+'.'+aippathstrlist[1]
    aipdic     = {aip[0]:aip[2] for aip in aipdic1}
    if aippathstr in aipdic:
        if currentblockheight >= aipdic[aippathstr]: #if height is higher than the protocol
            intversion = int(aippathstrlist[1].split('_')[1]) + 1
            nextaippathstr = aippathstrlist[0]+'.'+aippathstrlist[1].split('_')[0]+'_'+str(intversion) +'.'+ aippathstrlist[2]
            if nextaippathstr in aipdic:
                return False if currentblockheight >= aipdic[aippathstr] else True
            return True
    else:
        return False


def GetAocpayAddressFromHeight(aocpaydic, ht):
    index = -1
    for i, t in enumerate(aocpaydic):
        if ht >= t[1]:
            index = i
            continue
        else:
            break
    return "" if index < 0 else aocpaydic[index][0]

        
        
