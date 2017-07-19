
class DefaultProbabilisticModel(object):
    """
    Class containing the values assigned to the probabilities model variables
    """
    def __init__(self):
        # Observed probability of a non-all to exists after a branch and all near conditional were equal
        self.branch_after_cpsr_and_near_cond_are_equals = 0.85

        # Observed probability of a non-all to exists after a branch and the previous conditional was equal
        self.branch_after_cpsr_and_prev_cond_are_equals = 0.65

        # Observed probability of a non-all to exists after a branch and the previous conditional was equal
        self.branch_after_cpsr_and_after_cond_are_equals = 0.76

        # Indicates the probability of a branching instruction happening after a flag register write
        self.branch_after_cpsr = 0.6

        # Indicates the probability that a instructions have the same conditional of its predecesor and sucesor
        self.both_conditionals_are_equals = 0.7

        # Indicates the probability that a instructions have the same conditional of its predecesor
        self.prev_conditionals_are_equals = 0.65

        # Indicates the chance of a jump being invalid if it lies inside the program
        self.jump_is_valid = 0.1
