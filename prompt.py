import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


def generate_prompt() -> str:
  """Ask the LLM (prompt.txt instructions) for a new image prompt and
  append it to the prompt.json pool. Returns the prompt text."""
  with open("prompt.txt", encoding="utf-8") as f:
    prompt = f.read().strip()

  response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
      "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
      "Content-Type": "application/json",
    },
    data=json.dumps({
      "model": "x-ai/grok-4.3",
      "messages": [{"role": "user", "content": prompt}],
    })
  )

  result = response.json()
  answer = result["choices"][0]["message"]["content"]
  print(answer)

  try:
    with open("prompt.json", encoding="utf-8") as f:
      prompts = json.load(f)
    if not isinstance(prompts, list):
      prompts = [prompts]
  except (FileNotFoundError, json.JSONDecodeError):
    prompts = []
  prompts.append(answer)
  with open("prompt.json", "w", encoding="utf-8") as f:
    json.dump(prompts, f, indent=2, ensure_ascii=False)
  return answer


if __name__ == "__main__":
  import make_image
  answer = generate_prompt()
  count = len(json.load(open("prompt.json", encoding="utf-8")))
  os.makedirs("images", exist_ok=True)
  make_image.generate_image(answer, f"images/mission_{count}")
