"""Fail-closed Mini process/port visibility gate for FLR-0416 QEMU."""

import argparse
import os
import re
import stat
import subprocess
import sys


class PreflightError(RuntimeError):
    pass


def _unescape_mount_path(value):
    return (
        value.replace("\\040", " ")
        .replace("\\011", "\t")
        .replace("\\012", "\n")
        .replace("\\134", "\\")
    )


def _validate_proc_visibility(mountinfo_text):
    proc_mounts = []
    for line in mountinfo_text.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        try:
            separator = fields.index("-")
        except ValueError as error:
            raise PreflightError("proc-visibility-mountinfo-malformed") from error
        if separator < 6 or len(fields) <= separator + 3:
            raise PreflightError("proc-visibility-mountinfo-malformed")
        filesystem = fields[separator + 1]
        mountpoint = _unescape_mount_path(fields[4])
        if filesystem == "proc" and mountpoint == "/proc":
            mount_options = fields[5].split(",")
            super_options = fields[separator + 3].split(",")
            proc_mounts.append(mount_options + super_options)

    if len(proc_mounts) != 1:
        raise PreflightError("proc-visibility-mount-not-unique")

    hidepid = [
        option.split("=", 1)[1]
        for option in proc_mounts[0]
        if option.startswith("hidepid=")
    ]
    if any(value not in ("0", "off") for value in hidepid):
        raise PreflightError("proc-visibility-hidepid-enabled-or-unknown")


def _pid_directory_state(path):
    try:
        return os.stat(path).st_mode
    except FileNotFoundError:
        return None
    except OSError as error:
        raise PreflightError("proc-entry-state-unverifiable") from error


def _read_proc_file(path, pid_directory):
    try:
        with open(path, "rb") as stream:
            return stream.read()
    except OSError as error:
        if _pid_directory_state(pid_directory) is None:
            return None
        if isinstance(error, PermissionError):
            raise PreflightError("proc-entry-unreadable") from error
        if isinstance(error, FileNotFoundError):
            raise PreflightError("proc-entry-incomplete") from error
        raise PreflightError("proc-entry-read-failed") from error


def _target_kinds(comm, arguments):
    names = [os.path.basename(value.rstrip("/")) for value in [comm] + arguments]
    kinds = set()
    if any(name.startswith("qemu-system-") for name in names):
        kinds.add("qemu")
    if "runqemu" in names:
        kinds.add("runqemu")
    if "flutter-auto" in names:
        kinds.add("flutter-auto")
    if any(name == "gdb" or name.startswith("gdb-") for name in names):
        kinds.add("gdb")
    if "devtool" in names:
        kinds.add("devtool")
    if "bitbake" in names or "bitbake-server" in names:
        kinds.add("bitbake")
    return sorted(kinds)


def _status_identity(path, pid_directory):
    content = _read_proc_file(path, pid_directory)
    if content is None:
        return None
    uid_match = re.search(rb"^Uid:\s+(\d+)", content, re.MULTILINE)
    state_match = re.search(rb"^State:\s+(\S+)", content, re.MULTILINE)
    if uid_match is None or state_match is None:
        raise PreflightError("proc-entry-identity-incomplete")
    return int(uid_match.group(1)), state_match.group(1).decode("ascii", "replace")


def scan_processes(proc_root="/proc", mountinfo_path="/proc/self/mountinfo"):
    """Inspect every visible numeric PID, rejecting any unverified live entry."""
    try:
        with open(mountinfo_path, "r", encoding="utf-8") as stream:
            mountinfo_text = stream.read()
    except OSError as error:
        raise PreflightError("proc-visibility-mountinfo-unreadable") from error
    _validate_proc_visibility(mountinfo_text)

    try:
        entries = list(os.scandir(proc_root))
    except OSError as error:
        raise PreflightError("proc-enumeration-failed") from error

    scanned = 0
    disappeared = 0
    owners = []
    for entry in entries:
        if not entry.name.isdigit():
            continue
        pid_directory = os.path.join(proc_root, entry.name)
        try:
            mode = os.stat(pid_directory).st_mode
        except FileNotFoundError:
            disappeared += 1
            continue
        except OSError as error:
            raise PreflightError("proc-entry-state-unverifiable") from error
        if not stat.S_ISDIR(mode):
            raise PreflightError("proc-entry-not-directory")
        scanned += 1

        raw_comm = _read_proc_file(os.path.join(pid_directory, "comm"), pid_directory)
        if raw_comm is None:
            disappeared += 1
            continue
        raw_cmdline = _read_proc_file(os.path.join(pid_directory, "cmdline"), pid_directory)
        if raw_cmdline is None:
            disappeared += 1
            continue
        comm = raw_comm.decode("utf-8", "replace").strip()
        arguments = [
            os.fsdecode(value)
            for value in raw_cmdline.split(b"\0")
            if value
        ]
        kinds = _target_kinds(comm, arguments)
        if not kinds:
            continue

        identity = _status_identity(os.path.join(pid_directory, "status"), pid_directory)
        if identity is None:
            disappeared += 1
            continue
        uid, state = identity
        owners.append(
            {
                "pid": int(entry.name),
                "uid": uid,
                "kind": kinds,
                "state": state,
            }
        )

    return {
        "scanned": scanned,
        "disappeared": disappeared,
        "owners": sorted(owners, key=lambda owner: owner["pid"]),
    }


def check_ports_free(ports, ss_binary="ss", runner=subprocess.run):
    """Check only requested listening TCP ports; query errors are never free."""
    values = list(ports)
    if not values or any(
        not isinstance(port, int) or isinstance(port, bool) or port < 1 or port > 65535
        for port in values
    ):
        raise PreflightError("port-list-invalid")
    normalized = sorted(set(values))

    for port in normalized:
        query = [ss_binary, "-H", "-ltn", "( sport = :%d )" % port]
        try:
            result = runner(query, capture_output=True, text=True, check=False, timeout=5)
        except (OSError, subprocess.SubprocessError) as error:
            raise PreflightError("port-inspection-failed") from error
        if result.returncode != 0 or (result.stderr or "").strip():
            raise PreflightError("port-inspection-failed")
        if (result.stdout or "").strip():
            raise PreflightError("port-in-use:%d" % port)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="append", type=int, required=True)
    arguments = parser.parse_args(argv)
    try:
        scan = scan_processes()
        owners = scan["owners"]
        if owners:
            summary = ",".join(
                "%s(pid=%d,uid=%d,state=%s)"
                % ("+".join(owner["kind"]), owner["pid"], owner["uid"], owner["state"])
                for owner in owners
            )
            raise PreflightError("residual-owner:" + summary)
        check_ports_free(arguments.port)
    except PreflightError as error:
        print("FLR0416_PREFLIGHT=FAIL reason=%s" % error, file=sys.stderr)
        return 1

    print(
        "FLR0416_PREFLIGHT=PASS proc_visibility=hidepid-off scanned_processes=%d "
        "disappeared_during_scan=%d target_owners=0 ports=%s"
        % (
            scan["scanned"],
            scan["disappeared"],
            ",".join(str(port) for port in sorted(set(arguments.port))),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
