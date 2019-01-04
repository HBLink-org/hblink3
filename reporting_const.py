###############################################################################
#   Copyright (C) 2018  Cortney T. Buffington, N0MJS <n0mjs@me.com>
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

# Opcodes for the network-based reporting protocol

REPORT_OPCODES = {
    'CONFIG_REQ': b'\x00',
    'CONFIG_SND': b'\x01',
    'BRIDGE_REQ': b'\x02',
    'BRIDGE_SND': b'\x03',
    'CONFIG_UPD': b'\x04',
    'BRIDGE_UPD': b'\x05',
    'LINK_EVENT': b'\x06',
    'BRDG_EVENT': b'\x07',
    }
