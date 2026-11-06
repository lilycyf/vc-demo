"""Pod-scoped spending deadline; credentials stay in container process memory."""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BASE = "https://api.runpod.io/v2/pods/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pod-id", required=True)
    parser.add_argument("--deadline", required=True)
    parser.add_argument("--state", default="/workspace/t47d_budget_guard_state.json")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    deadline = datetime.fromisoformat(args.deadline).timestamp()
    pairs = [p.split(b"=", 1) for p in Path("/proc/1/environ").read_bytes().split(b"\0") if b"=" in p]
    container_env = {k.decode(): v.decode() for k, v in pairs}
    if container_env.get("RUNPOD_POD_ID") != args.pod_id:
        raise ValueError("Guard may operate only on its own Pod")
    session = requests.Session()
    session.headers["Authorization"] = "Bearer " + container_env["RUNPOD_API_KEY"]
    response = session.get(BASE + args.pod_id, timeout=30)
    response.raise_for_status()
    if response.json().get("id") != args.pod_id:
        raise ValueError("Authenticated Pod identity mismatch")
    state = {"pod_id": args.pod_id, "deadline_utc": datetime.fromtimestamp(deadline, timezone.utc).isoformat(),
             "deadline_beijing": datetime.fromtimestamp(deadline, timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).isoformat(),
             "pid": os.getpid(), "api_self_check": "passed", "mode": "check_only" if args.check_only else "armed",
             "credential_storage": "existing container environment only; never logged or persisted to volume",
             "action": "stop current Pod, never delete Pod or Network Volume"}
    if args.check_only:
        print(json.dumps(state), flush=True)
        return
    Path(args.state).write_text(json.dumps(state, indent=2) + "\n")
    print(json.dumps(state), flush=True)
    while time.time() < deadline:
        time.sleep(min(60, max(deadline - time.time(), 0)))
    # Source: runpod/runpodctl internal/api/pods.go podAction, REST v2.
    for attempt in range(12):
        try:
            response = session.post(BASE + args.pod_id + "/action", json={"action": "stop"}, timeout=30)
            if response.ok:
                state.update(mode="stop_requested", http_status=response.status_code)
                Path(args.state).write_text(json.dumps(state, indent=2) + "\n")
                return
            state.update(last_http_status=response.status_code, last_attempt=attempt + 1)
        except requests.RequestException as error:
            state.update(last_error_type=type(error).__name__, last_attempt=attempt + 1)
        Path(args.state).write_text(json.dumps(state, indent=2) + "\n")
        time.sleep(30)
    raise RuntimeError("Automatic stop request failed; inspect the console immediately")


if __name__ == "__main__":
    main()
