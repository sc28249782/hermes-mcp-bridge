"""Run the mandatory offline suite and inspect its complete post-exit output."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    here = Path(__file__).resolve().parent
    print(json.dumps({"evidence_class": "ci-environment-facts", "python": sys.version,
                      "procfs_coherent": os.getpid() == int(Path('/proc/self/stat').read_text().split()[0]),
                      "r1_complete": False, "r2_authorized": False}), flush=True)
    result = subprocess.run([sys.executable, '-W', 'error::ResourceWarning', '-B',
                             '-m', 'unittest', '-v', 'test_observation', 'test_r1_integration',
                             'test_joined_collect'], cwd=here,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=120, check=False)
    raw = result.stdout
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    warnings = [marker.decode() for marker in (b'ResourceWarning', b'Exception ignored in',
                b'Exception ignored while finalizing database', b'PytestUnraisableExceptionWarning') if marker in raw]
    counts = re.findall(rb'^Ran (\d+) tests? in ', raw, re.M)
    complete = counts == [b'69'] and re.search(rb'^OK\s*$', raw, re.M) is not None
    print(json.dumps({"suite_exit": result.returncode, "expected_tests": 69,
                      "complete_without_skips": complete, "warning_markers": warnings,
                      "r1_complete": False, "r2_authorized": False}), flush=True)
    return result.returncode or int(bool(warnings) or not complete)


if __name__ == '__main__':
    raise SystemExit(main())
