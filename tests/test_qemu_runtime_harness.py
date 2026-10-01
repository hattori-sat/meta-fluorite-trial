import ast
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import threading
import time
import unittest


HARNESS = Path(__file__).resolve().parents[1] / 'scripts/qemu-runtime-harness.sh'
GATE_VALIDATOR = Path(__file__).resolve().parents[1] / 'scripts/flr0350_launch_gate.py'
SERIAL_PROMPT = b'qa-console# '
GATE_OBSERVATION = (
    b'FLR0350_GATE_OBSERVATION version=1 pid=706 start=3089 '
    b'start_after=3089 recorded_start=3089 uid=1001 comm=sh state=S '
    b'tracer=0 syscall=read nr=0 arg1=0x0 target_type=fifo target_dev=40 '
    b'target_ino=23 gate_type=fifo gate_dev=40 gate_ino=23 gate_uid=1001 '
    b'gate_mode=600'
)


class RuntimeHarnessTests(unittest.TestCase):
    def run_serial_exec_fixture(self, directory, setup_reply):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.settimeout(5)
            listener.bind(('localhost', 0))
            listener.listen(1)
        except OSError:
            listener.close()
            raise
        port = listener.getsockname()[1]
        state = {'requested_command': None, 'errors': []}

        def receive_line(connection):
            data = bytearray()
            while not data.endswith(b'\n'):
                chunk = connection.recv(4096)
                if not chunk:
                    return bytes(data)
                data.extend(chunk)
                if len(data) > 16384:
                    raise RuntimeError('serial command exceeded test bound')
            return bytes(data)

        def serve_console():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(5)
                    if receive_line(connection) != b'\n':
                        raise RuntimeError('serial helper did not request a prompt')
                    connection.sendall(SERIAL_PROMPT)
                    setup_command = receive_line(connection)
                    if setup_command != b'stty -echo\n':
                        raise RuntimeError('unexpected echo-off command')
                    connection.sendall(setup_reply)
                    requested_command = receive_line(connection)
                    state['requested_command'] = requested_command
                    if requested_command:
                        connection.sendall(
                            GATE_OBSERVATION
                            + b'\r\nrc=0\r\n__FLR_SERIAL_COMMAND_DONE_7B31__\n'
                            + SERIAL_PROMPT
                        )
            except (OSError, RuntimeError) as exc:
                state['errors'].append(str(exc))
            finally:
                listener.close()

        command_file = directory / 'observer.cmd'
        output_file = directory / 'observer.out'
        launch_file = directory / 'launch.out'
        command_file.write_text('true\n', encoding='utf-8')
        launch_file.write_text(
            'FLR0350_LAUNCH_WRAPPER=READY pid=706 start=3089 '
            'uid=1001 comm=sh\n',
            encoding='utf-8',
        )
        thread = threading.Thread(target=serve_console, daemon=True)
        thread.start()
        try:
            result = subprocess.run(
                [
                    'bash', str(HARNESS), 'serial-exec',
                    '--serial-port', str(port), '--user', 'root',
                    '--prompt', SERIAL_PROMPT.decode(),
                    '--command-file', str(command_file),
                    '--output', str(output_file),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        finally:
            thread.join(timeout=6)
            listener.close()
        self.assertFalse(thread.is_alive(), 'fake serial console did not finish')
        self.assertEqual(state['errors'], [])
        output = output_file.read_bytes() if output_file.exists() else b''
        validator = subprocess.run(
            [
                'python3', str(GATE_VALIDATOR), '--validate',
                str(launch_file), str(output_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        ) if output_file.exists() else None
        return result, output, validator, state

    def test_embedded_python_compiles(self):
        blocks = re.findall(r"<<'PY'\n(.*?)\nPY", HARNESS.read_text(), re.S)
        self.assertGreaterEqual(len(blocks), 3)
        for index, block in enumerate(blocks):
            with self.subTest(block=index):
                ast.parse(block)

    def test_process_detector_handles_linux_truncation_and_interpreter(self):
        text = HARNESS.read_text()
        function = text.split('target_processes() {', 1)[1].split('\n}\n', 1)[0]
        mock = '''
ps() {
  case "$*" in
    *comm*) printf '%s\n' '501 qemu-system-x86' '502 python3' ;;
    *) printf '%s\n' \
      '501 1 Sl /sdk/bin/qemu-system-x86_64 -snapshot' \
      '502 1 S python3 /sdk/scripts/runqemu snapshot' \
      '503 1 S bash -c echo qemu-system-x86_64' \
      '504 1 Z [qemu-system-x86] <defunct>' ;;
  esac
}
'''
        result = subprocess.run(['bash', '-c', mock + '\n' + function],
                                text=True, capture_output=True, check=True)
        self.assertEqual([line.split()[0] for line in result.stdout.splitlines()],
                         ['501', '502'])

    def test_guest_readiness_and_qmp_teardown_are_bounded(self):
        text = HARNESS.read_text()
        self.assertIn('guest-ready)', text)
        self.assertIn('serial-exec)', text)
        self.assertIn('output_file', text)
        self.assertIn('__FLR_SERIAL_COMMAND_DONE_7B31__', text)
        self.assertIn('timeout_seconds', text)
        self.assertIn('sock.sendall(b"\\n")', text)
        self.assertIn("sock.sendall(b'{\"execute\":\"qmp_capabilities\"}\\r\\n')", text)
        self.assertIn("sock.sendall(b'{\"execute\":\"quit\"}\\r\\n')", text)

    def test_serial_exec_capture_passes_strict_gate_without_setup_preamble(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, output, validator, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'stty -echo\r\n' + SERIAL_PROMPT,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(state['requested_command'])
        self.assertIsNotNone(validator)
        self.assertEqual(
            validator.returncode,
            0,
            validator.stdout + validator.stderr,
        )
        self.assertNotIn(b'stty -echo', output)
        self.assertEqual(output.count(b'FLR0350_GATE_OBSERVATION'), 1)

    def test_serial_exec_fails_closed_on_unexpected_echo_off_response(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, _, _, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'unexpected serial chatter\r\n' + SERIAL_PROMPT,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('reason=echo-off-response-unexpected', result.stderr)
        self.assertFalse(state['requested_command'])

    def test_serial_exec_timeout_preserves_incremental_runtime_transcript(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.settimeout(5)
            listener.bind(('localhost', 0))
            listener.listen(1)
        except OSError:
            listener.close()
            raise
        port = listener.getsockname()[1]
        state = {'requested_command': None, 'errors': []}

        def receive_line(connection):
            data = bytearray()
            while not data.endswith(b'\n'):
                chunk = connection.recv(4096)
                if not chunk:
                    return bytes(data)
                data.extend(chunk)
            return bytes(data)

        def serve_console():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(5)
                    if receive_line(connection) != b'\n':
                        raise RuntimeError('serial helper did not request a prompt')
                    connection.sendall(SERIAL_PROMPT)
                    if receive_line(connection) != b'stty -echo\n':
                        raise RuntimeError('unexpected echo-off command')
                    connection.sendall(b'stty -echo\r\n' + SERIAL_PROMPT)
                    state['requested_command'] = receive_line(connection)
                    connection.sendall(b'partial runtime transcript\r\n')
                    time.sleep(1.5)
            except (OSError, RuntimeError) as exc:
                state['errors'].append(str(exc))
            finally:
                listener.close()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command_file = root / 'observer.cmd'
            output_file = root / 'observer.out'
            command_file.write_text('true\n', encoding='utf-8')
            thread = threading.Thread(target=serve_console, daemon=True)
            thread.start()
            try:
                result = subprocess.run(
                    [
                        'bash', str(HARNESS), 'serial-exec',
                        '--serial-port', str(port), '--user', 'root',
                        '--prompt', SERIAL_PROMPT.decode(),
                        '--command-file', str(command_file),
                        '--output', str(output_file),
                        '--timeout-seconds', '1',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                output = output_file.read_bytes()
            finally:
                thread.join(timeout=3)
                listener.close()

        self.assertFalse(thread.is_alive(), 'fake serial console did not finish')
        self.assertEqual([], state['errors'])
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn('reason=deadline-expired', result.stderr)
        self.assertIn(b'partial runtime transcript', output)

    def test_serial_exec_never_sends_guest_command_after_global_deadline(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.settimeout(5)
            listener.bind(('localhost', 0))
            listener.listen(1)
        except OSError:
            listener.close()
            raise
        port = listener.getsockname()[1]
        state = {'requested_command': None, 'errors': []}

        def receive_line(connection):
            data = bytearray()
            while not data.endswith(b'\n'):
                chunk = connection.recv(4096)
                if not chunk:
                    return bytes(data)
                data.extend(chunk)
            return bytes(data)

        def serve_console():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(4)
                    if receive_line(connection) != b'\n':
                        raise RuntimeError('serial helper did not request a prompt')
                    time.sleep(1.2)
                    connection.sendall(SERIAL_PROMPT)
                    if receive_line(connection) != b'stty -echo\n':
                        raise RuntimeError('unexpected echo-off command')
                    time.sleep(0.9)
                    connection.sendall(b'stty -echo\r\n' + SERIAL_PROMPT)
                    requested = receive_line(connection)
                    if requested:
                        state['requested_command'] = requested
                    else:
                        state['connection_closed'] = True
            except (ConnectionResetError, BrokenPipeError):
                state['connection_closed'] = True
            except (OSError, RuntimeError) as exc:
                state['errors'].append(str(exc))
            finally:
                listener.close()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command_file = root / 'observer.cmd'
            output_file = root / 'observer.out'
            command_file.write_text('true\n', encoding='utf-8')
            thread = threading.Thread(target=serve_console, daemon=True)
            thread.start()
            try:
                result = subprocess.run(
                    [
                        'bash', str(HARNESS), 'serial-exec',
                        '--serial-port', str(port), '--user', 'root',
                        '--prompt', SERIAL_PROMPT.decode(),
                        '--command-file', str(command_file),
                        '--output', str(output_file),
                        '--timeout-seconds', '2',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            finally:
                thread.join(timeout=4)
                listener.close()

        self.assertFalse(thread.is_alive(), 'fake serial console did not finish')
        self.assertEqual([], state['errors'])
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIsNone(state['requested_command'])
        self.assertTrue(state.get('connection_closed'))
        self.assertIn('deadline-expired', result.stderr)

    def test_serial_exec_persists_login_diagnostics_when_prompt_is_missing(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.settimeout(3)
            listener.bind(('localhost', 0))
            listener.listen(1)
        except OSError:
            listener.close()
            raise
        port = listener.getsockname()[1]
        errors = []

        def serve_console():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(2)
                    if connection.recv(4096) != b'\n':
                        raise RuntimeError('serial helper did not request a prompt')
                    connection.sendall(b'guest boot diagnostic: no login prompt\r\n')
            except (OSError, RuntimeError) as exc:
                errors.append(str(exc))
            finally:
                listener.close()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command_file = root / 'observer.cmd'
            output_file = root / 'observer.out'
            setup_output_file = root / 'observer.setup.out'
            command_file.write_text('true\n', encoding='utf-8')
            thread = threading.Thread(target=serve_console, daemon=True)
            thread.start()
            try:
                result = subprocess.run(
                    [
                        'bash', str(HARNESS), 'serial-exec',
                        '--serial-port', str(port), '--user', 'root',
                        '--prompt', SERIAL_PROMPT.decode(),
                        '--command-file', str(command_file),
                        '--output', str(output_file),
                        '--setup-output', str(setup_output_file),
                        '--timeout-seconds', '2',
                    ],
                    capture_output=True,
                    text=True,
                    timeout=4,
                )
                setup_transcript = setup_output_file.read_bytes()
            finally:
                thread.join(timeout=2)
                listener.close()

        self.assertFalse(thread.is_alive(), 'fake serial console did not finish')
        self.assertEqual([], errors)
        self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn(
            b'guest boot diagnostic', setup_transcript
        )


if __name__ == '__main__':
    unittest.main()
