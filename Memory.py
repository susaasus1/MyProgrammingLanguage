class DataMemory:
    """
    Data Memory
    0-510 for numbers
    511 for direct operand loading
    512-1023 for indirect addressing
    1024-2047 for characters
    """

    def __init__(self, memory_size, data_section):
        assert len(data_section) < memory_size, "Length data_section more than memory_size"
        self.data_address = 0
        self.memory_size = memory_size
        self.data = []
        self.mapping_memory(data_section)

    def latch_data_address(self, address):
        assert 0 <= address <= self.memory_size, "Address out of memory"
        self.data_address = address

    def mapping_memory(self, data_section):
        data_memory = []
        num = data_section.index("numbers")
        ind = data_section.index("indirect")
        st = data_section.index("strings")

        for elem in range(num + 1, ind):
            data_memory.append(data_section[elem])
        assert len(data_memory) <= 512, "Out of memory"
        while len(data_memory) != 512:
            data_memory.append(0)

        for elem in range(ind + 1, st):
            data_memory.append(data_section[elem])
        assert len(data_memory) <= 1024, "Out of memory"
        while len(data_memory) != 1024:
            data_memory.append(0)

        for elem in range(st + 1, len(data_section)):
            data_memory.append(data_section[elem])
        assert len(data_memory) <= 2048, "Out of memory"
        while len(data_memory) != 2048:
            data_memory.append(0)

        self.data = data_memory


class ProgramMemory:
    """
    Program Memory
    0-2047
    """

    def __init__(self, memory_size, program):
        assert len(program) < memory_size, "Length program more than memory_size"
        self.data: int | dict = program
        self.program_start = 0
        self.program_len = len(program)

    def get_instruction(self, counter):
        assert counter < self.program_len, "PC out of memory"
        return self.data[counter]
