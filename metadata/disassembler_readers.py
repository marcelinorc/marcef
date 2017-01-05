"""
Readers of disassemble files
"""
from metadata.darm_instruction import DARMInstruction


class DisassembleReader (object):
    """
    Abstract class of all disassemble file readers
    """

    ARM_SET = 0
    THUMB_SET = 1
    BOTH = 2

    def __init__(self, filename, instruction_set=ARM_SET):
        self._filename = filename
        self._instruction_set = instruction_set

    def read(self):
        """
        Read a disassemble file
        :return: A list of instructions sorted by their memory position
        """
        pass

    @staticmethod
    def _disassemble(encodings, instruction_set =ARM_SET):
        """
        Disassemble a list of instructions
        """


class TextDisassembleReader(DisassembleReader):
    """
    Reads the instructions in text format from the https://onlinedisassembler.com/static/home/,
    for example:    .text:000107ec f0 87 bd e8
    """

    def read(self):
        if self._instruction_set != DisassembleReader.ARM_SET:
            raise RuntimeError("Instruction encoding not supported yet")

        result = []

        for line in open(self._filename):
            e = line.rstrip('\n').split(".text:", 1)[1].split("  ", 1)[0].split(" ", 1)
            result.append(DARMInstruction(e[1], position=int(e[0], 16)))

        return result