import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    ADD = 'ADD'
    SUB = 'SUB'
    DIV = 'DIV'
    MOD = 'MOD'
    MUL = 'MUL'

    WR_MEM = 'WR_MEM'
    WR_NMEM = 'WR_NMEM'
    WR_BUF = 'WR_BUF'
    RD_NMEM = 'RD_NMEM'
    RD_MEM = 'RD_MEM'
    RD_BUF = 'RD_BUF'

    MOV = 'MOV'

    JMP = 'JMP'
    JZ = 'JZ'
    JNZ = 'JNZ'

    HLT = 'HLT'
    NOP = 'NOP'


class Term(namedtuple('Term', 'line var arg')):
    pass


def write_code(filename, code, strings, numbers, indirect, data):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))

    data_file = ["numbers"]
    for elem in numbers:
        data_file.append(elem)
    data_file.append("indirect")
    for elem in indirect:
        data_file.append(elem)
    data_file.append("strings")
    for elem in strings:
        data_file.append(elem)

    with open(data, "w", encoding="utf-8") as file:
        file.write(json.dumps(data_file, indent=4))


def read_code(filename, data_file):
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        instr['opcode'] = Opcode(instr['opcode'])
        if 'term' in instr:
            instr['term'] = Term(
                instr['term'][0], instr['term'][1], instr['term'][2])

    with open(data_file, encoding="utf-8") as file:
        if data_file == "":
            data_file = []
        else:
            data_file = json.loads(file.read())

    return code, data_file
