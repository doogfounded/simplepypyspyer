"""
PyPy JIT Probe - Dual-View Inspection Prototype (Step 1)

Provides an accessible yet in-depth view into PyPy's Tracing JIT compiler.
- View 1 (Summary): Plain-English breakdown of compiled loops, native code footprint,
  and guard checks.
- View 2 (Deep Dive): Line-by-line inspection of IR operations, categorizing guards,
  arithmetic, and memory accesses.
"""
import sys
import time
import argparse
from typing import List, Dict, Any


class CompiledTrace:
    """Represents a compiled JIT loop or bridge with analytical breakdown."""
    def __init__(self, info):
        self.trace_type = getattr(info, 'type', 'unknown')
        self.loop_no = getattr(info, 'loop_no', None) if self.trace_type == 'loop' else None
        self.bridge_no = getattr(info, 'bridge_no', None) if self.trace_type == 'bridge' else None
        self.asmlen = getattr(info, 'asmlen', 0)
        self.asmaddr = getattr(info, 'asmaddr', 0)
        self.raw_ops = list(getattr(info, 'operations', []))
        
        # Categorize operations
        self.guards = []
        self.math_ops = []
        self.mem_ops = []
        self.control_ops = []
        self.other_ops = []
        
        for op in self.raw_ops:
            op_str = str(op)
            name = op_str.split('(')[0].split('=')[-1].strip()
            if 'guard' in name.lower():
                self.guards.append(op_str)
            elif any(k in name.lower() for k in ('int_', 'float_', 'bool_', 'and', 'or', 'xor')):
                self.math_ops.append(op_str)
            elif any(k in name.lower() for k in ('field', 'array', 'gc', 'alloc', 'raw')):
                self.mem_ops.append(op_str)
            elif any(k in name.lower() for k in ('jump', 'label', 'finish')):
                self.control_ops.append(op_str)
            else:
                self.other_ops.append(op_str)


class JitProbe:
    """Context manager to intercept and inspect JIT compilation events."""
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.traces: List[CompiledTrace] = []
        self.aborts: List[str] = []
        self._is_pypy = '__pypy__' in sys.builtin_module_names

    def _compile_hook(self, info):
        try:
            self.traces.append(CompiledTrace(info))
        except Exception as e:
            print(f"[JitProbe Internal Error] {e}", file=sys.stderr)

    def _abort_hook(self, jitdriver_name, greenkey, reason):
        self.aborts.append(f"Trace aborted ({jitdriver_name}): {reason}")

    def __enter__(self):
        if not self._is_pypy:
            return self
        import pypyjit
        pypyjit.set_compile_hook(self._compile_hook)
        pypyjit.set_abort_hook(self._abort_hook)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._is_pypy:
            return
        import pypyjit
        pypyjit.set_compile_hook(None)
        pypyjit.set_abort_hook(None)

    def print_report(self):
        """Prints the Dual-View CLI inspection report."""
        print("\n" + "=" * 70)
        print("          PYPY TRACING JIT - DUAL-VIEW INSPECTION REPORT")
        print("=" * 70)

        if not self._is_pypy:
            print("\n[NOTE] Not running under PyPy!")
            print("  CPython executes code using a standard bytecode interpreter.")
            print("  To observe JIT compilation, run this script using PyPy 3:")
            print("  --> uv run --python pypy-3.11 pypy3 tools/jit_probe.py\n")
            return

        if not self.traces:
            print("\n[INFO] No loops were JIT-compiled during this run.")
            print("  Tip: PyPy's JIT compiles loops after ~1,039 iterations by default.")
            return

        print(f"\n[+] Total Compiled Traces: {len(self.traces)}")
        if self.aborts:
            print(f"[!] Trace Aborts Encountered: {len(self.aborts)}")
            for abort in self.aborts:
                print(f"    - {abort}")

        for idx, trace in enumerate(self.traces, 1):
            trace_id = f"Loop #{trace.loop_no}" if trace.trace_type == 'loop' else f"Bridge #{trace.bridge_no}"
            print("\n" + "-" * 70)
            print(f" Trace #{idx}: [{trace.trace_type.upper()}] ({trace_id})")
            print("-" * 70)

            # View 1: High-Level Accessible Summary
            print(f"  * Native Machine Code: {trace.asmlen} bytes at address 0x{trace.asmaddr:x}")
            print(f"  * Total IR Operations: {len(trace.raw_ops)}")
            print(f"    - Compute & Arithmetic: {len(trace.math_ops)} ops")
            print(f"    - Memory & GC Access:   {len(trace.mem_ops)} ops")
            print(f"    - Safety Guards Placed: {len(trace.guards)} guards")

            # Accessible Explanation
            print("\n  [Plain-English Explanation]")
            if trace.guards:
                print(f"    The JIT placed {len(trace.guards)} guard check(s). These are lightweight")
                print("    CPU checks ensuring variable types and loop conditions don't change.")
                print("    As long as guards pass, execution stays in blazing-fast native assembly.")
            else:
                print("    No guards were needed. This code executes as uninterrupted assembly!")

            if trace.math_ops:
                print(f"    {len(trace.math_ops)} operation(s) represent pure CPU arithmetic that")
                print("    run in native hardware registers without Python object boxing.")

            # View 2: Deep Dive IR Breakdown
            if self.verbose:
                print("\n  [Deep Dive: Intermediate Representation (IR) Operations]")
                for op_idx, op in enumerate(trace.raw_ops, 1):
                    prefix = "    "
                    if 'guard' in str(op).lower():
                        prefix = "  [GUARD] "
                    elif any(k in str(op).lower() for k in ('field', 'gc', 'alloc')):
                        prefix = "  [MEM]   "
                    print(f"  {op_idx:3d}: {prefix}{op}")
            else:
                print("\n  (Run with --verbose to view all individual IR operations)")

        print("\n" + "=" * 70 + "\n")


def demo_workload():
    """Canonical warm loop designed to trigger PyPy's JIT threshold."""
    print("Executing benchmark workload (2,500 iterations)...")
    t0 = time.perf_counter()
    total = 0
    for i in range(2500):
        total += (i * 3) ^ (i >> 2)
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"Completed in {elapsed:.3f} ms. Result = {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyPy Tracing JIT Dual-View Probe")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display full IR operation listings")
    args = parser.parse_args()

    probe = JitProbe(verbose=args.verbose)
    with probe:
        demo_workload()

    probe.print_report()
