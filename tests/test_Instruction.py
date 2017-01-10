import os
from unittest import TestCase

from semantic_codec.architecture.disassembler_readers import TextDisassembleReader
from semantic_codec.architecture.instruction import Instruction


class TestInstruction(TestCase):

    ASM_PATH = os.path.join(os.path.dirname(__file__), 'data/dissasembly.armasm')

    def test_create(self):
        instInt = Instruction(1000)
        instStr = Instruction("1000")
        self.assertEqual(instInt.encoding, instStr.encoding)

    def test_create_hex_big_endian(self):
        instInt = Instruction(11575523)
        instStr = Instruction("00 b0 a0 e3", Instruction.HEX_STR, False)
        self.assertEqual(instInt.encoding, instStr.encoding)

    def test_create_hex_little_endian(self):
        instInt = Instruction(3818958848)
        instStr = Instruction("00 b0 a0 e3", Instruction.HEX_STR)
        self.assertEqual(instInt.encoding, instStr.encoding)

    def test_create_bad_type(self):
        try:
            instFail = Instruction(0.0)
            self.fail("Exception not raised")
        except RuntimeError:
            return

    def test_branch_to_static(self):
        """
        Test that the branch_to method returns an actual instruction from the instruction lit if the address is static
        """
        instructions = TextDisassembleReader(self.ASM_PATH).read()
        bne = instructions[22]
        jump_to = bne.branch_to(instructions)
        self.assertEqual(jump_to, instructions[15])

    def test_branch_unknown(self):
        """
        Test that the branch_to method returns an actual instruction from the instruction lit if the address is static
        """
        instructions = TextDisassembleReader(self.ASM_PATH).read()
        jump_to = instructions[20].branch_to(instructions)
        self.assertEqual(jump_to, None)
