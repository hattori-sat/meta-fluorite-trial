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
SERIAL_PROMPT = b'qa-console# '
GATE_OBSERVATION = (
    b'FLR0350_GATE_OBSERVATION version=1 pid=706 start=3089 '
    b'start_after=3089 recorded_start=3089 uid=1001 comm=sh state=S '
    b'tracer=0 syscall=read nr=0 arg1=0x0 target_type=fifo target_dev=40 '
    b'target_ino=23 gate_type=fifo gate_dev=40 gate_ino=23 gate_uid=1001 '
    b'gate_mode=600'
)
SETUP_MARKER_RE = re.compile(rb'__FLR_SERIAL_SETUP_DONE_[A-Fa-f0-9]+__')
COMMAND_MARKER_RE = re.compile(rb'__FLR_SERIAL_COMMAND_DONE_[A-Fa-f0-9]+__')


def receive_serial_line(connection):
    data = bytearray()
    while not data.endswith(b'\n'):
        chunk = connection.recv(4096)
        if not chunk:
            return bytes(data)
        data.extend(chunk)
        if len(data) > 16384:
            raise RuntimeError('serial command exceeded test bound')
    return bytes(data)


def setup_exchange(
    connection,
    setup_reply,
    *,
    state=None,
    stty_status=0,
    echo_probe=False,
    chunk_setup=False,
    stage1_reply=None,
    probe_delay=0,
):
    stage1_command = receive_serial_line(connection)
    expected_stage1 = b'stty -echo; __FLR_SERIAL_STTY_RC=$?\n'
    if stage1_command != expected_stage1:
        raise RuntimeError(f'unexpected echo-off command: {stage1_command!r}')
    if state is not None:
        state['stage1_command'] = stage1_command
    if stage1_reply is None:
        stage1_reply = stage1_command.rstrip(b'\n') + b'\r\n' + SERIAL_PROMPT
    connection.sendall(stage1_reply)

    probe_command = receive_serial_line(connection)
    marker = SETUP_MARKER_RE.search(probe_command)
    if not probe_command.startswith(b'printf ') or marker is None:
        raise RuntimeError(f'unexpected echo-off probe: {probe_command!r}')
    if state is not None:
        state['probe_command'] = probe_command
        state['setup_marker'] = marker.group(0)
    if probe_delay:
        time.sleep(probe_delay)

    response = setup_reply
    has_marker = b'{{setup_marker}}' in response
    if has_marker:
        response = response.replace(
            b'{{setup_marker}}',
            marker.group(0) + b':' + str(stty_status).encode(),
        )
    if echo_probe:
        response = probe_command.rstrip(b'\n') + b'\r\n' + response
    if chunk_setup:
        for offset in range(0, len(response), 4):
            connection.sendall(response[offset:offset + 4])
            time.sleep(0.005)
    else:
        connection.sendall(response)
    if not has_marker:
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass


class RuntimeHarnessTests(unittest.TestCase):
    def run_serial_exec_fixture(
        self,
        directory,
        setup_reply,
        command_status=0,
        chunk_setup=False,
        stty_status=0,
        echo_probe=False,
        stage1_reply=None,
        command_reply_marker=None,
    ):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.settimeout(5)
            listener.bind(('localhost', 0))
            listener.listen(1)
        except OSError:
            listener.close()
            raise
        port = listener.getsockname()[1]
        state = {'requested_command': None, 'requested_commands': [], 'errors': []}

        def serve_console():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(5)
                    if receive_serial_line(connection) != b'\n':
                        raise RuntimeError('serial helper did not request a prompt')
                    connection.sendall(SERIAL_PROMPT)
                    setup_exchange(
                        connection,
                        setup_reply,
                        state=state,
                        stty_status=stty_status,
                        echo_probe=echo_probe,
                        chunk_setup=chunk_setup,
                        stage1_reply=stage1_reply,
                    )
                    requested_command = receive_serial_line(connection)
                    state['requested_command'] = requested_command
                    if requested_command:
                        state['requested_commands'].append(requested_command)
                    if requested_command:
                        command_marker = COMMAND_MARKER_RE.search(requested_command)
                        if command_marker is None:
                            raise RuntimeError('requested command has no unique completion marker')
                        reply_marker = (
                            command_reply_marker
                            if command_reply_marker is not None
                            else command_marker.group(0)
                        )
                        connection.sendall(
                            GATE_OBSERVATION
                            + f'\r\nrc={command_status}\r\n'.encode()
                            + reply_marker + b'\n'
                            + SERIAL_PROMPT
                        )
            except BrokenPipeError:
                state['connection_closed'] = True
            except (OSError, RuntimeError) as exc:
                state['errors'].append(str(exc))
            finally:
                listener.close()

        command_file = directory / 'observer.cmd'
        output_file = directory / 'observer.out'
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
        return result, output, state

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
        self.assertIn('__FLR_SERIAL_SETUP_DONE_', text)
        self.assertIn("stty -echo; __FLR_SERIAL_STTY_RC=$?", text)
        self.assertIn('__FLR_SERIAL_COMMAND_DONE_', text)
        self.assertIn('timeout_seconds', text)
        self.assertIn('sock.sendall(b"\\n")', text)
        self.assertIn("sock.sendall(b'{\"execute\":\"qmp_capabilities\"}\\r\\n')", text)
        self.assertIn("sock.sendall(b'{\"execute\":\"quit\"}\\r\\n')", text)

    def test_serial_exec_capture_passes_strict_gate_without_setup_preamble(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, output, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'stty -echo\r\n{{setup_marker}}\r\n' + SERIAL_PROMPT,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(state['requested_command'])
        self.assertRegex(
            state['requested_command'].decode(),
            r'__FLR_SERIAL_COMMAND_DONE_[a-f0-9]{24}__',
        )
        self.assertNotIn(b'stty -echo', output)
        self.assertEqual(output.count(b'FLR0350_GATE_OBSERVATION'), 1)

    def test_serial_exec_passes_when_tty_echo_was_already_disabled(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, output, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'{{setup_marker}}\r\n' + SERIAL_PROMPT,
                stage1_reply=SERIAL_PROMPT,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(state['requested_commands']), 1)
        self.assertEqual(output.count(b'FLR0350_GATE_OBSERVATION'), 1)

    def test_serial_exec_uses_unique_setup_marker_after_duplicate_prompt_residue(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, output, state = self.run_serial_exec_fixture(
                Path(temporary),
                SERIAL_PROMPT
                + SERIAL_PROMPT
                + b'\r\n{{setup_marker}}\r\n'
                + SERIAL_PROMPT,
                chunk_setup=True,
                stage1_reply=SERIAL_PROMPT + SERIAL_PROMPT,
            )

        self.assertIsNotNone(
            state['setup_marker'],
            f"setup marker omitted; requested_commands={state['requested_commands']!r}; "
            + result.stdout + result.stderr,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"setup marker={state['setup_marker']!r}; "
            f"requested_commands={state['requested_commands']!r}; "
            + result.stdout + result.stderr,
        )
        self.assertEqual(len(state['requested_commands']), 1)
        self.assertTrue(state['requested_commands'][0].startswith(b'true; rc=$?;'))
        self.assertEqual(output.count(b'FLR0350_GATE_OBSERVATION'), 1)

    def test_serial_exec_fails_closed_on_unexpected_echo_off_response(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, _, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'unexpected serial chatter\r\n' + SERIAL_PROMPT,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('reason=echo-off-marker-not-observed', result.stderr)
        self.assertFalse(state['requested_command'])

    def test_serial_exec_fails_closed_when_setup_marker_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, _, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'wrong setup marker\r\n' + SERIAL_PROMPT,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('reason=echo-off-marker-not-observed', result.stderr)
        self.assertFalse(state['requested_commands'])

    def test_serial_exec_fails_closed_when_probe_input_is_echoed(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, _, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'{{setup_marker}}\r\n' + SERIAL_PROMPT,
                echo_probe=True,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('reason=echo-off-response-unexpected', result.stderr)
        self.assertEqual(state['probe_command'].count(state['setup_marker']), 1)
        self.assertFalse(state['requested_commands'])

    def test_serial_exec_fails_closed_when_stty_status_is_nonzero(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, _, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'{{setup_marker}}\r\n' + SERIAL_PROMPT,
                stty_status=1,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('reason=echo-off-marker-status-invalid', result.stderr)
        self.assertFalse(state['requested_commands'])

    def test_serial_exec_fails_closed_on_duplicate_prompt_after_setup_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, _, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'{{setup_marker}}\r\n' + SERIAL_PROMPT + SERIAL_PROMPT,
                chunk_setup=True,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('reason=echo-off-response-unexpected', result.stderr)
        self.assertFalse(state['requested_commands'])

    def test_serial_exec_preserves_guest_command_output_and_nonzero_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, output, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'{{setup_marker}}\r\n' + SERIAL_PROMPT,
                command_status=23,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('command_status=23', result.stderr)
        self.assertEqual(output.count(b'FLR0350_GATE_OBSERVATION'), 1)
        self.assertEqual(len(state['requested_commands']), 1)

    def test_serial_exec_rejects_stale_fixed_completion_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            result, _, state = self.run_serial_exec_fixture(
                Path(temporary),
                b'{{setup_marker}}\r\n' + SERIAL_PROMPT,
                command_reply_marker=b'__FLR_SERIAL_COMMAND_DONE_7B31__',
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('reason=completion-marker-not-observed', result.stderr)
        self.assertEqual(len(state['requested_commands']), 1)

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

        def serve_console():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(5)
                    if receive_serial_line(connection) != b'\n':
                        raise RuntimeError('serial helper did not request a prompt')
                    connection.sendall(SERIAL_PROMPT)
                    setup_exchange(
                        connection,
                        b'{{setup_marker}}\r\n' + SERIAL_PROMPT,
                    )
                    state['requested_command'] = receive_serial_line(connection)
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

        def serve_console():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(4)
                    if receive_serial_line(connection) != b'\n':
                        raise RuntimeError('serial helper did not request a prompt')
                    time.sleep(1.2)
                    connection.sendall(SERIAL_PROMPT)
                    setup_exchange(
                        connection,
                        b'{{setup_marker}}\r\n' + SERIAL_PROMPT,
                        probe_delay=0.9,
                    )
                    requested = receive_serial_line(connection)
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
