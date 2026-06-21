# bargechute — Prerequisites

Install the following before running bargechute. Each is a one-time setup.

---

## 1. Python 3.11 or later

Download from https://python.org/downloads

Verify:
```
python --version
```

---

## 2. Ollama

Ollama serves the local LLM. bargechute connects to it over HTTP on localhost:11434.

Download and install from https://ollama.com

After installation Ollama runs automatically as a Windows background service.

Verify:
```
ollama --version
```

---

## 3. qwen2.5-coder:7b model

Pull the model into Ollama (~4 GB download, one-time):

```
ollama pull qwen2.5-coder:7b
```

Verify the model is available:
```
ollama list
```

You should see `qwen2.5-coder:7b` in the output.

---

## 4. Go 1.23 or later

bargechute runs `go build` and `go test` against the Barge repository.
Go must be on your PATH.

Download from https://go.dev/dl

Verify:
```
go version
```

---

## 5. Barge repository

bargechute reads and writes Go source files in the Barge repo.

Clone it:
```
git clone https://github.com/asbassan/barge.git
```

Then set the `BARGE_PATH` environment variable to point at it:
```
$env:BARGE_PATH = "C:\path\to\barge"
```

To make it permanent, add it to your Windows system environment variables.

---

## 6. bargechute Python dependencies

From the bargechute repo root:
```
pip install -e ".[dev]"
```

---

## 7. Seed the memory

Load foundational Barge knowledge into the SQLite memory store:
```
python scripts/seed_memory.py
```

---

## Verify everything works

```
python -m pytest tests/ -v
```

All tests should pass without Ollama running — they only test the memory layer.

To test the full agent (requires Ollama + model):
```
python main.py
```

Type: `what files are in the Barge internal/build package?`
