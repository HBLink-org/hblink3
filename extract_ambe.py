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
This module is used to extract the AMBE72, FEC encoded data needed to make DMR
frames. It prints out a list of lists, the outer list contains the word and each
of the inner lists has two elements that comprise the 3 AMBE frames sent in each
DMR packet. The frames are split into 1.5 frames and 1.5 frames, that is to say
the two 108 bit segments used in DMR bursts.

This program is intended to produce the data needed to build words (or phrases)
that can be used to populate the voice_lib.py file. It does not write the file
for you, you must copy the output and paste them into the file. Most of the
formatting, but not all, is done for you.

It will not process OpenBridge systems, and it is strongly recommended you only
use it with one system in the hblink.cfg file at a time -- otherwise things can
get really out of hand quickly.

This is a program for ADVANCED USERS ONLY. I really mean it this time, if you're
not comfortable with how DMR packets are structured and basic Python, this isn't
going to work well for you.
'''


# Python modules we need
from bitarray import bitarray

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor

# Things we import from the main hblink module
from hblink import HBSYSTEM, systems, hblink_handler
from dmr_utils3.utils import int_id
import config
import log

# The module needs logging, but handlers, etc. are controlled by the parent
import logging
logger = logging.getLogger(__name__)


# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016-2019 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Colin Durbridge, G4EML, Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'GNU GPLv3'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'

# Module gobal varaibles
# Precalculated "dmrbits" (DMRD packet byte 15) -- just (slot << 7 | this value) and you're good to go!
HEADBITS  = 0b00100001
BURSTBITS = [0b00010000,0b00000001,0b00000010,0b00000011,0b00000100,0b00000101]
TERMBITS  = 0b00100010


class HBP(HBSYSTEM):

    def __init__(self, _name, _config, _report):
        HBSYSTEM.__init__(self, _name, _config, _report)
        self.current_stream = '\x00'

    def dmrd_received(self, _peer_id, _rf_src, _dst_id, _seq, _slot, _call_type, _frame_type, _dtype_vseq, _stream_id, _data):
        
        dmr = _data[20:53]
        bits = _data[15] & ~(1<<7)
        
        dmrraw = bitarray(endian='big')
        dmrraw.frombytes(dmr)
        
        if bits == HEADBITS:
            if self.current_stream != _stream_id:
                print('START STREAM ID {} ON SLOT {} FROM SUBSCRIBER {} TO GROUP {}'.format(int_id(_stream_id), _slot, int_id(_rf_src), int_id(_dst_id)))
                print('[')
                self.current_stream = _stream_id
            
        if bits == TERMBITS:
            if self.current_stream == _stream_id:
                print('    ]')
                print('STOP STREAM ID {}'.format(int_id(_stream_id)))
                self.current_stream = '\x00'
        
        if bits == BURSTBITS[0]:
            bts = 'Burst A'
            sig = [dmrraw[:108], dmrraw[-108:]]
            print('        {},'.format(sig))
        if bits == BURSTBITS[1]:
            bts = 'Burst B'
            sig = [dmrraw[:108], dmrraw[-108:]]
            print('        {},'.format(sig))
        if bits == BURSTBITS[2]:
            bts = 'Burst C'
            sig = [dmrraw[:108], dmrraw[-108:]]
            print('        {},'.format(sig))
        if bits == BURSTBITS[3]:
            bts = 'Burst D'
            sig = [dmrraw[:108], dmrraw[-108:]]
            print('        {},'.format(sig))
        if bits == BURSTBITS[4]:
            bts = 'Burst E'
            sig = [dmrraw[:108], dmrraw[-108:]]
            print('        {},'.format(sig))
        if bits == BURSTBITS[5]:
            bts = 'Burst F'
            sig = [dmrraw[:108], dmrraw[-108:]]
            print('        {}'.format(sig))
            
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
    parser.add_argument('-c', '--config', action='store', dest='CONFIG_FILE', help='/full/path/to/config.file (usually hblink.cfg)')
    parser.add_argument('-l', '--logging', action='store', dest='LOG_LEVEL', help='Override config file logging level.')
    cli_args = parser.parse_args()

    # Ensure we have a path for the config file, if one wasn't specified, then use the default (top of file)
    if not cli_args.CONFIG_FILE:
        cli_args.CONFIG_FILE = os.path.dirname(os.path.abspath(__file__))+'/hblink.cfg'

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
        logger.info('(GLOBAL) SHUTDOWN: CONFBRIDGE IS TERMINATING WITH SIGNAL %s', str(_signal))
        hblink_handler(_signal, _frame)
        logger.info('(GLOBAL) SHUTDOWN: ALL SYSTEM HANDLERS EXECUTED - STOPPING REACTOR')
        reactor.stop()

    # Set signal handers so that we can gracefully exit if need be
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, sig_handler)

    # INITIALIZE THE REPORTING LOOP
    report_server = None

    # HBlink instance creation
    logger.info('(GLOBAL) HBlink \'bridge.py\' -- SYSTEM STARTING...')
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