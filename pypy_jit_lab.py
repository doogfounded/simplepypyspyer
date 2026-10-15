"""
PyPy JIT Interactive Laboratory - Master CLI Launcher

An all-in-one terminal dashboard to explore, benchmark, and inspect PyPy's
adaptive Tracing JIT compiler in real-time.

Features:
- Probe: Real-time inspection of JIT compilation hooks, IR operations, and native bytes.
- Experiment 1 (Escape Analysis): Watch temporary objects vanish into CPU registers.
- Experiment 2 (Guards & Bridges): Understand how the JIT stitches alternate branches.
- Experiment 3 (Optimization Playbook): Compare JIT-friendly vs hostile patterns (20x-30x speedups).
"""
import sys
import os
import argparse

# Ensure tools/ is on sys.path so sibling imports succeed
tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from jit_probe import JitProbe, demo_workload
from lab_escape_analysis import EscapeAnalysisLab
from lab_guards_and_bridges import GuardsAndBridgesLab
from lab_jit_playbook import PlaybookLab


def print_banner():
    is_pypy = '__pypy__' in sys.builtin_module_names
    runtime_str = "PyPy 3 (JIT Active)" if is_pypy else "CPython 3 (Bytecode Interpreter)"

    print("\n" + "=" * 74)
    print("               WELCOME TO THE PYPY JIT INTERACTIVE LAB")
    print("=" * 74)
    print(f" Current Runtime: {runtime_str}")
    if not is_pypy:
        print(" [!] For full JIT compilation & assembly metrics, launch via PyPy:")
        print("     uv run --python pypy-3.11 pypy3 tools/pypy_jit_lab.py")
    print("=" * 74)


def run_probe_demo(verbose: bool = False):
    print("\n>>> Launching: JIT Probe Demo (Canonical Arithmetic Loop)...")
    probe = JitProbe(verbose=verbose)
    with probe:
        demo_workload()
    probe.print_report()


def run_experiment_1(verbose: bool = False):
    print("\n>>> Launching: Experiment 1 - Escape Analysis & Virtual Objects...")
    lab = EscapeAnalysisLab(iterations=50000, verbose=verbose)
    lab.run()


def run_experiment_2(verbose: bool = False):
    print("\n>>> Launching: Experiment 2 - Guards & Stitched Bridges...")
    lab = GuardsAndBridgesLab(iterations=6000, verbose=verbose)
    lab.run()


def run_experiment_3(verbose: bool = False):
    print("\n>>> Launching: Experiment 3 - JIT-Friendly vs JIT-Hostile Playbook...")
    lab = PlaybookLab(verbose=verbose)
    lab.run()


def run_all(verbose: bool = False):
    run_probe_demo(verbose)
    run_experiment_1(verbose)
    run_experiment_2(verbose)
    run_experiment_3(verbose)


def interactive_menu(verbose: bool = False):
    while True:
        print_banner()
        print("\nSelect an Experiment to Run:")
        print("  [1] JIT Probe Demo (Dual-View Loop Compilation & Guards)")
        print("  [2] Experiment 1: The Disappearing Allocation (Escape Analysis)")
        print("  [3] Experiment 2: Dynamic Branching, Guards & Bridges")
        print("  [4] Experiment 3: JIT-Friendly vs JIT-Hostile Playbook (Speedups)")
        print("  [5] Run All Experiments Sequentially (Full Guided Tour)")
        print("  [0] Exit")
        print("-" * 74)

        try:
            choice = input("Enter choice [0-5]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting lab. Goodbye!")
            break

        if choice == '1':
            run_probe_demo(verbose)
        elif choice == '2':
            run_experiment_1(verbose)
        elif choice == '3':
            run_experiment_2(verbose)
        elif choice == '4':
            run_experiment_3(verbose)
        elif choice == '5':
            run_all(verbose)
        elif choice == '0':
            print("\nExiting lab. Goodbye!")
            break
        else:
            print(f"\n[!] Invalid option '{choice}'. Please select 0 to 5.")

        input("\nPress Enter to return to the main menu...")


def main():
    parser = argparse.ArgumentParser(description="PyPy Tracing JIT Interactive Lab Dashboard")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display full IR operation listings")
    parser.add_argument("--all", action="store_true", help="Run all experiments non-interactively")
    parser.add_argument("--exp", type=int, choices=[1, 2, 3], help="Run a specific experiment (1, 2, or 3)")
    parser.add_argument("--probe", action="store_true", help="Run the JIT probe demo")
    args = parser.parse_args()

    if args.all:
        print_banner()
        run_all(verbose=args.verbose)
    elif args.probe:
        print_banner()
        run_probe_demo(verbose=args.verbose)
    elif args.exp == 1:
        print_banner()
        run_experiment_1(verbose=args.verbose)
    elif args.exp == 2:
        print_banner()
        run_experiment_2(verbose=args.verbose)
    elif args.exp == 3:
        print_banner()
        run_experiment_3(verbose=args.verbose)
    else:
        interactive_menu(verbose=args.verbose)


if __name__ == "__main__":
    main()
