import json
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Get your key at https://kenerateai.com/app/mcp (sign in, create a "ken_..." key)
API_KEY = os.environ["KENERATE_API_KEY"]
MCP_URL = "https://mcp.kenerateai.com/mcp"
MODEL = "kenerate/flux-2-dev"

_id = 0
_session_id = None


def _parse(r):
  if "text/event-stream" in r.headers.get("Content-Type", ""):
    result = None
    for line in r.text.splitlines():
      if line.startswith("data:"):
        result = json.loads(line[5:].strip())
    return result
  return r.json()


def rpc(method, params=None, notify=False):
  global _id, _session_id
  headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
  }
  if _session_id:
    headers["mcp-session-id"] = _session_id
  body = {"jsonrpc": "2.0", "method": method}
  if not notify:
    _id += 1
    body["id"] = _id
  if params is not None:
    body["params"] = params
  r = requests.post(MCP_URL, headers=headers, json=body)
  if _session_id is None:
    _session_id = r.headers.get("mcp-session-id")
  r.raise_for_status()
  return None if notify else _parse(r)


def tool(name, arguments):
  resp = rpc("tools/call", {"name": name, "arguments": arguments})
  if "error" in resp:
    raise RuntimeError(resp["error"])
  result = resp["result"]
  text = next(c["text"] for c in result.get("content", []) if c.get("type") == "text")
  if result.get("isError"):
    raise RuntimeError(text)
  return json.loads(text)


def generate_image(prompt, out_path="output"):
  rpc("initialize", {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {"name": "make-image", "version": "1.0"},
  })
  rpc("notifications/initialized", notify=True)

  print(f"Generating image with {MODEL}...")
  job = tool("generate_image", {"model": MODEL, "prompt": prompt})
  kind, job_id = job["jobs"][0]["kind"], job["jobs"][0]["id"]
  print(f"Job started: {kind} {job_id}")

  while True:
    status = tool("wait_for_generation", {"kind": kind, "id": job_id})
    state = status.get("status")
    print(f"Status: {state}")
    if state == "completed":
      url = status["urls"][0]
      break
    if state == "failed":
      raise RuntimeError(f"Generation failed: {status}")
    time.sleep(5)

  img = requests.get(url)
  img.raise_for_status()
  ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(
    img.headers.get("Content-Type", "").split(";")[0], ".png")
  out = out_path + ext
  with open(out, "wb") as f:
    f.write(img.content)
  print(f"Saved {out} ({url})")
  return out


if __name__ == "__main__":
  raw = open("prompt.json", encoding="utf-8").read().strip()
  try:
    data = json.loads(raw)
    prompt = data[-1] if isinstance(data, list) else raw
  except json.JSONDecodeError:
    prompt = raw
  generate_image(prompt)
