from project.problem import Problem
import argparse
from collections import deque


class DeterminizationProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Add the determinization command-line argument.
        """
        parser.add_argument(
            '--det',
            help='determinize the given finite automaton',
            action='store_true'
        )

    def is_chosen_problem(self, args):
        """
        Check whether the determinization problem was selected.
        """
        return bool(args.det)

    def run(self, args):
        """
        Read a nondeterministic finite automaton from a file,
        determinize it, and write the resulting DFA into a file.
        """
        input_file = args.input
        output_file = args.output

        if input_file is None:
            raise ValueError('The --input argument is required.')

        if output_file is None:
            raise ValueError('The --output argument is required.')

        states, alphabet, start_state, accepting_states, transitions = \
            self.read_automaton(input_file)

        deterministic_states, deterministic_transitions = self.determinize(
            alphabet,
            start_state,
            transitions
        )

        deterministic_accepting_states = self.find_accepting_states(
            deterministic_states,
            accepting_states
        )

        self.write_automaton(
            output_file,
            alphabet,
            deterministic_states,
            deterministic_accepting_states,
            deterministic_transitions
        )

    def read_automaton(self, input_file):
        """
        Read and validate the input automaton.
        """
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.read().splitlines()

        if len(lines) < 4:
            raise ValueError(
                'The input file must contain at least four lines.'
            )

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2].strip()
        accepting_states = set(lines[3].split())

        state_set = set(states)
        alphabet_set = set(alphabet)

        if not states:
            raise ValueError('The automaton must contain at least one state.')

        if not alphabet:
            raise ValueError('The alphabet must not be empty.')

        if len(states) != len(state_set):
            raise ValueError('The state list contains duplicate states.')

        if len(alphabet) != len(alphabet_set):
            raise ValueError('The alphabet contains duplicate symbols.')

        if start_state not in state_set:
            raise ValueError(
                f'Invalid start state: {start_state}'
            )

        invalid_accepting_states = accepting_states - state_set

        if invalid_accepting_states:
            invalid_states = ', '.join(sorted(invalid_accepting_states))

            raise ValueError(
                f'Invalid accepting state or states: {invalid_states}'
            )

        transitions = {}

        for line_number, line in enumerate(lines[4:], start=5):
            line = line.strip()

            if not line:
                continue

            parts = line.split()

            if len(parts) != 3:
                raise ValueError(
                    f'Invalid transition at line {line_number}: {line}'
                )

            source_state, symbol, destination_state = parts

            if source_state not in state_set:
                raise ValueError(
                    f'Invalid source state at line {line_number}: '
                    f'{source_state}'
                )

            if symbol not in alphabet_set:
                raise ValueError(
                    f'Invalid symbol at line {line_number}: {symbol}'
                )

            if destination_state not in state_set:
                raise ValueError(
                    f'Invalid destination state at line {line_number}: '
                    f'{destination_state}'
                )

            transition_key = (source_state, symbol)

            if transition_key not in transitions:
                transitions[transition_key] = set()

            transitions[transition_key].add(destination_state)

        return (
            states,
            sorted(alphabet),
            start_state,
            accepting_states,
            transitions
        )

    def determinize(self, alphabet, start_state, transitions):
        """
        Determinize the automaton using subset construction.
        """
        start_subset = frozenset({start_state})

        subset_names = {
            start_subset: 's0'
        }

        deterministic_states = [start_subset]
        deterministic_transitions = []

        unprocessed_states = deque([start_subset])

        while unprocessed_states:
            current_subset = unprocessed_states.popleft()
            current_name = subset_names[current_subset]

            for symbol in alphabet:
                destination_subset = set()

                for state in current_subset:
                    destinations = transitions.get(
                        (state, symbol),
                        set()
                    )

                    destination_subset.update(destinations)

                # Do not create an edge when there is no transition.
                if not destination_subset:
                    continue

                destination_subset = frozenset(destination_subset)

                if destination_subset not in subset_names:
                    new_name = f's{len(deterministic_states)}'

                    subset_names[destination_subset] = new_name
                    deterministic_states.append(destination_subset)
                    unprocessed_states.append(destination_subset)

                destination_name = subset_names[destination_subset]

                deterministic_transitions.append(
                    (current_name, symbol, destination_name)
                )

        return deterministic_states, deterministic_transitions

    def find_accepting_states(
        self,
        deterministic_states,
        original_accepting_states
    ):
        """
        A deterministic state is accepting if its subset contains
        at least one accepting state of the original automaton.
        """
        deterministic_accepting_states = []

        for index, state_subset in enumerate(deterministic_states):
            if state_subset.intersection(original_accepting_states):
                deterministic_accepting_states.append(f's{index}')

        return deterministic_accepting_states

    def write_automaton(
        self,
        output_file,
        alphabet,
        deterministic_states,
        deterministic_accepting_states,
        deterministic_transitions
    ):
        """
        Write the deterministic automaton in the required format.
        """
        state_names = [
            f's{index}'
            for index in range(len(deterministic_states))
        ]

        output_lines = [
            ' '.join(state_names),
            ' '.join(alphabet),
            's0',
            ' '.join(deterministic_accepting_states)
        ]

        for source_state, symbol, destination_state \
                in deterministic_transitions:
            output_lines.append(
                f'{source_state} {symbol} {destination_state}'
            )

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('\n'.join(output_lines))