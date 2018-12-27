'''
THIS EXAMPLE WILL NOT WORK AS IT IS - YOU MUST SPECIFY YOUR OWN VALUES!!!


'''

BRIDGES = {
    'KANSAS': [
            {'SYSTEM': 'PLYMOUTH',    'TS': 2, 'TGID': 3120,  'ACTIVE': True, 'TIMEOUT': 2, 'TO_TYPE': 'NONE',  'ON': [2,], 'OFF': [9,]},
        ],
    'BYRG': [
            {'SYSTEM': 'PLYMOUTH',    'TS': 1, 'TGID': 3100,  'ACTIVE': True, 'TIMEOUT': 2, 'TO_TYPE': 'NONE', 'ON': [3,], 'OFF': [8,]},
        ],
    'ENGLISH': [
            {'SYSTEM': 'PLYMOUTH',    'TS': 1, 'TGID': 13,    'ACTIVE': True, 'TIMEOUT': 2, 'TO_TYPE': 'NONE', 'ON': [4,], 'OFF': [7,]},
        ]
}

if __name__ == '__main__':
    from pprint import pprint
    pprint(BRIDGES)