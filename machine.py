from typing import Final

import logging
import sys

from isa import Opcode, read_code
from Memory import DataMemory, ProgramMemory
from translator import check_number

min_word: Final = -pow(2, 31)
max_word: Final = pow(2, 31) - 1


class DataPath:
    def __init__(self, memory_size: int, mem: DataMemory, input_buf):
        self.memory_size = memory_size
        self.mem = mem
        self.acc = 0
        self.input_buf = input_buf
        self.out_buf = []

    def write(self):
        self.mem.data[self.mem.data_address] = self.acc

    def output(self):
        self.out_buf.append(str(self.acc))

    def read(self):
        self.mem.data[self.mem.data_address] = self.acc

    def output_str(self):
        if self.acc == 0:
            return False
        else:
            symbol = chr(self.acc)
            logging.debug('output: %s << %s', repr(''.join(self.out_buf)), repr(symbol))
            self.out_buf.append(symbol)
            return True

    def latch_acc(self, sel):
        if sel == Opcode.RD_BUF.value:
            self.acc = float(''.join(self.input_buf))
        elif sel == Opcode.RD_NMEM.value:
            self.acc = ord(self.input_buf.pop(0))
        elif sel in {Opcode.RD_MEM.value, Opcode.MOV.value, Opcode.WR_BUF.value, Opcode.WR_NMEM.value}:
            self.acc = self.mem.data[self.mem.data_address]
        elif sel == Opcode.MOD.value:
            self.acc = float(self.acc) % float(self.mem.data[self.mem.data_address])
        elif sel == Opcode.SUB.value:
            self.acc = float(self.acc) - float(self.mem.data[self.mem.data_address])
        elif sel == Opcode.ADD.value:
            self.acc = float(self.acc) + float(self.mem.data[self.mem.data_address])
        elif sel == Opcode.DIV.value:
            self.acc = float(self.acc) / float(self.mem.data[self.mem.data_address])
        elif sel == Opcode.MUL.value:
            self.acc = float(self.acc) * float(self.mem.data[self.mem.data_address])

    def zero(self):
        return self.acc == 0


class ControlUnit:
    def __init__(self, data_path: DataPath, program_mem: ProgramMemory):
        self.data_path = data_path
        self.program_mem = program_mem
        self.pc = 0
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def latch_pc(self, sel_next):
        if sel_next:
            self.pc += 1
        else:
            instr = self.program_mem.get_instruction(self.pc)
            assert 'arg' in instr, "internal error"
            self.pc = instr["arg"]

    def decode_and_execute(self):
        instr = self.program_mem.get_instruction(self.pc)
        logging.debug('%s', self)
        opcode = instr["opcode"]

        if opcode is Opcode.HLT:
            raise StopIteration()

        if opcode is Opcode.JMP:
            addr = instr["arg"]
            self.pc = addr
            self.tick()

        if opcode is Opcode.JNZ:
            if self.data_path.zero():
                self.latch_pc(sel_next=True)
            else:
                self.latch_pc(sel_next=False)
            self.tick()

        if opcode is Opcode.JZ:
            if self.data_path.zero():
                self.latch_pc(sel_next=False)
            else:
                self.latch_pc(sel_next=True)
            self.tick()

        if opcode is Opcode.RD_MEM:
            addr = instr["arg"]
            self.data_path.mem.latch_data_address(addr)
            self.tick()

            self.data_path.latch_acc(opcode)
            self.latch_pc(sel_next=True)
            self.tick()

        if opcode is Opcode.WR_NMEM:
            addr = self.data_path.mem.data[instr["arg"]]
            self.data_path.mem.latch_data_address(addr)
            self.tick()
            self.data_path.latch_acc(opcode)
            self.tick()
            while self.data_path.output_str():
                addr += 1
                self.data_path.mem.latch_data_address(addr)
                self.tick()
                self.data_path.latch_acc(opcode)
                self.tick()
            self.latch_pc(sel_next=True)
            self.tick()

        if opcode is Opcode.RD_NMEM:
            addr = self.data_path.mem.data[instr["arg"]]
            self.data_path.mem.latch_data_address(addr)
            self.tick()
            self.data_path.latch_acc(opcode)
            self.tick()
            self.data_path.read()
            while len(self.data_path.input_buf) > 0:
                addr += 1
                self.data_path.mem.latch_data_address(addr)
                self.tick()
                self.data_path.latch_acc(opcode)
                self.tick()
                self.data_path.read()
            self.latch_pc(sel_next=True)
            self.tick()

        if opcode is Opcode.RD_BUF:
            addr = instr["arg"]
            self.data_path.mem.latch_data_address(addr)
            self.tick()
            self.data_path.latch_acc(opcode)
            self.tick()
            self.data_path.read()
            self.latch_pc(sel_next=True)
            self.tick()

        if opcode in {Opcode.MOD.value, Opcode.ADD.value, Opcode.DIV.value, Opcode.SUB.value, Opcode.MUL.value}:
            addr = instr["arg"]
            if check_number(instr["arg"]):
                self.data_path.mem.latch_data_address(addr)
            else:
                self.data_path.mem.data[511] = str(instr["arg"])[1:]
                self.data_path.mem.latch_data_address(511)
            self.tick()

            self.data_path.latch_acc(opcode)
            self.latch_pc(sel_next=True)
            self.tick()

        if opcode is Opcode.WR_MEM:
            addr = instr["arg"]
            self.data_path.mem.latch_data_address(addr)
            self.tick()

            self.data_path.write()
            self.latch_pc(sel_next=True)
            self.tick()

        if opcode is Opcode.MOV:
            arg = instr["arg"]
            self.data_path.mem.data[511] = arg
            self.data_path.mem.latch_data_address(511)
            self.tick()

            self.data_path.latch_acc(opcode)
            self.latch_pc(sel_next=True)
            self.tick()

        if opcode is Opcode.NOP:
            self.latch_pc(sel_next=True)
            self.tick()

        if opcode is Opcode.WR_BUF:
            arg = instr["arg"]
            self.data_path.mem.latch_data_address(arg)
            self.tick()

            self.data_path.latch_acc(opcode)
            self.tick()

            self.data_path.output()
            self.latch_pc(sel_next=True)
            self.tick()

    def __repr__(self):
        state = f"{{TICK: {self._tick}," \
                f"PC: {self.pc}, " \
                f"ACC: {self.data_path.acc} }}"

        instr = self.program_mem.get_instruction(self.pc)
        opcode = instr["opcode"]
        arg = instr.get("arg", "")
        action = f"{opcode} {arg}"
        return f"{state} {action}"


def simulation(code, input_tokens, data_memory_size, limit, data):
    instr_counter = 0
    data_memory = DataMemory(data_memory_size / 2, data)
    program_memory = ProgramMemory(data_memory_size / 2, code)
    data_path = DataPath(data_memory_size / 2, data_memory, input_tokens)
    control_unit = ControlUnit(data_path, program_memory)
    counter = 0
    try:
        while True:
            counter += 1
            assert limit > instr_counter, "too long execution, increase limit!"
            control_unit.decode_and_execute()
            instr_counter += 1

    except EOFError:
        logging.warning("Input buffer is empty")
    except StopIteration:
        pass
    logging.info("output_buffer: %s", repr(''.join(data_path.out_buf)))
    return data_path.out_buf, instr_counter, control_unit.current_tick()


def main(args):
    assert 2 <= len(args) <= 3, "Wrong arguments: machine.py <code_file> <data_file.txt> <input_file>"
    code_file = args[0]
    data_file = args[1]
    if len(args) == 2:
        input_file = ""
    else:
        input_file = args[2]
    code, data = read_code(code_file, data_file)
    if input_file != "":
        with open(input_file, encoding="utf-8") as file:
            input_text = file.read()
            input_token = []
            for char in input_text:
                input_token.append(char)
    else:
        input_token = []

    output, instr_counter, ticks = simulation(code=code, input_tokens=input_token, data_memory_size=4096, limit=5000000,
                                              data=data)

    print(''.join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
