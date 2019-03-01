#!/usr/bin/env python
#
###############################################################################
#   Copyright (C) 2016-2019 Cortney T. Buffington, N0MJS <n0mjs@me.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
###############################################################################

from bitarray import bitarray
from dmr_utils3 import bptc, golay, qr
from dmr_utils3.utils import bytes_3, bytes_4
from dmr_utils3.const import EMB, SLOT_TYPE, BS_VOICE_SYNC, BS_DATA_SYNC, LC_OPT
from random import randint
from voice_lib import words

# Precalculated "dmrbits" (DMRD packet byte 15) -- just (slot << 7 | this value) and you're good to go!
HEADBITS  = 0b00100001
BURSTBITS = [0b00010000,0b00000001,0b00000010,0b00000011,0b00000100,0b00000101]
TERMBITS  = 0b00100010

# Need a bitstring of 4-bytes of zero for burst F
NULL_EMB_LC = bitarray(endian='big')
NULL_EMB_LC.frombytes(b'\x00\x00\x00\x00')

# This is where HBP encodes RSSI, it will need to be null
TAIL = b'\x00\x00'
    
# WARNING this funciton uses yeild to return a generator that will pass the next HBP packet for a phrase
# each time that it is called. Do NOT try to use it like a normal function.
def pkt_gen(_rf_src, _dst_id, _peer, _slot, _phrase):

    # Calculate all of the static components up-front
    STREAM_ID = bytes_4(randint(0x00, 0xFFFFFFFF))
    SDP = _rf_src + _dst_id + _peer
    LC = LC_OPT + _dst_id + _rf_src
    
    HEAD_LC = bptc.encode_header_lc(LC)
    HEAD_LC = [HEAD_LC[:98], HEAD_LC[-98:]]
    
    TERM_LC = bptc.encode_terminator_lc(LC)
    TERM_LC = [TERM_LC[:98], TERM_LC[-98:]]
    
    EMB_LC = bptc.encode_emblc(LC)
    
    EMBED = []
    EMBED.append(                    BS_VOICE_SYNC                     )
    EMBED.append(EMB['BURST_B'][:8] +  EMB_LC[1]  + EMB['BURST_B'][-8:])
    EMBED.append(EMB['BURST_C'][:8] +  EMB_LC[2]  + EMB['BURST_C'][-8:])
    EMBED.append(EMB['BURST_D'][:8] +  EMB_LC[3]  + EMB['BURST_D'][-8:])
    EMBED.append(EMB['BURST_E'][:8] +  EMB_LC[4]  + EMB['BURST_E'][-8:])
    EMBED.append(EMB['BURST_F'][:8] + NULL_EMB_LC + EMB['BURST_F'][-8:])
    
    
    #initialize the HBP calls stream sequence to 0
    SEQ = 0

    # Send the Call Stream
    
    # Send 3 Voice Header Frames
    for i in range(3):
        pkt = b'DMRD' + bytes([SEQ]) + SDP + bytes([_slot << 7 | HEADBITS]) + STREAM_ID + (HEAD_LC[0] + SLOT_TYPE['VOICE_LC_HEAD'][:10] + BS_DATA_SYNC + SLOT_TYPE['VOICE_LC_HEAD'][-10:] + HEAD_LC[1]).tobytes() + TAIL
        SEQ = (SEQ + 1) % 0x100
        yield pkt
        
    # Send each burst, six bursts per Superframe rotating through with the proper EMBED value per burst A-F
    for word in _phrase:
        for burst in range(0, len(word)):
            print(burst)
            pkt = b'DMRD' + bytes([SEQ]) + SDP + bytes([_slot << 7 | BURSTBITS[burst % 6]]) + STREAM_ID + (word[burst + 0][0] + EMBED[burst % 6] + word[burst + 0][1]).tobytes() + TAIL
            SEQ = (SEQ + 1) % 0x100
            yield pkt

    # Send a single Voice Terminator Frame
    pkt = b'DMRD' + bytes([SEQ]) + SDP + bytes([_slot << 7 | TERMBITS]) + STREAM_ID + (TERM_LC[0] + SLOT_TYPE['VOICE_LC_TERM'][:10] + BS_DATA_SYNC + SLOT_TYPE['VOICE_LC_TERM'][-10:] + TERM_LC[1]).tobytes() + TAIL
    SEQ = (SEQ + 1) % 0x100
    yield pkt
    
    # Return False to indicate we're done.
    return False


if __name__ == '__main__':
    from time import time
    
    speech = pkt_gen(bytes_3(3120101), bytes_3(3120), bytes_4(312000), 0, [words['all_circuits'], words['all_circuits']])
    

    while True:
        try:
            pkt = next(speech)
        except StopIteration:
            break
        print(len(pkt), pkt[4], pkt)
