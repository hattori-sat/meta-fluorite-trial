import ast
from pathlib import Path
import re
import subprocess
import unittest


HARNESS = Path(__file__).resolve().parents[1] / 'scripts/qemu-runtime-harness.sh'


class RuntimeHarnessTests(unittest.TestCase):
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
        self.assertEqual(text.count(r'\r\n'), 2)


if __name__ == '__main__':
    unittest.main()
