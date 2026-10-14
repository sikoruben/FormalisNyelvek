from project.problem import Problem
import argparse


class DFAProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Add the DFA-specific command-line argument.
        """
        parser.add_argument(
            '--check',
            help='check one or more words with the DFA',
            type=str
        )

    def is_chosen_problem(self, args):
        """
        Check whether the DFA problem was selected.
        """
        return args.check is not None

    def run(self, args):
        """
        Read the DFA from the input file, check the given words,
        and write the results into the output file.
        """
        input_file = args.input
        output_file = args.output

        # Read the non-empty lines of the input file.
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = [
                line.strip()
                for line in file
                if line.strip()
            ]

        # First four lines describe the DFA.
        states = set(lines[0].split())
        alphabet = set(lines[1].split())
        start_state = lines[2]
        accepting_states = set(lines[3].split())

        # Remaining lines describe the transitions:
        # current_state symbol next_state
        transitions = {}

        for line in lines[4:]:
            current_state, symbol, next_state = line.split()
            transitions[(current_state, symbol)] = next_state

        # Words given to --check are separated by commas.
        words = args.check.split(',')

        results = []

        for word in words:
            current_state = start_state
            accepted = True

            for symbol in word:
                if symbol not in alphabet:
                    accepted = False
                    break

                transition = (current_state, symbol)

                if transition not in transitions:
                    accepted = False
                    break

                current_state = transitions[transition]

            if accepted and current_state in accepting_states:
                results.append('IGEN')
            else:
                results.append('NEM')

        # Write one result per line.
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('\n'.join(results))