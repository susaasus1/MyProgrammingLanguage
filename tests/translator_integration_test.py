import unittest

import isa
import translator


def start(code_file, opcode_file, correct_opcode_file, data_file):
    translator.main([code_file, opcode_file, data_file])
    res = isa.read_code(opcode_file, data_file)
    correct_res = isa.read_code(correct_opcode_file, data_file)
    assert res == correct_res


class TestTranslator(unittest.TestCase):

    def test_prob5(self):
        start("examples/prob5_fast.javajs", "opcode.txt", "examples/correct_opcode_prob5_fast.txt", "examples/data.txt")

    def test_helloworld(self):
        start("examples/helloworld.javajs", "opcode.txt", "examples/correct_opcode_helloworld.txt", "examples/data.txt")

    def test_sum(self):
        start("examples/sum.javajs", "opcode.txt", "examples/correct_opcode_sum.txt", "examples/data.txt")
