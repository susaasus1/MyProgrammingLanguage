import unittest

import machine
import translator


def start(code_file, opcode_file, data_file, input_file):
    translator.main([code_file, opcode_file, data_file])
    if input_file == "":
        return machine.main([opcode_file, data_file])
    return machine.main([opcode_file, data_file, input_file])


class TestMachine(unittest.TestCase):

    def test_prob5_fast(self):
        out = start("examples/prob5_fast.javajs", "opcode.txt", "examples/data.txt", "")
        assert float(out[0]) == 232792560

    def test_prob5_light(self):
        out = start("examples/prob5_light.javajs", "opcode.txt", "examples/data.txt", "")
        assert out == 232792560

    def test_helloworld(self):
        out = start("examples/helloworld.javajs", "opcode.txt", "examples/data.txt", "")
        assert out[0] == 'H' and out[1] == 'e' and out[2] == 'l' \
               and out[3] == 'l' and out[4] == 'o' and out[5] == ' ' \
               and out[6] == 'w' and out[7] == 'o' and out[8] == 'r' \
               and out[9] == 'l' and out[10] == 'd' and out[11] == '!'

    def test_cat(self):
        out = start("examples/cat.javajs", "opcode.txt", "examples/data.txt", "examples/input.txt")
        assert out[0] == 'L' and out[1] == 'A' and out[2] == 'B' \
               and out[3] == '3' and out[4] == ' ' and out[5] == 'P' \
               and out[6] == 'O' and out[7] == ' ' and out[8] == 'A' \
               and out[9] == 'K'

    def test_sum(self):
        out = start("examples/sum.javajs", "opcode.txt", "examples/data.txt", "")
        assert out == 210


