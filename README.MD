# Slicey-LocalLLM

A benchmark for how well local language models can drive [3D Slicer](https://www.slicer.org/) through the Slicey assistant. Each task is a natural-language prompt (e.g. "load this NRRD file"). The runner sends it to Slicey, waits for the model to finish, then checks the resulting Slicer scene automatically and records pass/fail.

The goal is to compare small local models against a frontier model on the same tasks, and then measure how much guidance techniques (code examples, recipes, error feedback) improve the local models. See [`docs/workplan.md`](docs/workplan.md) for the full plan.

## Setup

### Hardware

| | |
|---|---|
| Computer | 2025 MacBook Air, Apple M4 |
| Memory | 16 GB unified memory |

Slicer, the model server, macOS and the model all share the same 16 GB. The models were chosen to leave enough room for Slicer while they run. All data used is public sample data or small synthetic fixtures.

### Local model server: LM Studio

[LM Studio](https://lmstudio.ai/) serves the local models. It was chosen because:

- it gave the best performance of the local servers tried on this machine;
- it runs natively on Apple Silicon;
- it provides a local API server that Slicey connects to;
- it makes it easy to load models and see which model is serving requests.

Alternatives considered:

- **Docker Model Runner** uses `llama.cpp` with Metal on Apple Silicon. It's useful for container-based, repeatable setups.
- **vLLM** is the usual choice on Linux with an NVIDIA GPU. Its Apple Silicon support is experimental, so it isn't used here.

### Models

| Model | Role | Parameters | Size | Quantization | Max context |
|---|---|---:|---:|---|---:|
| `mistralai/Ministral-3` | local | 3B | 3.0 GB | Q4_K_M | 262,144 |
| `nvidia/nemotron-3-nano` | local | 4B | 2.8 GB | Q4_K_M | 1,048,576 |
| `qwen3-5-4b` | local | 4.3B | 2.8 GB | Q4 | 262,144 |
| `Hunyuan-4B-Instruct` | local | 4B | — | — | — |
| Claude Opus 5.5 (`claude-opus-5-5`) | frontier baseline | — | API | — | — |

Notes:

- All local models run with LM Studio's default inference settings.
- 8B and 12B models were too resource-intensive for this machine, and 2B models couldn't do even the most basic tasks. That leaves the 3–4B range.
- The frontier model runs through Slicey's `claude-api` backend, not LM Studio.

## Repository structure

```
Slicey-LocalLLM/
├── runner/
│   ├── run_benchmark.py   # runs on your machine: loads tasks, sends each to Slicer, saves results
│   └── slicer_worker.py   # runs inside Slicer: resets the scene, prompts Slicey, waits, runs the check
├── checks/
│   ├── checkManager.py    # finds the check for a task id and runs it (CheckContext helpers)
│   ├── checkLoad.py       # checks for the loading tasks (01–08)
│   └── test_files/        # fixtures the prompts refer to (see test_files/README.md)
│       └── outputs/       # where tasks write files; emptied before every task
├── tasks/
│   ├── task_prompts.md    # the task prompts, one "### <id> — <title>" section each
│   └── tasks.json         # JSON version of the tasks
├── tools/
│   └── json_converter.py  # converts task_prompts.md to JSON
├── docs/
│   ├── workplan.md        # setup, model selection and benchmark plan
│   └── tasks.md           # the candidate tasks and their intended checks
└── results/               # one folder per run: results/<timestamp>/results.jsonl
```

### How a task runs

1. `run_benchmark.py` reads the prompts. It replaces `{TEST_FILES}` with the absolute path to `checks/test_files`, so the model gets a full path.
2. For each task, it POSTs a short Python snippet to Slicer's Web Server (`/slicer/exec`). The snippet runs `slicer_worker.py` inside Slicer.
3. The worker prepares a clean starting point, then sends the prompt:
   - clears the scene;
   - empties `outputs/`;
   - resets Slicey's conversation;
   - selects the model;
   - sends the prompt through `logic.sendUserMessage`.
4. It waits for Slicey's `turn_finished` event, for up to 150 s. On a timeout it cancels the turn and waits for Slicey to become idle again.
5. If the turn finished, the worker runs the task's check from `checks/` against the scene and returns the result to the runner.
6. The runner adds timing and run info, then appends one line to `results/<run_id>/results.jsonl`.

### Result records

Each line of `results.jsonl` is one task attempt:

| Field | Meaning |
|---|---|
| `outcome` | `finished`, `timeout`, `slicey_error` (Slicey reported an error), `worker_error`, `request_error` or `code_error` (harness problems) |
| `passed` | `true` / `false` from the check; `null` if the task wasn't scored (no check, checker crashed, harness error) |
| `failures` | what the check found wrong, when `passed` is `false` |
| `llm_s`, `wall_s` | time from prompt to end of turn, and total time for the task |
| `task_id`, `repeat`, `run_id`, `model`, `timestamp` | which attempt this was |
| `cancel_clean` | after a timeout: whether Slicey was idle again before the next task |
| `errors`, `checker_error` | error messages from Slicey or from the check, if any |

## Running the benchmark

### Prerequisites

1. **3D Slicer 5.13** with the **Slicey** extension installed.
2. **Slicer's Web Server module** running on port **2016**, with the Slicer API (`/slicer/exec`) enabled.
3. **LM Studio** with its local server running and the model loaded. The model name must match the one in Slicey's model list.
4. **Python 3** with `requests` (`pip install requests`) for the runner. The runner uses your normal Python, not Slicer's.

Check that Slicer's exec endpoint is reachable:

```bash
curl -X POST http://localhost:2016/slicer/exec --data '__execResult = {"hello": 1}'
# -> {"hello": 1}
```

### Run

```bash
python runner/run_benchmark.py                          # all tasks, default model
python runner/run_benchmark.py --tasks 01-08            # only tasks 01 to 08
python runner/run_benchmark.py --model nemotron-3-nano --tasks 01-08,11 --repeats 3
python runner/run_benchmark.py --help
```

| Option | Default | Meaning |
|---|---|---|
| `--model` | `qwen3-5-4b` | model name as shown in Slicey |
| `--file` | `task_prompts.md` | task file in `tasks/` (`.md` or `.json`) |
| `--tasks` | all | task ids, e.g. `01-08,11` |
| `--repeats` | `1` | run each task this many times |

All paths are worked out from the repo's own location, so you can run the runner from any folder. The run folder is printed at the start (`Run <id> -> results/<id>`). Each task is written to disk as soon as it finishes, so stopping with Ctrl+C keeps the results collected so far.

### Testing checks without a model

A check should fail on an empty scene and pass on a correct one. To test this, set up both by hand in Slicer's Python console and call the check directly:

```python
import runpy
run_check = runpy.run_path("<repo>/checks/checkManager.py")["run_check"]
slicer.mrmlScene.Clear(0)
print(run_check("01"))   # empty scene -> passed: False
```
