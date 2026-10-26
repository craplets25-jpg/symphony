#!/usr/bin/env python3
"""One real, harmless app-server inference; prints only sanitized evidence."""

import json
import os
import queue
import signal
import subprocess
import tempfile
import threading
import time

from runner import environment


with tempfile.TemporaryDirectory(prefix="aurelio-app-server-") as workspace:
    process = subprocess.Popen(
        ["codex", "app-server"], cwd=workspace, env=environment(),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, start_new_session=True,
    )
    messages = queue.Queue()

    def read_messages():
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except json.JSONDecodeError:
                pass
        messages.put({"transport_closed": True})

    threading.Thread(target=read_messages, daemon=True).start()

    def send(method, params, request_id=None):
        message = {"method": method, "params": params}
        if request_id is not None:
            message["id"] = request_id
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def receive(predicate, timeout=60):
        deadline = time.monotonic() + timeout
        while True:
            message = messages.get(timeout=max(0.01, deadline - time.monotonic()))
            if message.get("transport_closed"):
                raise RuntimeError("app-server transport closed")
            if predicate(message):
                if "error" in message:
                    raise RuntimeError("RPC error: " + str(message["error"].get("code")))
                return message
            if time.monotonic() >= deadline:
                raise TimeoutError("No matching app-server response")

    try:
        send("initialize", {"clientInfo": {"name": "aurelio_readiness_probe", "version": "1.0"}}, 1)
        receive(lambda message: message.get("id") == 1)
        send("initialized", {})
        print("initialize: passed", flush=True)
        send("account/read", {"refreshToken": False}, 2)
        account = receive(lambda message: message.get("id") == 2)["result"]
        print("account/read:", json.dumps({
            "account_present": bool(account.get("account")),
            "type": (account.get("account") or {}).get("type"),
            "requiresOpenaiAuth": account.get("requiresOpenaiAuth"),
        }), flush=True)
        send("thread/start", {"cwd": workspace, "sandbox": "read-only", "approvalPolicy": "never"}, 3)
        thread = receive(lambda message: message.get("id") == 3)["result"]["thread"]["id"]
        print("thread:", thread, flush=True)
        send("turn/start", {
            "threadId": thread, "cwd": workspace, "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly"},
            "input": [{"type": "text", "text": "Reply with exactly READY. Do not use tools or access files."}],
        }, 4)
        turn = receive(lambda message: message.get("id") == 4)["result"]["turn"]["id"]
        print("turn:", turn, flush=True)
        answers = []

        def completed(message):
            if message.get("method") == "item/completed":
                item = message.get("params", {}).get("item", {})
                if item.get("type") == "agentMessage":
                    answers.append(item.get("text", ""))
            return message.get("method") == "turn/completed"

        final = receive(completed, timeout=120)["params"]["turn"]
        if final.get("status") != "completed" or "READY" not in answers:
            raise RuntimeError("Inference did not complete with READY; status=" + str(final.get("status")))
        print("inference: completed; response: READY", flush=True)
    finally:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        print("app-server stopped:", process.returncode, flush=True)
