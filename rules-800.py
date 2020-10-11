BRIDGES = {
    '1/2': [
            {'SYSTEM': '444.800',    'TS': 1, 'TGID': 2,    'ACTIVE': True, 'TIMEOUT': 5,'TO_TYPE': 'NONE',   'ON': [], 'OFF': [], 'RESET': []},
            {'SYSTEM': 'OBP',        'TS': 1, 'TGID': 2,    'ACTIVE': True, 'TIMEOUT': 5,'TO_TYPE': 'NONE',   'ON': [], 'OFF': [], 'RESET': []}
        ],
    'KANSAS': [
            {'SYSTEM': '444.800',    'TS': 2, 'TGID': 3120, 'ACTIVE': True, 'TIMEOUT': 5,'TO_TYPE': 'NONE',   'ON': [], 'OFF': [], 'RESET': []},
            {'SYSTEM': 'OBP',        'TS': 1, 'TGID': 3120, 'ACTIVE': True, 'TIMEOUT': 5,'TO_TYPE': 'NONE',   'ON': [], 'OFF': [], 'RESET': []}
        ]
}

UNIT = ["444.800", "OBP"]

if __name__ == '__main__':
    from pprint import pprint
    pprint(BRIDGES)
