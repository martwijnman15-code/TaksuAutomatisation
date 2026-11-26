import sys
import unittest
import subprocess
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import main

class StatusTests(unittest.TestCase):
    def test_streams_output_before_command_finishes(self):
        received = threading.Event()
        lines = []
        def output(line):
            lines.append(line)
            received.set()
        errors = []
        def run():
            try:
                main.run_status_command([sys.executable, '-u', '-c', "import time; print('progress'); time.sleep(1); print('warning', file=__import__('sys').stderr)"], output)
            except BaseException as exc:
                errors.append(exc)
        worker = threading.Thread(target=run)
        worker.start()
        arrived = received.wait(.8)
        still_running = worker.is_alive()
        worker.join()
        self.assertEqual(errors, [])
        self.assertTrue(arrived and still_running, 'progress must arrive before process completion')
        self.assertEqual(lines, ['progress', 'warning'])

    def test_reports_nonzero_exit(self):
        lines = []
        with self.assertRaises(subprocess.CalledProcessError):
            main.run_status_command([sys.executable, '-c', "print('failed'); raise SystemExit(7)"], lines.append)
        self.assertEqual(lines, ['failed'])

if __name__ == '__main__':
    unittest.main()
