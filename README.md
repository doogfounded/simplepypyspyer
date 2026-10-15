# PyPy JIT Interactive Laboratory

An interactive, visual laboratory to explore, benchmark, and inspect PyPy's adaptive Tracing JIT compiler in real-time.

Zero external dependencies required (uses only the standard library and PyPy's built-in `pypyjit` module).

---

## Quickstart

### Method 1: The 1-Line Way (Using `uv`)

No manual PyPy installation needed. [`uv`](https://github.com/astral-sh/uv) automatically fetches a portable PyPy runtime and runs the lab across Windows, macOS, or Linux:

```bash
uv run --python pypy-3.11 pypy3 tools/pypy_jit_lab.py
```

### Method 2: Using an Existing PyPy 3 Installation

If you already have `pypy3` installed:

```bash
pypy3 tools/pypy_jit_lab.py
```

### Method 3: Comparative Run with Standard CPython

Run the same dashboard under standard CPython to observe how code executes when no JIT is present:

```bash
python tools/pypy_jit_lab.py
```

---

## CLI Options

| Command                                | Description                                                   |
| :------------------------------------- | :------------------------------------------------------------ |
| `pypy3 tools/pypy_jit_lab.py`          | Interactive terminal menu                                     |
| `pypy3 tools/pypy_jit_lab.py --all`    | Run all experiments non-interactively (full tour)             |
| `pypy3 tools/pypy_jit_lab.py --probe`  | Run the JIT Probe demo on a warm loop                         |
| `pypy3 tools/pypy_jit_lab.py --exp 1`  | Run Experiment 1 (Escape Analysis)                            |
| `pypy3 tools/pypy_jit_lab.py --exp 2`  | Run Experiment 2 (Guards & Bridges)                           |
| `pypy3 tools/pypy_jit_lab.py --exp 3`  | Run Experiment 3 (Optimization Playbook)                      |
| `pypy3 tools/pypy_jit_lab.py --all -v` | Run with `--verbose` to view low-level IR compiler operations |

---

## Laboratory Overview

1. **`jit_probe.py` (Core Inspection Engine)**:
   Programmatically intercepts PyPy's runtime compiler hooks (`set_compile_hook`, `set_abort_hook`) and outputs a Dual-View report (high-level human summary + detailed IR listing).

2. **`lab_escape_analysis.py` (Experiment 1: The Disappearing Allocation)**:
   Demonstrates how PyPy's escape analysis completely eliminates temporary object allocations (e.g. `Point(x, y)`), holding attributes directly in CPU registers without touching the heap.

3. **`lab_guards_and_bridges.py` (Experiment 2: Dynamic Branching & Bridges)**:
   Visualizes how conditional statements (`if/else`) are compiled into native guard instructions, and how flipping conditions triggers the compilation of secondary stitched "bridges".

4. **`lab_jit_playbook.py` (Experiment 3: JIT-Friendly Playbook)**:
   Benchmarks three canonical performance patterns (Type Stability, Call Site Inlining, and Algorithmic Execution), measuring **20x–48x speedups** over CPython 3.11.
