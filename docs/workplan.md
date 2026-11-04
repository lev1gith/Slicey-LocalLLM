# Slicey Model Testing Workplan

## Setup

### Hardware

- **Computer:** 2025 MacBook Air with Apple M4 chip and 16 GB unified memory.
- Slicer, LM Studio, macOS, and the model all share this memory, so benchmark with Slicer open and record memory pressure as well as model file size.
- Use public, anonymized sample data only.

### Local model server

- **Chosen starting point: LM Studio.** It has the best performance from the three local model servers for running local models, runs natively on Apple Silicon, provides a local API server, and is straightforward to use for loading models and checking which model is serving requests.
- **Docker Model Runner:** a second local option. On Apple Silicon it uses the `llama.cpp` backend with Metal acceleration and serves models through an API. It is useful for container-based distribution and repeatable setup.
- **vLLM:** an option for comparison on a Linux machine with a supported NVIDIA GPU, where it is commonly used for higher-throughput serving. Apple Silicon support is an experimental/native or plugin-based route, so it is not the primary setup for this MacBook Air.


## Model selection

The following models have been tried in LM Studio. 

| Model | Parameters | Size | Quantization | Max context length | Inference settings |
|---|---:|---:|---|---:|---|
| `Mistralai/Ministral-3` | 3B | 3.0 GB | Q4_K_M | 262,144 | Default |
| `nvidia/nemotron-3-nano` | 4B | 2.8 GB | Q4_K_M | 1,048,576 | Default |
| `qwen3-5-4b` | 4.3B | 2.8 GB | Q4 | 262,144 | Default |
| `qwen3-5-2b` | 2B | 1.3 GB | Q4 | 262,144 | Default |
| `granite-3-3-2b` | 2B | 1.5 GB | Q4 | 131,072 | Default |
| `gemma-2-2b` | 2B | 1.7 GB | Q4 | 8,192 | Default |

- 8 and 12B parameter models were tested but were found to be too resource intensive
- 2B parameter models couldn't perform even the most basic tasks
- 4B parameter models had decent performance and could perform some basic tasks so they are going to be the chosen local models.
- Use the three tested ≈4B-class models, Qwen3.5 4B and NVIDIA Nemotron 3 4B, and Ministral-3-3B, for the main local-model comparison. They run well enough on the laptop while leaving more room for Slicer than larger candidates.

## Benchmark and baseline plan

1. **Finalize the task set:** select 30–50 common Slicer actions from [`tasks.md`](tasks.md), including loading data, segmenting, measuring, configuring views, and exporting.
2. **Prepare each task:** define its prompt, public input data or fixture, clean starting scene, and expected result.
3. **Write automatic test cases:** for every task, add a pass/fail check that inspects the Slicer scene or verifies output files and their contents.
4. **Build the headless runner:** start a clean Slicer instance for each run, send the task to Slicey through `SliceyLogic.sendUserMessage()`, wait for completion, and run the corresponding automatic check.
5. **Log run statistics:** have the runner save model and inference settings, pass/fail result, number of chat turns, tokens used, elapsed time, and errors. Use Slicey's saved chat or usage data for turn and token counts where available.
6. **Run the baseline:** run the same task set through one frontier model and each selected local model, using the same prompts, fixtures, Slicer version, and starting scenes.
7. **Repeat and compare:** repeat runs for each task and model, calculate success rates with confidence intervals, and compare turns and token use.

## Guidance experiments

After measuring the baseline, add one guidance technique at a time and rerun the same tasks:

- Higher-level Slicer tools for common actions.
- Retrieved Slicer code examples and forum answers.
- Task-specific step-by-step recipes.
- Python error messages and scene state fed back for retries.
- Constrained tool-call output, such as a JSON schema.

Compare each technique on its own, then combine the useful ones. Keep task prompts, checks, and model settings consistent between baseline and guidance runs.

## Deliverables

- Open-source benchmark tasks, automatic checks, and runner.
- Results table comparing frontier and local models, then guidance techniques.
- Useful guidance changes developed on a SlicerSandbox branch and proposed for Slicey.
- Short write-up for the Slicer forum; consider a workshop paper or degree-project report if the results support it.

## References

- [LM Studio system requirements](https://lmstudio.ai/docs/app/system-requirements)
- [LM Studio local API server](https://lmstudio.ai/docs/developer/core/server)
- [Docker Model Runner inference engines and platform support](https://docs.docker.com/ai/model-runner/inference-engines/)
- [vLLM installation and Apple Silicon notes](https://docs.vllm.ai/en/latest/getting_started/installation/)
