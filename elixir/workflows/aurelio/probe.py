#!/usr/bin/env python3
"""One real, harmless app-server inference; prints only sanitized evidence."""

import json
import os
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time

from runner import SKILLS, environment


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
        skill_inputs = []
        if "--skills" in sys.argv:
            send("skills/list", {"cwds": [workspace], "forceReload": True}, 5)
            discovered = receive(lambda message: message.get("id") == 5)["result"]["data"]
            entry = next(entry for entry in discovered if entry["cwd"] == workspace)
            if entry["errors"]:
                raise RuntimeError("Skill discovery errors")
            for name in SKILLS:
                matches = [skill for skill in entry["skills"] if skill["name"] == name and skill["enabled"]]
                if len(matches) != 1:
                    raise RuntimeError("Expected one enabled shared skill: " + name)
                skill_inputs.append({"type": "skill", "name": name, "path": matches[0]["path"]})
                print("discovered skill:", name, matches[0]["path"], flush=True)
        send("thread/start", {"cwd": workspace, "sandbox": "read-only", "approvalPolicy": "never"}, 3)
        thread = receive(lambda message: message.get("id") == 3)["result"]["thread"]["id"]
        print("thread:", thread, flush=True)
        prompt = "Reply with exactly READY. Do not use tools or access files."
        if skill_inputs:
            prompt = (
                "This is an authorized, non-mutating compatibility test. Invoke $linear $commit $pull $push $land "
                "by reading their supplied instructions, but do not commit, push, create or merge a PR. "
                "Use the connected native GitHub plugin to read metadata for craplets25-jpg/aurelio-trade. "
                "Do not use gh API calls. After all five skills and that real native plugin read succeed, reply READY."
            )
        send("turn/start", {
            "threadId": thread, "cwd": workspace, "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly"},
            "input": [{"type": "text", "text": prompt}, *skill_inputs],
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
