"""
This script will continously monitor docker container logs and aggregate the stacktrace of error logs
Aggregated error logs will be stored as a timestamped json object in a file for further processing
"""

import subprocess
import re
import time
import json

# Your Jenkins container name or ID
CONTAINER_NAME = "jenkins"
OUTPUT_FILE = "stacktraces.jsonl"

# Matches a Jenkins-style timestamp line
TIMESTAMP_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+\+\d{4}")

def is_timestamp_line(line: str) -> bool:
    return bool(TIMESTAMP_REGEX.match(line.strip()))

def monitor_docker_logs():
    print(f"🔍 Monitoring logs from container: {CONTAINER_NAME}")
    process = subprocess.Popen(
        ["docker", "logs", "-f", CONTAINER_NAME],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    buffer = []
    buffering = False

    for line in iter(process.stdout.readline, ""):
        line = line.rstrip()

        if is_timestamp_line(line):
            if "SEVERE" in line:
                if buffering and buffer:
                    write_stacktrace(buffer)
                    buffer = []
                buffering = True
                print(f"🟡 Start of stacktrace: {line}")
                buffer.append(line)
            elif buffering:
                # New timestamp, so end of previous stacktrace
                write_stacktrace(buffer)
                buffer = []
                buffering = False

        elif buffering:
            buffer.append(line)

    process.stdout.close()
    process.wait()

def write_stacktrace(lines):
    if not lines:
        return
    stacktrace_json = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "stacktrace": "\n".join(lines)
    }
    with open(OUTPUT_FILE, "a") as out:
        json.dump(stacktrace_json, out)
        out.write("\n")
    print(f"✅ Stacktrace saved with {len(lines)} lines")

if __name__ == "__main__":
    monitor_docker_logs()
