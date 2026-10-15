"""
PyPy JIT Interactive Lab - Experiment 2: Guards and Bridges

Demonstrates how PyPy's Tracing JIT handles dynamic conditional branching (if/else).

- Guards: A tracing JIT compiles a single linear execution path. When it hits an 'if',
  it compiles the path it saw, inserting a CPU 'guard' instruction (conditional jump).
- Bridges: If the condition flips and fails the guard repeatedly, PyPy traces the
  alternate branch, compiles it into native assembly (a 'Bridge'), and patches the
  guard to jump directly to the bridge!
"""
import sys
import time
import argparse


class GuardsAndBridgesLab:
    def __init__(self, iterations: int = 6000, verbose: bool = False):
        self.iterations = iterations
        self.verbose = verbose
        self._is_pypy = '__pypy__' in sys.builtin_module_names
        self.traces = []

    def _compile_hook(self, info):
        trace_data = {
            'type': info.type,
            'asmlen': info.asmlen,
            'asmaddr': info.asmaddr,
            'ops': list(info.operations),
            'guards': [str(op) for op in info.operations if 'guard' in str(op).lower()]
        }
        self.traces.append(trace_data)

    def run_bifurcated_experiment(self):
        """Loop where the condition is True for the first half, then False for the second."""
        self.traces = []
        import pypyjit
        pypyjit.set_compile_hook(self._compile_hook)

        midpoint = self.iterations // 2
        t0 = time.perf_counter()
        total = 0
        for i in range(self.iterations):
            if i < midpoint:
                total += (i ^ 1)
            else:
                total -= (i ^ 2)
        elapsed = (time.perf_counter() - t0) * 1000

        pypyjit.set_compile_hook(None)
        return elapsed, total, list(self.traces)

    def run(self):
        print("\n" + "=" * 74)
        print("       PYPY JIT LAB - EXPERIMENT 2: GUARDS AND BRIDGES (BRANCHING)")
        print("=" * 74)

        if not self._is_pypy:
            print("\n[NOTE] Not running under PyPy!")
            print("  CPython interprets if/else branches dynamically on every step.")
            print("  To witness guard and bridge compilation, run with PyPy 3:")
            print("  --> uv run --python pypy-3.11 pypy3 tools/lab_guards_and_bridges.py\n")
            return

        print(f"\nRunning conditional loop ({self.iterations:,} iterations)...")
        print("  - Iterations 0 to 2,999:  'if' branch is True (compiles main loop)")
        print("  - Iterations 3,000+:      'if' branch is False (triggers side exit & bridge)")

        elapsed, total, traces = self.run_bifurcated_experiment()

        loops = [t for t in traces if t['type'] == 'loop']
        bridges = [t for t in traces if t['type'] == 'bridge']

        print("\n" + "-" * 74)
        print("                        EXPERIMENT RESULTS")
        print("-" * 74)
        print(f" Total Traces Compiled:      {len(traces)} (Loops: {len(loops)}, Bridges: {len(bridges)})")
        print(f" Execution Wall Time:        {elapsed:.2f} ms")
        if loops:
            print(f" Main Loop Native Assembly:  {loops[0]['asmlen']} bytes ({len(loops[0]['guards'])} guards)")
        if bridges:
            print(f" Stitched Bridge Assembly:   {bridges[0]['asmlen']} bytes ({len(bridges[0]['guards'])} guards)")
        print("-" * 74)

        # Visual ASCII Rail Switch Diagram
        print("\n[Architectural Visual: The JIT Railroad Switch]")
        print("                [Main Loop Trace (Native Machine Code)]")
        print("                          |")
        print("         i < 3000 ? ======> YES --------> [total += (i ^ 1)] ----+ ")
        print("                          |                                      |")
        print("                         [GUARD]                                 |")
        print("                          | (Condition flips!)                   | (Loop Back)")
        print("                          V                                      |")
        print("               [Stitched Bridge Trace]                           |")
        print("                     (Native Code)                               |")
        print("                          |                                      |")
        print("                          +-------------> [total -= (i ^ 2)] ----+")

        # Plain-English Explanation
        print("\n[Plain-English Architectural Explanation]")
        print("  1. The JIT first assumed 'i < 3000' would always be True. It compiled the")
        print("     hot loop into native machine code and planted a CPU 'guard' instruction.")
        print()
        print("  2. When iteration 3,000 arrived, the guard failed repeatedly. Instead of")
        print("     giving up and de-optimizing back to the slow interpreter forever, the JIT")
        print(f"     recorded a secondary trace for the 'else' branch ({bridges[0]['asmlen'] if bridges else 0} bytes).")
        print()
        print("  3. It then 'hot-patched' the failed guard to jump directly into the new")
        print("     Bridge assembly! Now BOTH branches execute at raw native CPU speed.")

        if self.verbose:
            print("\n" + "=" * 74)
            print("              DEEP DIVE: INTERMEDIATE REPRESENTATION DIFF")
            print("=" * 74)
            if loops:
                print("\n--- Main Loop Key Guard ---")
                for g in loops[0]['guards'][:4]:
                    print("    [LOOP GUARD]   ", g)
            if bridges:
                print("\n--- Stitched Bridge Key Guard ---")
                for g in bridges[0]['guards'][:4]:
                    print("    [BRIDGE GUARD] ", g)
        else:
            print("\n(Run with --verbose to view the IR operation listings for Loop and Bridge)")

        print("\n" + "=" * 74 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyPy Guards and Bridges Lab")
    parser.add_argument("-n", "--iterations", type=int, default=6000, help="Loop iterations (default: 6,000)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display IR operation listings")
    args = parser.parse_args()

    lab = GuardsAndBridgesLab(iterations=args.iterations, verbose=args.verbose)
    lab.run()
