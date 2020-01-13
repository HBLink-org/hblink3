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
This is a very simple call/packet router for Homebrew Repeater Protocol. It
will forward traffic from any system to all other systems configured in the
hblink.py configuration file. It does not check for call contentions or
filter TS/TGID combinations. It should really only be used as a proxy to
hide multiple Homebrew repater protocol systems behind what appears as a single
repeater, hotspot, etc.

As is, this program only works with group voice packets. It could work for all
of them by removing a few things.

IT ONLY WORKS FOR HBP SYSTEMS!!! Using it with OpenBridge or XLX wouldn't make
a lot of sense, and has the potential to do bad things.
'''

# Python modules we need
import sys
from bitarray import bitarray
from time import time
from importlib import import_module
from types import ModuleType

# Twisted is pretty important, so I keep it separate
from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import NetstringReceiver
from twisted.internet import reactor, task

# Things we import from the main hblink module
from hblink import HBSYSTEM, OPENBRIDGE, systems, hblink_handler, reportFactory, REPORT_OPCODES, config_reports, mk_aliases, acl_check
from dmr_utils3.utils import bytes_3, int_id, get_alias
from dmr_utils3 import decode, bptc, const
import config
import log
import const

# The module needs logging logging, but handlers, etc. are controlled by the parent
import logging
logger = logging.getLogger(__name__)


# Does anybody read this stuff? There's a PEP somewhere that says I should do this.
__author__     = 'Cortney T. Buffington, N0MJS'
__copyright__  = 'Copyright (c) 2016-2018 Cortney T. Buffington, N0MJS and the K0USY Group'
__credits__    = 'Colin Durbridge, G4EML, Steve Zingman, N4IRS; Mike Zingman, N4IRR; Jonathan Naylor, G4KLX; Hans Barthen, DL5DI; Torsten Shultze, DG1HT'
__license__    = 'GNU GPLv3'
__maintainer__ = 'Cort Buffington, N0MJS'
__email__      = 'n0mjs@me.com'
__status__     = 'pre-alpha'

# Module gobal varaibles


class bridgeallSYSTEM(HBSYSTEM):

    def __init__(self, _name, _config, _report):
        HBSYSTEM.__init__(self, _name, _config, _report)
        self._laststrid = ''

        # Status information for the system, TS1 & TS2
        # 1 & 2 are "timeslot"
        self.STATUS = {
            1: {
                'RX_START':     time(),
                'RX_LOSS':      0,
                'RX_SEQ':       0,
                'RX_RFS':       b'\x00',
                'TX_RFS':       b'\x00',
                'RX_STREAM_ID': b'\x00',
                'TX_STREAM_ID': b'\x00',
                'RX_TGID':      b'\x00\x00\x00',
                'TX_TGID':      b'\x00\x00\x00',
                'RX_TIME':      time(),
                'TX_TIME':      time(),
                'RX_TYPE':      const.HBPF_SLT_VTERM,
                },
            2: {
                'RX_START':     time(),
                'RX:LOSS':      0,
                'RX_SEQ':       0,
                'RX_RFS':       b'\x00',
                'TX_RFS':       b'\x00',
                'RX_STREAM_ID': b'\x00',
                'TX_STREAM_ID': b'\x00',
                'RX_TGID':      b'\x00\x00\x00',
                'TX_TGID':      b'\x00\x00\x00',
                'RX_TIME':      time(),
                'TX_TIME':      time(),
                'RX_TYPE':      const.HBPF_SLT_VTERM,
                }
            }

    def dmrd_received(self, _peer_id, _rf_src, _dst_id, _seq, _slot, _call_type, _frame_type, _dtype_vseq, _stream_id, _data):
        pkt_time = time()
        dmrpkt = _data[20:53]
        _bits = _data[15]

        if _call_type == 'group':

            # Is this is a new call stream?
            new_stream = (_stream_id != self.STATUS[_slot]['RX_STREAM_ID'])

            if new_stream:
                self.STATUS[_slot]['RX_START'] = pkt_time
                self.STATUS[_slot]['RX_LOSS'] = 0
                self.STATUS[_slot]['RX_SEQ'] = _seq
                logger.info('(%s) *CALL START* STREAM ID: %s SUB: %s (%s) PEER: %s (%s) TGID %s (%s), TS %s', \
                        self._system, int_id(_stream_id), get_alias(_rf_src, subscriber_ids), int_id(_rf_src), get_alias(_peer_id, peer_ids), int_id(_peer_id), get_alias(_dst_id, talkgroup_ids), int_id(_dst_id), _slot)
            else:
                # This could be much better, it will have errors during roll-over
                if _seq > (self.STATUS[_slot]['RX_SEQ'] + 1):
                    #print(_seq, self.STATUS[_slot]['RX_SEQ'])
                    self.STATUS[_slot]['RX_LOSS'] += _seq - (self.STATUS[_slot]['RX_SEQ'] + 1)

            # Final actions - Is this a voice terminator?
            if (_frame_type == const.HBPF_DATA_SYNC) and (_dtype_vseq == const.HBPF_SLT_VTERM) and (self.STATUS[_slot]['RX_TYPE'] != const.HBPF_SLT_VTERM):
                call_duration = pkt_time - self.STATUS[_slot]['RX_START']
                logger.info('(%s) *CALL END*   STREAM ID: %s SUB: %s (%s) PEER: %s (%s) TGID %s (%s), TS %s, Loss: %s, Duration: %s', \
                        self._system, int_id(_stream_id), get_alias(_rf_src, subscriber_ids), int_id(_rf_src), get_alias(_peer_id, peer_ids), int_id(_peer_id), get_alias(_dst_id, talkgroup_ids), int_id(_dst_id), _slot, self.STATUS[_slot]['RX_LOSS'], call_duration)


            for _target in self._CONFIG['SYSTEMS']: 
                if _target != self._system:

                    _target_status = systems[_target].STATUS
                    _target_system = self._CONFIG['SYSTEMS'][_target]

                    # BEGIN STANDARD CONTENTION HANDLING
                    #
                    # The rules for each of the 4 "ifs" below are listed here for readability. The Frame To Send is:
                    #   From a different group than last RX from this HBSystem, but it has been less than Group Hangtime
                    #   From a different group than last TX to this HBSystem, but it has been less than Group Hangtime
                    #   From the same group as the last RX from this HBSystem, but from a different subscriber, and it has been less than stream timeout
                    #   From the same group as the last TX to this HBSystem, but from a different subscriber, and it has been less than stream timeout
                    # The "continue" at the end of each means the next iteration of the for loop that tests for matching rules
                    #
                    if ((_dst_id != _target_status[_slot]['RX_TGID']) and ((pkt_time - _target_status[_slot]['RX_TIME']) < _target_system['GROUP_HANGTIME'])):
                        if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD and self.STATUS[_slot]['RX_STREAM_ID'] != _stream_id:
                            logger.info('(%s) Call not routed to TGID %s, target active or in group hangtime: HBSystem: %s, TS: %s, TGID: %s', self._system, int_id(_dst_id), _target, _slot, int_id(_target_status[_slot]['RX_TGID']))
                        continue
                    if ((_dst_id != _target_status[_slot]['TX_TGID']) and ((pkt_time - _target_status[_slot]['TX_TIME']) < _target_system['GROUP_HANGTIME'])):
                        if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD and self.STATUS[_slot]['RX_STREAM_ID'] != _stream_id:
                            logger.info('(%s) Call not routed to TGID%s, target in group hangtime: HBSystem: %s, TS: %s, TGID: %s', self._system, int_id(_dst_id), _target, _slot, int_id(_target_status[_slot]['TX_TGID']))
                        continue
                    if (_dst_id == _target_status[_slot]['RX_TGID']) and ((pkt_time - _target_status[_slot]['RX_TIME']) < const.STREAM_TO):
                        if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD and self.STATUS[_slot]['RX_STREAM_ID'] != _stream_id:
                            logger.info('(%s) Call not routed to TGID%s, matching call already active on target: HBSystem: %s, TS: %s, TGID: %s', self._system, int_id(_dst_id), _target, _slot, int_id(_target_status[_slot]['RX_TGID']))
                        continue
                    if (_dst_id == _target_status[_slot]['TX_TGID']) and (_rf_src != _target_status[_slot]['TX_RFS']) and ((pkt_time - _target_status[_slot]['TX_TIME']) < const.STREAM_TO):
                        if _frame_type == const.HBPF_DATA_SYNC and _dtype_vseq == const.HBPF_SLT_VHEAD and self.STATUS[_slot]['RX_STREAM_ID'] != _stream_id:
                            logger.info('(%s) Call not routed for subscriber %s, call route in progress on target: HBSystem: %s, TS: %s, TGID: %s, SUB: %s', self._system, int_id(_rf_src), _target, _slot, int_id(_target_status[_slot]['TX_TGID']), int_id(_target_status[_slot]['TX_RFS']))
                        continue


                    # ACL Processing
                    if self._CONFIG['GLOBAL']['USE_ACL']:
                        if not acl_check(_rf_src, self._CONFIG['GLOBAL']['SUB_ACL']):
                            if _stream_id != _target_status[_slot]['TX_STREAM_ID']:
                                logger.info('(%s) CALL DROPPED ON EGRESS WITH STREAM ID %s FROM SUBSCRIBER %s BY GLOBAL ACL', _target, int_id(_stream_id), int_id(_rf_src))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            continue
                        if _slot == 1 and not acl_check(_dst_id, self._CONFIG['GLOBAL']['TG1_ACL']):
                            if _stream_id != _target_status[_slot]['TX_STREAM_ID']:
                                logger.info('(%s) CALL DROPPED ON EGRESS WITH STREAM ID %s ON TGID %s BY GLOBAL TS1 ACL', _target, int_id(_stream_id), int_id(_dst_id))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            continue
                        if _slot == 2 and not acl_check(_dst_id, self._CONFIG['GLOBAL']['TG2_ACL']):
                            if _stream_id != _target_status[_slot]['TX_STREAM_ID']:
                                logger.info('(%s) CALL DROPPED ON EGRESS WITH STREAM ID %s ON TGID %s BY GLOBAL TS2 ACL', _target, int_id(_stream_id), int_id(_dst_id))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            continue
                    if _target_system['USE_ACL']:
                        if not acl_check(_rf_src, _target_system['SUB_ACL']):
                            if _stream_id != _target_status[_slot]['TX_STREAM_ID']:
                                logger.info('(%s) CALL DROPPED ON EGRESS WITH STREAM ID %s FROM SUBSCRIBER %s BY SYSTEM ACL', _target, int_id(_stream_id), int_id(_rf_src))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            continue
                        if _slot == 1 and not acl_check(_dst_id, _target_system['TG1_ACL']):
                            if _stream_id != _target_status[_slot]['TX_STREAM_ID']:
                                logger.info('(%s) CALL DROPPED ON EGRESS WITH STREAM ID %s ON TGID %s BY SYSTEM TS1 ACL', _target, int_id(_stream_id), int_id(_dst_id))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            continue
                        if _slot == 2 and not acl_check(_dst_id, _target_system['TG2_ACL']):
                            if _stream_id != _target_status[_slot]['TX_STREAM_ID']:
                                logger.info('(%s) CALL DROPPED ON EGRESS WITH STREAM ID %s ON TGID %s BY SYSTEM TS2 ACL', _target, int_id(_stream_id), int_id(_dst_id))
                                _target_status[_slot]['TX_STREAM_ID'] = _stream_id
                            continue

                    # Record this stuff for later
                    # Is this a new call stream?
                    if new_stream:
                         # Record the DST TGID and Stream ID
                         _target_status[_slot]['TX_START'] = pkt_time
                         _target_status[_slot]['TX_TGID'] = _dst_id
                         _target_status[_slot]['TX_RFS'] = _rf_src
                         _target_status[_slot]['TX_PEER'] = _peer_id
                         _target_status[_slot]['TX_STREAM_ID'] = _stream_id

                    _target_status[_slot]['TX_TIME'] = pkt_time

                    systems[_target].send_system(_data)
                    #logger.debug('(%s) Packet routed to system: %s', self._system, _target)

            # Mark status variables for use later
            self.STATUS[_slot]['RX_RFS']       = _rf_src
            self.STATUS[_slot]['RX_SEQ']       = _seq
            self.STATUS[_slot]['RX_TYPE']      = _dtype_vseq
            self.STATUS[_slot]['RX_TGID']      = _dst_id
            self.STATUS[_slot]['RX_TIME']      = pkt_time
            self.STATUS[_slot]['RX_STREAM_ID'] = _stream_id


#************************************************
#      MAIN PROGRAM LOOP STARTS HERE
#************************************************

if __name__ == '__main__':
    import argparse
    import sys
    import os
    import signal
    from dmr_utils3.utils import try_download, mk_id_dict

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
    logger.debug('Logging system started, anything from here on gets logged')

    # Set up the signal handler
    def sig_handler(_signal, _frame):
        logger.info('SHUTDOWN: BRIDGE_ALL IS TERMINATING WITH SIGNAL %s', str(_signal))
        hblink_handler(_signal, _frame)
        logger.info('SHUTDOWN: ALL SYSTEM HANDLERS EXECUTED - STOPPING REACTOR')
        reactor.stop()

    # Set signal handers so that we can gracefully exit if need be
    for sig in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(sig, sig_handler)

    # Create the name-number mapping dictionaries
    peer_ids, subscriber_ids, talkgroup_ids = mk_aliases(CONFIG)

    # INITIALIZE THE REPORTING LOOP
    report_server = config_reports(CONFIG, reportFactory)

    # HBlink instance creation
    logger.info('HBlink \'bridge_all.py\' -- SYSTEM STARTING...')
    for system in CONFIG['SYSTEMS']:
        if CONFIG['SYSTEMS'][system]['ENABLED']:
            if CONFIG['SYSTEMS'][system]['MODE'] == 'OPENBRIDGE':
                logger.critical('%s FATAL: Instance is mode \'OPENBRIDGE\', \n\t\t...Which would be tragic for Bridge All, since it carries multiple call\n\t\tstreams simultaneously. bridge_all.py onlyl works with MMDVM-based systems', system)
                sys.exit('bridge_all.py cannot function with systems that are not MMDVM devices. System {} is configured as an OPENBRIDGE'.format(system))
            else:
                systems[system] = bridgeallSYSTEM(system, CONFIG, report_server)
            reactor.listenUDP(CONFIG['SYSTEMS'][system]['PORT'], systems[system], interface=CONFIG['SYSTEMS'][system]['IP'])
            logger.debug('%s instance created: %s, %s', CONFIG['SYSTEMS'][system]['MODE'], system, systems[system])

    reactor.run()
