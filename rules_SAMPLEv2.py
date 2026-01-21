# Config Automation Foolery
# Simple struct is a list of TGs and a List of System names (those named in the cfg for this instance)
# These lists should be passed into BuildBridges as BuildBridges(<timeslot>,tg_list,system_list)
#
# The BRIDGES dict will have to be set and then .updated for each subsequent set of TGs and TSs
#
# Overrides for each key/value pair in the dict structure exist for the system and are exactly as named in the structure:
# SYSTEM,TS,TGID,ACTIVE,TIMEOUT,TO_TYPE,ON,OFF,RESET
# These overrides currently must exist in sets of two or more.  So to override a standard system and set it to not active
# the system value within the list would be set, as an example, to: 'SYSTEM:OBP-3103,ACTIVE:False'
# Structurally that is: '<dict key>:value,<dict key>:value,<dict key>:value' and so on
#
# Examples below

# Define some pretty basic stuff that we will setup for TS1 - but also override for any OPENSPOT (half duplex) connections 
# forcing that traffic to TS:2 and also setting it up for PTT
TS1_TGS = [3100, 3108,31080,31082,31083,31084,31085,31086]
TS1_SYSTEMS = ['OBP-3103', 'IPSC_TS1', 'MMDVM', 'SYSTEM:OPENSPOT,TS:2,TO_TYPE:ON']

# Next example, some more basic stuff that we will send over TS:2
# NOTE though that each example I'm sending traffic over TS:1 for the OpenBridge connection - why? because OBP only uses TS1
TS2_TGS = [313,314,315]
TS2_SYSTEMS = ['SYSTEM:OBP-3103,TS:1','OPENSPOT','MMDVM']

# All kinds of craziness here that I'm too tired to explain, the idea is just to give another example of additional overrides
CUSTOM_TG = [3135]
CUSTOM_SYSTEMS = ['SYSTEM:OBP-3103,TS:1','SYSTEM:OPENSPOT,TIMEOUT:30,TO_TYPE:ON','SYSTEM:MMDVM,TS:1,TGID:12345,TO_TYPE:ON']

def BuildBridges(ts,tgids,systems):
    BRIDGE = {}
    for tgid in tgids:
        export_dict = []
        keyArg = {}
        for system in systems:
            # No keyvalue pairs just build the dict with some defaults
            keyArg["SYSTEM"] = system
            keyArg["TS"] = ts
            keyArg["TGID"] = tgid
            keyArg["ON"] = []
            keyArg["RESET"] = []
            keyArg["TIMEOUT"] = 15
            keyArg["TO_TYPE"] = 'NONE'
            keyArg["ACTIVE"] = True

            usystem  = system.split(",")
            # If we found a , we assume there will be keyvalue pairs and build our dict
            if len(usystem) > 1:
                keyArg.update(args.split(':') for args in usystem)
                if keyArg['TO_TYPE'] == 'ON': # Handle ON To_Type.. no, I don't care about off for now
                    keyArg["ON"].append(keyArg["TGID"])
                    keyArg["RESET"].append(keyArg["TGID"])

            export_dict.append({'SYSTEM': keyArg["SYSTEM"], 'TS': int(keyArg["TS"]), 'TGID': int(keyArg["TGID"]), 'ACTIVE': keyArg["ACTIVE"], 'TIMEOUT': int(keyArg["TIMEOUT"]), 'TO_TYPE': keyArg["TO_TYPE"], 'ON': keyArg["ON"], 'OFF': [], 'RESET': keyArg["RESET"]})

        BRIDGE.update({str(tgid):export_dict})
    return BRIDGE

# Here we do the actual building (this is where you input the lists into the sub)
BRIDGES = BuildBridges(1,TS1_TGS,TS1_SYSTEMS)
BRIDGES.update(BuildBridges(2,TS2_TGS,TS2_SYSTEMS))
BRIDGES.update(BuildBridges(2,CUSTOM_TG,CUSTOM_SYSTEMS))


if __name__ == '__main__':
    from pprint import pprint
    pprint(BRIDGES)