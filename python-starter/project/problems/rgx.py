from project.problem import Problem
import argparse
import re


class RegexProblem(Problem):
    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Add the regex task command-line argument.
        """
        parser.add_argument(
            '--rgx',
            help='run the selected regex task',
            type=int,
            choices=[1, 2, 3, 4, 5]
        )

    def is_chosen_problem(self, args):
        """
        Check whether a regex task was selected.
        """
        return args.rgx is not None

    def run(self, args):
        """
        Read the log file, execute the selected regex task,
        and write the result into the output file.
        """
        if not args.input:
            raise ValueError('The --input argument is required.')

        if not args.output:
            raise ValueError('The --output argument is required.')

        with open(args.input, 'r', encoding='utf-8') as file:
            log_data = file.read()

        if args.rgx == 1:
            result = self.solve_task_1(log_data)
        elif args.rgx == 2:
            result = self.solve_task_2(log_data)
        elif args.rgx == 3:
            result = self.solve_task_3(log_data)
        elif args.rgx == 4:
            result = self.solve_task_4(log_data)
        elif args.rgx == 5:
            result = self.solve_task_5(log_data)
        else:
            raise ValueError('Invalid regex task number.')

        with open(args.output, 'w', encoding='utf-8') as file:
            file.write(result)

    def solve_task_1(self, log_data):
        """
        Count the ten requested types of log lines.
        Each count is written on a separate line.
        """
        patterns = [
            # 1. All lines created on October 15.
            r'^10-15[ \t].*$',

            # 2. All lines created on October 15 at 10:18:51.
            r'^10-15[ \t]+10:18:51(?:\.\d+)?[ \t].*$',

            # 3. All lines created at second 51, independently of the minute.
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:51(?:\.\d+)?[ \t].*$',

            # 4. All lines whose tag is lowmemorykiller.
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'\d+[ \t]+\d+[ \t]+[IDVEFAW][ \t]+'
            r'lowmemorykiller[ \t]*:.*$',

            # 5. Lines created at 10:18:51 with process ID 221.
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'10:18:51(?:\.\d+)?[ \t]+'
            r'221[ \t]+\d+[ \t]+[IDVEFAW][ \t]+.*$',

            # 6. All error lines.
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'\d+[ \t]+\d+[ \t]+E[ \t]+.*$',

            # 7. All warnings sent by PackageManager.
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'\d+[ \t]+\d+[ \t]+W[ \t]+'
            r'PackageManager[ \t]*:.*$',

            # 8. All ExoPlayer debug information.
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'\d+[ \t]+\d+[ \t]+D[ \t]+'
            r'ExoPlayer[^:]*[ \t]*:.*$',

            # 9. Error and warning lines containing a Java position.
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'\d+[ \t]+\d+[ \t]+[EW][ \t]+'
            r'.*\.java:\d+.*$',

            # 10. Lines containing the word Thread in the message.
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'\d+[ \t]+\d+[ \t]+[IDVEFAW][ \t]+'
            r'[^:\r\n]+:[^\r\n]*\bThread\b[^\r\n]*$'
        ]

        results = []

        for pattern in patterns:
            matches = re.findall(
                pattern,
                log_data,
                flags=re.MULTILINE
            )
            results.append(str(len(matches)))

        return '\n'.join(results)

    def solve_task_2(self, log_data):
        """
        Extract Java source file names from error lines.
        Repeated file names are preserved.
        """
        pattern = (
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'\d+[ \t]+\d+[ \t]+E[ \t]+'
            r'[^\r\n]*?'
            r'(?:[A-Za-z_$][A-Za-z0-9_$]*\.)*'
            r'([A-Za-z_$][A-Za-z0-9_$]*\.java)'
            r':\d+'
        )

        file_names = re.findall(
            pattern,
            log_data,
            flags=re.MULTILINE
        )

        return '\n'.join(file_names)

    def solve_task_3(self, log_data):
        """
        Extract every different process ID while preserving
        the order of first occurrence.
        """
        pattern = (
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'(\d+)[ \t]+\d+[ \t]+[IDVEFAW][ \t]+'
        )

        process_ids = re.findall(
            pattern,
            log_data,
            flags=re.MULTILINE
        )

        unique_process_ids = []
        seen_process_ids = set()

        for process_id in process_ids:
            if process_id not in seen_process_ids:
                seen_process_ids.add(process_id)
                unique_process_ids.append(process_id)

        return '\n'.join(unique_process_ids)

    def solve_task_4(self, log_data):
        """
        Find the process ID that has the most error lines.
        """
        pattern = (
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'(\d+)[ \t]+\d+[ \t]+E[ \t]+'
        )

        error_process_ids = re.findall(
            pattern,
            log_data,
            flags=re.MULTILINE
        )

        if not error_process_ids:
            return 'PID=0 (0 errors)'

        error_counts = {}

        for process_id in error_process_ids:
            if process_id not in error_counts:
                error_counts[process_id] = 0

            error_counts[process_id] += 1

        most_errors_pid = None
        most_errors_count = -1

        for process_id, error_count in error_counts.items():
            if error_count > most_errors_count:
                most_errors_pid = process_id
                most_errors_count = error_count

        return f'PID={most_errors_pid} ({most_errors_count} errors)'

    def solve_task_5(self, log_data):
        """
        Count errors that occurred on the main thread.
        The process ID and thread ID must be identical.
        """
        pattern = (
            r'^[0-9]{2}-[0-9]{2}[ \t]+'
            r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.\d+)?[ \t]+'
            r'(\d+)[ \t]+\1[ \t]+E[ \t]+'
        )

        main_thread_errors = re.findall(
            pattern,
            log_data,
            flags=re.MULTILINE
        )

        return str(len(main_thread_errors))