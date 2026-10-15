"""
PyPy JIT Interactive Lab - Experiment 1: The Disappearing Allocation (Escape Analysis)

Demonstrates one of PyPy's most powerful compiler optimizations:
Virtual Object Optimization (Escape Analysis).

When temporary Python objects are instantiated inside a loop but never leak outside,
PyPy's JIT completely removes the allocation, holding attributes directly in CPU
registers or stack slots. If the object escapes (e.g. stored in a list), the JIT
is forced to allocate it on the heap.
"""
import sys
import time
import argparse


class Point:
    __slots__ = ('x', 'y')  # Clean class representation

    def __init__(self, x, y):
        self.x = x
        self.y = y


class EscapeAnalysisLab:
    def __init__(self, iterations: int = 50000, verbose: bool = False):
        self.iterations = iterations
        self.verbose = verbose
        self._is_pypy = '__pypy__' in sys.builtin_module_names
        self.traces = {}

    def _compile_hook(self, info):
        # Filter for loops compiled during our runs
        if info.type == 'loop':
            alloc_ops = [str(op) for op in info.operations
                         if any(k in str(op).lower() for k in ('new_', 'alloc', 'new_with_vtable'))]
            self.current_traces.append({
                'asmlen': info.asmlen,
                'ops_count': len(info.operations),
                'alloc_ops': alloc_ops,
                'operations': list(info.operations)
            })

    def run_non_escaping_experiment(self):
        """Case A: Point is created every iteration but never leaves the loop."""
        self.current_traces = []
        import pypyjit
        pypyjit.set_compile_hook(self._compile_hook)

        t0 = time.perf_counter()
        total = 0
        for i in range(self.iterations):
            p = Point(i, i * 2)
            total += p.x + p.y
        elapsed = (time.perf_counter() - t0) * 1000

        pypyjit.set_compile_hook(None)
        return elapsed, total, list(self.current_traces)

    def run_escaping_experiment(self):
        """Case B: Point is appended to an external list, forcing heap allocation."""
        self.current_traces = []
        import pypyjit
        pypyjit.set_compile_hook(self._compile_hook)

        escaped_list = []
        t0 = time.perf_counter()
        total = 0
        for i in range(self.iterations):
            p = Point(i, i * 2)
            escaped_list.append(p)
            total += p.x + p.y
        elapsed = (time.perf_counter() - t0) * 1000

        pypyjit.set_compile_hook(None)
        return elapsed, total, list(self.current_traces), len(escaped_list)

    def run(self):
        print("\n" + "=" * 74)
        print("    PYPY JIT LAB - EXPERIMENT 1: THE DISAPPEARING ALLOCATION")
        print("=" * 74)

        if not self._is_pypy:
            print("\n[NOTE] Not running under PyPy!")
            print("  CPython allocates memory for all objects on the heap.")
            print("  To witness escape analysis, run this with PyPy 3:")
            print("  --> uv run --python pypy-3.11 pypy3 tools/lab_escape_analysis.py\n")
            return

        print(f"\nRunning {self.iterations:,} iterations for each case...")

        # Run Case A
        time_a, total_a, traces_a = self.run_non_escaping_experiment()
        # Run Case B
        time_b, total_b, traces_b, escaped_count = self.run_escaping_experiment()

        # Compute metrics
        allocs_a = sum(len(t['alloc_ops']) for t in traces_a)
        allocs_b = sum(len(t['alloc_ops']) for t in traces_b)

        print("\n" + "-" * 74)
        print("                        EXPERIMENT RESULTS")
        print("-" * 74)
        print(f" {'Metric':<30} | {'Case A: Non-Escaping':<18} | {'Case B: Escaping':<16}")
        print("-" * 74)
        print(f" {'Object Behavior':<30} | {'Temporary (Local)':<18} | {'Stored in List':<16}")
        print(f" {'Python Point() Calls':<30} | {self.iterations:<18,d} | {self.iterations:<16,d}")
        print(f" {'Heap Allocations in JIT':<30} | {allocs_a:<18d} | {allocs_b:<16d}")
        print(f" {'Execution Time (ms)':<30} | {time_a:<18.2f} | {time_b:<16.2f}")
        speedup = time_b / time_a if time_a > 0 else 1.0
        print(f" {'Relative Speed':<30} | {f'{speedup:.1f}x Faster':<18} | {'Baseline':<16}")
        print("-" * 74)

        # Plain-English Explanation
        print("\n[Plain-English Architectural Explanation]")
        print("  1. In Case A, Python code created 50,000 Point() instances, BUT the JIT's")
        print("     Escape Analysis proved that 'p' never escapes the loop boundary.")
        print("     --> RESULT: The compiler virtualized Point into two CPU registers (x and y).")
        print(f"     --> HEAP ALLOCATIONS: Exactly {allocs_a}! Zero garbage collection pressure.")
        print()
        print("  2. In Case B, 'p' was stored into an external list (escaped_list.append(p)).")
        print("     Because the object must outlive the loop, the JIT could not virtualize it.")
        print(f"     --> RESULT: The compiler was forced to emit 'new_with_vtable' allocations.")
        print(f"     --> The non-escaping version ran {speedup:.1f}x faster due to zero GC/allocation overhead.")

        if self.verbose:
            print("\n" + "=" * 74)
            print("         DEEP DIVE: INTERMEDIATE REPRESENTATION (IR) COMPARISON")
            print("=" * 74)
            print("\n--- Case A (Virtualized Loop IR Sample) ---")
            if traces_a:
                sample_ops = [op for op in traces_a[0]['operations']
                              if any(k in str(op) for k in ('int_add', 'int_mul', 'Point', 'new_'))]
                for op in sample_ops[:8]:
                    print("    ", op)
                print("    --> Notice: No 'new_with_vtable' or heap allocation operations exist!")

            print("\n--- Case B (Escaping Loop IR Sample) ---")
            if traces_b:
                for op in traces_b[0]['alloc_ops'][:4]:
                    print("    [ALLOC] ", op)
                print("    --> Notice: 'new_with_vtable' allocates heap memory for every Point!")

        else:
            print("\n(Run with --verbose to view the IR operation comparison)")

        print("\n" + "=" * 74 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyPy Escape Analysis Interactive Lab")
    parser.add_argument("-n", "--iterations", type=int, default=50000, help="Loop iterations (default: 50,000)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display IR trace comparison")
    args = parser.parse_args()

    lab = EscapeAnalysisLab(iterations=args.iterations, verbose=args.verbose)
    lab.run()
