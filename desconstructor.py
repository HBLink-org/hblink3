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

'''
This tool listens to network traffic and breaks apart HBP and DMR packets.

It is a development and debugging tool and has no purpose in actual production
DMR networking systems.
'''

# Python modules we need
from binascii import b2a_hex as bhex
from bitarray import bitarray

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor

# Things we import from the main hblink module
from hblink import HBSYSTEM, systems, hblink_handler
from dmr_utils3.utils import bytes_3, bytes_4, int_id
from dmr_utils3 import bptc
import config
import log
from const import *


# REMOVE LATER from datetime import datetime
# The module needs logging, but handlers, etc. are controlled by the parent
import logging
logger = logging.getLogger(__name__)


# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016-2019 Cortney T. Buffington, N0MJS and the K0USY Group'
__license__    = 'GNU GPLv3'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'


DUMP_HBP = False
DUMP_DMR = True

# Module gobal varaibles

class HBP(HBSYSTEM):

    def __init__(self, _name, _config, _report):
        HBSYSTEM.__init__(self, _name, _config, _report)
        self.last_stream = b'\x00\x00\x00\x00'
        self.lcfrags = 0
        self.lostcount = 0


    def dmrd_received(self, _peer_id, _rf_src, _dst_id, _seq, _slot, _call_type, _frame_type, _dtype_vseq, _stream_id, _data):
        
        pktype = 'UNIDENTIFIED'
        
        if (_frame_type == HBPF_DATA_SYNC) and (_dtype_vseq == HBPF_SLT_VTERM):
            pktype = 'VTERM       '
            
        if (_frame_type == HBPF_DATA_SYNC) and (_dtype_vseq == HBPF_SLT_VHEAD):
            pktype = 'VHEAD       '
        
        if (_frame_type == HBPF_VOICE_SYNC):
            pktype = 'VOICE SYNC ' + str(_dtype_vseq + 1)
        
        if (_frame_type == HBPF_VOICE):
            pktype = 'VOICE      ' + str(_dtype_vseq + 1)
        
        if DUMP_HBP:
            print('STREAM: {} SEQ: {} PEER: {} SRC: {} DST: {} SLOT: {} CALL: {} FRAME: {} DTYPE: {}'.format(
                int_id(_stream_id), int_id(_seq), int_id(_peer_id), int_id(_rf_src), int_id(_dst_id), _slot, pktype, _frame_type, _dtype_vseq
            ))
        
        if DUMP_DMR:
            payload = _data[20:53]
            bitload = bitarray(endian='big')
            bitload.frombytes(payload)
            if pktype == ('VHEAD       '):
                LC = bptc.decode_full_lc(bitload[:98] + bitload[-98:]).tobytes()
                OPT = bhex(LC[0:3])
                DST = int_id(LC[3:6])
                SRC = int_id(LC[6:9])
            
                ST = bin(int.from_bytes((bitload[98:109] + bitload[-108:-99])[:8].tobytes(), 'big'))
                SC = bhex(bitload[108:-108].tobytes())
            
                print('VOICE HEADER: LC:(OPTIONS: {} DEST: {} SOURCE: {}) -- SLOT TYPE: {} -- SYNC: {}'.format(OPT, DST, SRC, ST, SC))
            
            elif pktype == ('VTERM       '):
                LC = bptc.decode_full_lc(bitload[:98] + bitload[-98:]).tobytes()
                OPT = bhex(LC[0:3])
                DST = int_id(LC[3:6])
                SRC = int_id(LC[6:9])
            
                ST = bin(int.from_bytes((bitload[98:109] + bitload[-108:-99])[:8].tobytes(), 'big'))
                SC = bhex(bitload[108:-108].tobytes())
            
                print('VOICE TERMINATOR: LC:(OPTIONS: {} DEST: {} SOURCE: {}) -- SLOT TYPE: {} -- SYNC: {}'.format(OPT, DST, SRC, ST, SC))
            
            elif pktype == ('VOICE SYNC 1'):
                self.lcfrags=0
                print('Voice Burst A')
                BVC = bitload[0:108] + bitload[-108:]
                BSC = bitload[108:-108]
                self.lcfrags = 0
            
            elif 'VOICE   ' in pktype:
                print('Voice Burst B-F')
                BVC = bitload[0:108] + bitload[-108:]
                BEB = bitload[108:116] + bitload[-116:-108]
                BES = bitload[116:-116]
                print(len(BVC), len(BEB), len(BES))
        

#************************************************
#      MAIN PROGRAM LOOP STARTS HERE
#************************************************

if __name__ == '__main__':
    import argparse
    import sys
    import os
    import signal

    # Change the current directory to the location of the application
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

    # CLI argument parser - handles picking up the config file from the command line, and sending a "help" message
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', action='store', dest='CONFIG_FILE', help='/full/path/to/config.file (usually deconstructor.cfg)')
    parser.add_argument('-l', '--logging', action='store', dest='LOG_LEVEL', help='Override config file logging level.')
    cli_args = parser.parse_args()

    # Ensure we have a path for the config file, if one wasn't specified, then use the default (top of file)
    if not cli_args.CONFIG_FILE:
        cli_args.CONFIG_FILE = os.path.dirname(os.path.abspath(__file__))+'/deconstructor.cfg'

    # Call the external routine to build the configuration dictionary
    CONFIG = config.build_config(cli_args.CONFIG_FILE)

    # Start the system logger
    if cli_args.LOG_LEVEL:
        CONFIG['LOGGER']['LOG_LEVEL'] = cli_args.LOG_LEVEL
    logger = log.config_logging(CONFIG['LOGGER'])
    logger.info('\n\nCopyright (c) 2013, 2014, 2015, 2016, 2018, 2019\n\tThe Regents of the K0USY Group. All rights reserved.\n')
    logger.debug('(GLOBAL) Logging system started, anything from here on gets logged')

    # Set up the signal handler
    def sig_handler(_signal, _frame):
        logger.info('(GLOBAL) SHUTDOWN: DECONSTRUCTOR IS TERMINATING WITH SIGNAL %s', str(_signal))
        hblink_handler(_signal, _frame)
        logger.info('(GLOBAL) SHUTDOWN: ALL SYSTEM HANDLERS EXECUTED - STOPPING REACTOR')
        reactor.stop()

    # Set signal handers so that we can gracefully exit if need be
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, sig_handler)

    # INITIALIZE THE REPORTING LOOP
    report_server = None

    # HBlink instance creation
    logger.info('(GLOBAL) HBlink \'hbp_deconstructor.py\' -- SYSTEM STARTING...')
    for system in CONFIG['SYSTEMS']:
        if CONFIG['SYSTEMS'][system]['ENABLED']:
            if CONFIG['SYSTEMS'][system]['MODE'] == 'MASTER' or CONFIG['SYSTEMS'][system]['MODE'] == 'PEER':
                systems[system] = HBP(system, CONFIG, report_server)
            reactor.listenUDP(CONFIG['SYSTEMS'][system]['PORT'], systems[system], interface=CONFIG['SYSTEMS'][system]['IP'])
            logger.debug('(GLOBAL) %s instance created: %s, %s', CONFIG['SYSTEMS'][system]['MODE'], system, systems[system])

    def loopingErrHandle(failure):
        logger.error('(GLOBAL) STOPPING REACTOR TO AVOID MEMORY LEAK: Unhandled error in timed loop.\n %s', failure)
        reactor.stop()

    reactor.run()