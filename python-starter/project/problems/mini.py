from project.problem import Problem
import argparse
import re


class MinimizationProblem(Problem):
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Add the automaton minimization command-line argument.
        """
        parser.add_argument(
            '--mini',
            help='minimize the given deterministic finite automaton',
            action='store_true'
        )

    def is_chosen_problem(self, args):
        """
        Check whether the minimization problem was selected.
        """
        return bool(args.mini)

    def run(self, args):
        """
        Read a deterministic finite automaton, minimize it,
        and write the result into the output file.
        """
        if not args.input:
            raise ValueError('The --input argument is required.')

        if not args.output:
            raise ValueError('The --output argument is required.')

        (
            states,
            alphabet,
            start_state,
            accepting_states,
            transitions
        ) = self.read_automaton(args.input)

        reachable_states = self.find_reachable_states(
            start_state,
            alphabet,
            transitions
        )

        # Unreachable states do not belong to the minimal automaton.
        states = states.intersection(reachable_states)
        accepting_states = accepting_states.intersection(states)

        transitions = {
            (source, symbol): target
            for (source, symbol), target in transitions.items()
            if source in states and target in states
        }

        partitions = self.minimize(
            states,
            alphabet,
            accepting_states,
            transitions
        )

        self.write_automaton(
            args.output,
            partitions,
            alphabet,
            start_state,
            accepting_states,
            transitions
        )

    def read_automaton(self, input_file):
        """
        Read and validate the automaton from the input file.
        """
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = [
                line.strip()
                for line in file
                if line.strip()
            ]

        if len(lines) < 4:
            raise ValueError(
                'The input file must contain at least four non-empty lines.'
            )

        state_list = lines[0].split()
        alphabet_list = lines[1].split()
        start_state = lines[2].strip()
        accepting_state_list = lines[3].split()

        if not state_list:
            raise ValueError('The list of states cannot be empty.')

        if not alphabet_list:
            raise ValueError('The alphabet cannot be empty.')

        if len(state_list) != len(set(state_list)):
            raise ValueError('The list of states contains duplicates.')

        if len(alphabet_list) != len(set(alphabet_list)):
            raise ValueError('The alphabet contains duplicates.')

        states = set(state_list)
        alphabet = set(alphabet_list)
        accepting_states = set(accepting_state_list)

        if start_state not in states:
            raise ValueError(
                f'Invalid start state: {start_state}'
            )

        invalid_accepting_states = accepting_states - states

        if invalid_accepting_states:
            invalid_states = ', '.join(
                sorted(invalid_accepting_states, key=self.natural_key)
            )
            raise ValueError(
                f'Invalid accepting state or states: {invalid_states}'
            )

        transitions = {}

        for line_number, line in enumerate(lines[4:], start=5):
            parts = line.split()

            if len(parts) != 3:
                raise ValueError(
                    f'Invalid transition on line {line_number}: {line}'
                )

            source, symbol, target = parts

            if source not in states:
                raise ValueError(
                    f'Invalid source state on line {line_number}: {source}'
                )

            if symbol not in alphabet:
                raise ValueError(
                    f'Invalid symbol on line {line_number}: {symbol}'
                )

            if target not in states:
                raise ValueError(
                    f'Invalid target state on line {line_number}: {target}'
                )

            transition_key = (source, symbol)

            if transition_key in transitions:
                previous_target = transitions[transition_key]

                # Repeated identical transitions are ignored.
                if previous_target == target:
                    continue

                raise ValueError(
                    'The automaton is not deterministic: '
                    f'{source} has more than one transition with {symbol}.'
                )

            transitions[transition_key] = target

        return (
            states,
            alphabet,
            start_state,
            accepting_states,
            transitions
        )

    def find_reachable_states(
        self,
        start_state,
        alphabet,
        transitions
    ):
        """
        Find all states reachable from the start state.
        """
        reachable = {start_state}
        stack = [start_state]

        while stack:
            current_state = stack.pop()

            for symbol in alphabet:
                target = transitions.get((current_state, symbol))

                if target is not None and target not in reachable:
                    reachable.add(target)
                    stack.append(target)

        return reachable

    def minimize(
        self,
        states,
        alphabet,
        accepting_states,
        transitions
    ):
        """
        Minimize the DFA using iterative partition refinement.

        A virtual sink state is temporarily used for missing transitions.
        The virtual state is not written into the output.
        """
        sink_state = object()

        needs_sink = any(
            (state, symbol) not in transitions
            for state in states
            for symbol in alphabet
        )

        working_states = set(states)

        if needs_sink:
            working_states.add(sink_state)

        final_partition = set(accepting_states)
        non_final_partition = working_states - final_partition

        partitions = []

        if final_partition:
            partitions.append(final_partition)

        if non_final_partition:
            partitions.append(non_final_partition)

        sorted_alphabet = sorted(alphabet, key=self.natural_key)

        while True:
            state_to_partition = {}

            for partition_index, partition in enumerate(partitions):
                for state in partition:
                    state_to_partition[state] = partition_index

            refined_partitions = []

            for partition in partitions:
                groups = {}

                for state in partition:
                    signature = []

                    for symbol in sorted_alphabet:
                        if state is sink_state:
                            target = sink_state
                        else:
                            target = transitions.get(
                                (state, symbol),
                                sink_state
                            )

                        signature.append(
                            state_to_partition[target]
                        )

                    signature = tuple(signature)

                    if signature not in groups:
                        groups[signature] = set()

                    groups[signature].add(state)

                refined_partitions.extend(groups.values())

            if self.partitions_are_equal(
                partitions,
                refined_partitions
            ):
                partitions = refined_partitions
                break

            partitions = refined_partitions

        result = []

        for partition in partitions:
            real_states = {
                state
                for state in partition
                if state is not sink_state
            }

            if real_states:
                result.append(real_states)

        result.sort(
            key=lambda group: self.natural_key(
                min(group, key=self.natural_key)
            )
        )

        return result

    def partitions_are_equal(self, first, second):
        """
        Check whether two partition collections contain the same groups.
        """
        first_normalized = {
            frozenset(partition)
            for partition in first
        }

        second_normalized = {
            frozenset(partition)
            for partition in second
        }

        return first_normalized == second_normalized

    def write_automaton(
        self,
        output_file,
        partitions,
        alphabet,
        start_state,
        accepting_states,
        transitions
    ):
        """
        Rename and write the minimized automaton.
        """
        state_to_group = {}
        group_representatives = []

        for group in partitions:
            representative = min(group, key=self.natural_key)
            group_representatives.append(representative)

            for state in group:
                state_to_group[state] = representative

        group_representatives.sort(key=self.natural_key)

        renamed_states = [
            self.rename_state(state)
            for state in group_representatives
        ]

        sorted_alphabet = sorted(alphabet, key=self.natural_key)

        minimized_start_state = self.rename_state(
            state_to_group[start_state]
        )

        minimized_accepting_states = set()

        for group in partitions:
            if group.intersection(accepting_states):
                representative = min(group, key=self.natural_key)
                minimized_accepting_states.add(
                    self.rename_state(representative)
                )

        sorted_accepting_states = sorted(
            minimized_accepting_states,
            key=self.natural_key
        )

        minimized_transitions = set()

        for group in partitions:
            representative = min(group, key=self.natural_key)
            renamed_source = self.rename_state(representative)

            # All states in one group are equivalent. A transition can
            # therefore be read from any group member that has one.
            sorted_group = sorted(group, key=self.natural_key)

            for symbol in sorted_alphabet:
                target = None

                for state in sorted_group:
                    possible_target = transitions.get((state, symbol))

                    if possible_target is not None:
                        target = possible_target
                        break

                if target is None:
                    continue

                target_representative = state_to_group[target]
                renamed_target = self.rename_state(
                    target_representative
                )

                minimized_transitions.add(
                    (
                        renamed_source,
                        symbol,
                        renamed_target
                    )
                )

        sorted_transitions = sorted(
            minimized_transitions,
            key=lambda transition: (
                self.natural_key(transition[0]),
                self.natural_key(transition[1]),
                self.natural_key(transition[2])
            )
        )

        output_lines = [
            ' '.join(renamed_states),
            ' '.join(sorted_alphabet),
            minimized_start_state,
            ' '.join(sorted_accepting_states)
        ]

        for source, symbol, target in sorted_transitions:
            output_lines.append(
                f'{source} {symbol} {target}'
            )

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write('\n'.join(output_lines))

    def rename_state(self, state):
        """
        Replace the first letter of the state name with 's'.

        Examples:
        q0 -> s0
        q15 -> s15
        """
        if len(state) <= 1:
            return 's'

        return 's' + state[1:]

    def natural_key(self, value):
        """
        Sort names naturally, so q2 comes before q10.
        """
        value = str(value)

        return [
            int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', value)
        ]