import os

from semantic_codec.architecture.disassembler_readers import TextDisassembleReader, ElfioTextDisassembleReader
from semantic_codec.corruption.corruptors import JSONCorruptor, RandomCorruptor, PacketCorruptor, CAPSInstruction, sys
from semantic_codec.metadata.metadata_collector import MetadataCollector
from semantic_codec.metadata.probabilistic_rules.rules import from_instruction_list_to_dict, from_instruction_dict_to_list, \
    from_functions_to_list_and_addr
from semantic_codec.metadata.recuperator import ProbabilisticRecuperator, probabilistic_rules
from semantic_codec.solution.solution_builders import ForwardConstraintSolutionEnumerator
from semantic_codec.solution.solution_io import SolutionWriter
from semantic_codec.solution.solution_quality import SolutionQuality


def print_report(instructions_output_file, original_program, recovered_program):

    depths ={}

    errors, recovered, fail_looses, fail_tide = 0, 0, 0, 0
    orig_stdout = sys.stdout
    f = open(instructions_output_file, 'w')
    sys.stdout = f

    bad_rules = {}
    aver_instr_tie_sum = 0
    aver_instr_tie_count = 0

    for i in range(0, len(original_program)):
        print('Original Instruction: {}'.format(original_program[i]))
        instructions = recovered_program[i]

        addr = original_program[i].address

        ori_inst = None
        for inst in instructions:
            if inst.encoding == original_program[i].encoding:
                ori_inst = inst
                break

        if len(instructions) > 1:
            instructions.sort(key=lambda x: x.score(), reverse=True)
            #max_encoding = 0
            #for inst in instructions:
            #    if inst.encoding > max_encoding:
            #        max_encoding = inst.encoding
            #instructions.sort(key = lambda x: x.score() * 1000000000 + (1 - x.encoding / max_encoding), reverse=True)

            errors += 1
            ori_str = str(original_program[i])
            c1_str = str(instructions[0])
            c2_str = str(instructions[1])
            if c1_str != ori_str and instructions[0].encoding != instructions[1].encoding:
                print(" * FAIL : 1st Instruction is not original. ")
                print(" * WRONG SCORES [Recovered vs Original]:")
                # Print the comparison with the original rule
                if ori_inst:
                    for k, v in instructions[0].scores_by_rule.items():
                        try:
                            ov = ori_inst.scores_by_rule[k]
                            if v > ov:
                                print(" -> {0!s}: {1:.6f} vs. {2:.6f} ".format(k, v, ov))
                                bad_rules[k] = bad_rules[k] + 1 if k in bad_rules else 1

                        except KeyError:
                            print(" KE: {} -- ".format(k), end="")
                print()

                fail_looses += 1
            elif instructions[0].score() == instructions[1].score() and c1_str != c2_str:
                inst_count = 0
                while inst_count < len(instructions) and \
                                instructions[0].score() == instructions[inst_count].score():
                    inst_count += 1
                print(' * TIE : {} instructions with good score'.format(inst_count))
                aver_instr_tie_sum += inst_count
                aver_instr_tie_count += 1
                fail_tide += 1
            else:
                recovered += 1
                print(" * OK!")

            count_depth = True
            this_depth = 0
            for inst in instructions:
                if inst.ignore:
                    print("X", end="")
                if inst.encoding == original_program[i].encoding:
                    print("{3} ++ [{2}] {0!s} : {1:.6f}: --> ".format(inst, inst.score(), inst.encoding, hex(addr)), end="")
                    count_depth = False
                    if not this_depth in depths:
                        depths[this_depth] = 1
                    else:
                        depths[this_depth] += 1
                else:
                    print("{3} -- [{2}] {0!s} : {1:.6f}: --> ".format(inst, inst.score(), inst.encoding, hex(addr)), end="")

                    if count_depth:
                        this_depth += 1

                for k, v in inst.scores_by_rule.items():
                    print(" {0!s}: {1:.6f} -- ".format(k, v), end="")
                print("")
        print("------------")

    print("------------")

    print('BAD RULES:')
    if len(bad_rules) == 0:
        print('No rule assigned a higher score to a false winner')
    for k, v in bad_rules.items():
        print('{} : {}'.format(k, v))

    if aver_instr_tie_count > 1:
        print("------------")
        print('AVERAGE TIE COUNT: {}'.format(aver_instr_tie_sum/aver_instr_tie_count))

    print("------------")

    print("ERRORS: {} -- LOSING: {} -- TIDE: {} --RECOVERED: {} -- RATIO: {} ".format(
        errors, fail_looses, fail_tide, recovered, recovered / errors))

    print("DEPTHS: {}".format(depths))

    sys.stdout = orig_stdout


def remove_bad_candidates_at_addr(v):
    previous = len(v)
    one_count = 0
    less_than_one_count = 0
    i = 0
    while i < len(v):
        score = v[i].score()
        if score == 1:
            one_count += 1
            i += 1
        elif score == 0:
            v.pop(i)
        else:
            less_than_one_count += 1
            if one_count > 0:
                v.pop(i)
            else:
                i += 1

    if less_than_one_count > 0:
        i = 0
        while i < len(v):
            score = v[i].score()
            if score < 1 and one_count > 0:
                v.pop(i)
            else:
                i += 1

    return previous - len(v)

def run_recovery(original_program, corruptor, recuperator, passes=1):
    # Separe the instructions from the function addresses
    original_program, fns = from_functions_to_list_and_addr(original_program)
    # Clone the original program
    program = [CAPSInstruction(v.encoding, position=v.address) for v in original_program]

    # Collect the metrics on it
    collector = MetadataCollector()
    collector.collect(program)

    print("[INFO]: Metrics collected")

    # Corrupt it:
    print("[INFO]: Corrupting program")
    program = corruptor.corrupt(from_instruction_list_to_dict(program))
    print("[INFO]: Program corrupted")
    SolutionQuality(program, original_program).report()

    print_report('corrupted_program.txt',
                 original_program, from_instruction_dict_to_list(program))

    initialwriter = SolutionWriter()
    initialwriter.write_binary('initial_solution.sol', original_program, program)


    pass_count = 1
    while (True):
        stable = True
        r = recuperator(collector, program, functions=fns)
        r.passes = passes
        r.recover()
        print("[INFO]: Heuristics computed  (pass {})".format(pass_count))

        print_report('instructions{}.txt'.format(pass_count),
                     original_program, from_instruction_dict_to_list(program))

        # Determine if there is any instruction that can be removed:
        for k, v in program.items():
            # Remove 0 or less than 1 if any instruction has 1 score
            prev = len(v)
            if remove_bad_candidates_at_addr(v) > 0:
                stable = False
            #if len(v) == 0:
            #    raise RuntimeError('Should not be empty')
        SolutionQuality(program, original_program).report()
        if stable:
            break
        pass_count += 1

    pass_count += 1

    # Change to continous
    for v in program.values():
        for inst in v:
            inst.score_function = probabilistic_rules
    print_report('instructions{}.txt'.format(pass_count),
        original_program, from_instruction_dict_to_list(program))

    print('[INFO]: Constraining: ')
    b = ForwardConstraintSolutionEnumerator(program, original_program)
    b.build()
    print('[INFO]: Constrained solution size: {}'.format(b.solution_size))
    print('[INFO]: Constrained solution: {}'.format(b.solution))
    a = SolutionQuality(program, original_program)
    a.report()

    pass_count += 1
    print_report('instructions{}.txt'.format(pass_count),
        original_program, from_instruction_dict_to_list(program))

    writer = SolutionWriter()
    writer.write_binary('final_solution.sol', original_program, program)


# max_error_per_instruction, corrupted_program=None, generate_new=False, )
if __name__ == "__main__":
    use_packets = True
    use_file = False
    recovered_program = None
    corruptor = None

    # ARM_SIMPLE = os.path.join(os.path.dirname(__file__), 'tests/data/dissasembly.armasm')
    #ARM_SIMPLE = os.path.join(os.path.dirname(__file__), 'tests/data/helloworld_elfiodissasembly.txt')
    #ARM_SIMPLE = os.path.join(os.path.dirname(__file__), 'tests/data/fft.disam')
    #ARM_SIMPLE = os.path.join(os.path.dirname(__file__), 'tests/data/dijkstra_small.disam')
    #ARM_SIMPLE = os.path.join(os.path.dirname(__file__), 'tests/data/crc32.disam')
    #ARM_SIMPLE = os.path.join(os.path.dirname(__file__), 'tests/data/bitcount.disam')
    ARM_SIMPLE = os.path.join(os.path.dirname(__file__), 'tests/data/basicmath_small.disam')
    #original_program = TextDisassembleReader(ARM_SIMPLE).read_functions()
    original_program = ElfioTextDisassembleReader(ARM_SIMPLE).read_functions()

    if not use_file:
        if use_packets:
            ll = 0
            for f in original_program:
                ll += len(f.instructions)
            packet_count = ll / 32
            lost = [3]
            print('[INFO:] Program Size: {} bytes -- Loss: {} -- Packet count: {}'.format(
                ll * 4, 16 * len(lost) * 2, packet_count))
            corruptor = PacketCorruptor(packet_count, ll, packets_lost=lost)
        else:
            corruptor = RandomCorruptor(30.0, 3, True)
    else:
        corruptor = JSONCorruptor()

    corruptor.corrupted_program_path = os.path.join(os.path.dirname(__file__), 'corrupted.json')
    #recovered_program = run_recovery(original_program, corruptor, Recuperator, 2)
    run_recovery(original_program, corruptor, ProbabilisticRecuperator)
