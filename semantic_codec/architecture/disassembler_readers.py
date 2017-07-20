"""
Readers of disassemble files
"""
import re

from semantic_codec.architecture.darm_instruction import DARMInstruction
from semantic_codec.architecture.functions import ElfFunction


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

    def read_instructions(self):
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
        pass




class TextDisassembleReader(DisassembleReader):
    """
    Reads the instructions in text format from the https://onlinedisassembler.com/static/home/,
    for example:    .text:000107ec f0 87 bd e8
    """
    def __init__(self, filename, instruction_set=DisassembleReader.ARM_SET):
        super(TextDisassembleReader, self).__init__(filename, instruction_set)
        self.functions = None
        self.instructions = None

    def read_functions(self):
        # Function header in our assembly
        p = re.compile("^\.\w+\:[0-9a-f]+\s*\<[\$|\w+]")

        if self._instruction_set != DisassembleReader.ARM_SET:
            raise RuntimeError("Instruction encoding not supported yet")

        result = []

        k, i = "no_method", 0
        result.append(ElfFunction(k))
        for line in open(self._filename):
            line = line.rstrip('\n')
            if p.match(line):
                k = line
                if k in result:
                    i += 1
                    k = line + i
                result.append(ElfFunction(k))
            elif len(line) > 0 and line[0] == ' ':
                e = line.split(":", 1)[1].split("  ", 1)[0].split(" ", 1)
                f = result[len(result) - 1]
                f.instructions.append(DARMInstruction(e[1], position=int(e[0], 16)))

        return result

    def read(self):
        return (self.read_instructions(), self.read_functions())

    def read_instructions(self):
        if self._instruction_set != DisassembleReader.ARM_SET:
            raise RuntimeError("Instruction encoding not supported yet")

        result = []

        for line in open(self._filename):
            if line[0] == ' ':
                e = line.rstrip('\n').split(":", 1)[1].split("  ", 1)[0].split(" ", 1)
                result.append(DARMInstruction(e[1], position=int(e[0], 16)))

        return result