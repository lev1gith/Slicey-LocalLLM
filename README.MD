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
| `Llama-3.2-3B-Instruct` | local | 3.2B | ~2.0 GB | Q4_K_M | 131,072 |
| Claude Opus 5.5 (`claude-opus-5-5`) | frontier baseline | — | hosted | — | — |

Notes:

- All local models run with LM Studio's default inference settings.
- 8B and 12B models were too resource-intensive for this machine, and 2B models couldn't do even the most basic tasks. That leaves the 3–4B range.
- Llama 3.2 3B was trained partly on the outputs of Llama 3.1 8B and 70B (distillation). It's included as a small model that learned from a much larger one, and it adds a fourth model family (Mistral, NVIDIA, Qwen, Meta).
- The local models run through Slicey's `server` backend: Claude Code pointed at LM Studio's Anthropic-compatible API. So they get the same agent loop, tools and system prompt as Opus. Slicey asks for reasoning, so models that support it (e.g. Nemotron) run with reasoning on.
- The frontier model runs through Slicey's Claude Code backend, not LM Studio. It's selected as `Opus 5.5` in Slicey's model list, and it runs on a Claude Code subscription, so there's no per-token bill.

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
└── results/               # one folder per run (see "Run output" below)
```

### How a task runs

1. `run_benchmark.py` reads the prompts. It replaces `{TEST_FILES}` with the absolute path to `checks/test_files`, so the model gets a full path.
2. For each task, it POSTs a short Python snippet to Slicer's Web Server (`/slicer/exec`). The snippet runs `slicer_worker.py` inside Slicer.
3. The worker prepares a clean starting point, then sends the prompt:
   - clears the scene;
   - empties `outputs/`;
   - switches to a new, empty DICOM database. Your own database is reopened when the task ends;
   - sets Slicey's shared folders to `checks/test_files/outputs` (read-write) and `checks/test_files` (read-only). Slicey lists the shared folders in its system prompt, so every model gets the same prompt. `outputs/` has to be writable: when the export path was in a read-only folder, Opus refused to save there. Your own list is put back when the task ends;
   - resets Slicey's conversation and its session token counter;
   - selects the model;
   - sends the prompt through `logic.sendUserMessage`.
4. It waits for Slicey's `turn_finished` event, for up to 150 s. On a timeout it cancels the turn and waits for Slicey to become idle again.
5. The worker runs the task's check from `checks/` against the scene. If the turn finished, the check decides `passed`. After a timeout the task still counts as failed, but the check runs anyway, once the turn has been cancelled, and its result is recorded separately as `passed_at_timeout`.
6. The worker reads the task's token usage from Slicey's session counters.
7. The worker then saves the scene as an `.mrb` file and copies Slicey's chat log for the task into the run folder, and returns the result to the runner. This happens after the check, because saving a scene can change the file paths the checks read.
8. The runner adds timing and run info, then appends one line to the run's `results.jsonl`.

### Run output

Each run gets its own folder, named after the model and the start time. A `/` in the model name becomes `_`.

```
results/qwen3-5-4b_2026-11-14T15-02-11/
├── results.jsonl              # one line per task attempt
└── outputs/
    ├── task01_rep1_outp.mrb   # the scene the model left behind (open in Slicer: File → Load Scene)
    ├── task01_rep1_chat.md    # Slicey's chat log: the code the model ran, its errors and replies
    └── ...
```

The `.mrb` shows *what* the model produced, and the chat log shows *how* it got there. A scene is saved for every outcome except `worker_error`; for a timeout it's saved after the turn was cancelled. Each `.mrb` contains every file loaded into the scene, so runs add up quickly (about 7 MB for a task with MRHead).

### Result records

Each line of `results.jsonl` is one task attempt:

| Field | Meaning |
|---|---|
| `outcome` | `finished`, `timeout`, `slicey_error` (Slicey reported an error), `worker_error`, `request_error` or `code_error` (harness problems) |
| `passed` | `true` / `false` from the check; `null` if the task wasn't scored (no check, checker crashed, harness error) |
| `failures` | what the check found wrong, when `passed` is `false` |
| `passed_at_timeout`, `failures_at_timeout` | timeouts only: the check's result on the scene the model left behind. `passed` stays `false`, so `passed_at_timeout: true` means the work was right but the model didn't end its turn in time |
| `llm_s`, `wall_s` | time from prompt to end of turn, and total time for the task |
| `task_id`, `repeat`, `run_id`, `model`, `timestamp` | which attempt this was |
| `cancel_clean` | after a timeout: whether Slicey was idle again before the next task |
| `errors`, `checker_error` | error messages from Slicey or from the check, if any |
| `session_usage` | tokens the task used: `inputTokens`, `outputTokens`, `costUsd`, `costEstimateIncomplete` (see below) |
| `scene_file`, `chat_log` | the task's saved `.mrb` and chat log, relative to the run folder; `null` if saving failed |
| `scene_error`, `chat_log_error` | why saving the scene or copying the chat log failed (saving never changes the outcome) |

#### Token usage

`session_usage` comes from Slicey's session counters, which are reset at the start of every task, so the numbers cover that task only. They're read after the turn ends, and for a timeout after it has been cancelled.

- **Local models** (agent backend through LM Studio): Slicey counts tokens only when the agent reports the end of a turn. A cancelled turn still reports its usage, so timed-out tasks have real counts too.
- **Claude Opus** (Claude Code backend): Slicey records the token counts that Claude Code reports.
- **Cost:** `costUsd` is `0` for every model. Local models aren't billed per token, and Opus runs on a Claude Code subscription. To compare costs, estimate them from `inputTokens` and `outputTokens` and the API price.
- **Harness errors** (`request_error`, `code_error`, `worker_error`) have no `session_usage` field, because no model ran.

## Running the benchmark

### Prerequisites

1. **3D Slicer 5.13** with the **Slicey** extension installed.
2. **Slicer's Web Server module** running on port **2016**, with the Slicer API (`/slicer/exec`) enabled.
3. **For the local models:** LM Studio with its local server running and the model loaded. The model name must match the one in Slicey's model list.
   **For the Opus baseline:** Slicey connected to Claude Code, so `Opus 5.5` appears in Slicey's model list.
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
python runner/run_benchmark.py --model "Opus 5.5" --tasks 01-40   # frontier baseline
python runner/run_benchmark.py --help
```

| Option | Default | Meaning |
|---|---|---|
| `--model` | `qwen3-5-4b` | model name as shown in Slicey |
| `--file` | `task_prompts.md` | task file in `tasks/` (`.md` or `.json`) |
| `--tasks` | all | task ids, e.g. `01-08,11` |
| `--repeats` | `1` | run each task this many times |

All paths are worked out from the repo's own location, so you can run the runner from any folder. The run folder is printed at the start (`Run <model>_<timestamp> -> results/<model>_<timestamp>`). Each task is written to disk as soon as it finishes, so stopping with Ctrl+C keeps the results collected so far.

### Testing checks without a model

A check should fail on an empty scene and pass on a correct one. To test this, set up both by hand in Slicer's Python console and call the check directly:

```python
import runpy
run_check = runpy.run_path("<repo>/checks/checkManager.py")["run_check"]
slicer.mrmlScene.Clear(0)
print(run_check("01"))   # empty scene -> passed: False
```
