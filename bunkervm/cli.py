"""
BunkerVM CLI — Developer-friendly command-line interface.

Commands:
    bunkervm demo                   # See BunkerVM in action (10 seconds)
    bunkervm run script.py          # Run a script inside a sandbox
    bunkervm run -c "print(42)"     # Run inline code
    bunkervm server                 # Start MCP server (existing behavior)
    bunkervm info                   # Show system info and readiness
    bunkervm vscode-setup           # Set up VS Code MCP integration
    bunkervm enable-network         # One-time: enable VM networking without sudo

Usage:
    pip install bunkervm
    bunkervm demo
"""

from __future__ import annotations

import argparse
import os
import sys
import time

# ANSI colors for terminal output
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_PURPLE = "\033[35m"
_RESET = "\033[0m"
_CHECK = f"{_GREEN}✓{_RESET}"
_CROSS = f"{_RED}✗{_RESET}"
_ARROW = f"{_CYAN}→{_RESET}"

# Disable colors if not a TTY
if not sys.stderr.isatty():
    _BOLD = _DIM = _GREEN = _CYAN = _YELLOW = _RED = _PURPLE = _RESET = ""
    _CHECK = "✓"
    _CROSS = "✗"
    _ARROW = "→"


def _print(msg: str = "", end: str = "\n") -> None:
    """Print to stderr (stdout reserved for output)."""
    print(msg, file=sys.stderr, end=end, flush=True)


# ── Demo Command ──


_DEMO_SCRIPT = '''\
import math, time

print("=" * 50)
print("  BunkerVM — Hardware-Isolated Sandbox Demo")
print("=" * 50)
print()

# 1. Prove we're inside a real VM
import platform
print(f"OS:       {platform.platform()}")
print(f"Hostname: {platform.node()}")
print(f"Python:   {platform.python_version()}")
print()

# 2. Compute primes (real work inside the sandbox)
def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(math.sqrt(n)) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    return [x for x in range(n + 1) if is_prime[x]]

primes = sieve(100)
print(f"Prime numbers under 100:")
print(" ".join(str(p) for p in primes))
print(f"\\nFound {len(primes)} primes")
print()

# 3. File system access (sandboxed)
with open("/tmp/demo.txt", "w") as f:
    f.write("Hello from BunkerVM!")
with open("/tmp/demo.txt") as f:
    print(f"File I/O test: {f.read()}")
print()

# 4. Show isolation
print(f"Process ID:  {__import__('os').getpid()}")
print(f"User:        {__import__('os').getenv('USER', 'root')}")
print(f"Working dir: {__import__('os').getcwd()}")
print()
print("✓ Code ran safely inside a Firecracker microVM")
print("✓ Full Linux environment (not a container)")
print("✓ Hardware-level isolation via KVM")
print("✓ VM will be destroyed after this demo")
'''


def cmd_demo(args: argparse.Namespace) -> int:
    """Run the BunkerVM demo — shows the product in 10 seconds."""
    from .runtime import run_code

    _print()
    _print(f"{_BOLD}{_PURPLE}  ╔══════════════════════════════════════╗{_RESET}")
    _print(f"{_BOLD}{_PURPLE}  ║         BunkerVM Demo                ║{_RESET}")
    _print(f"{_BOLD}{_PURPLE}  ║  Hardware-isolated AI sandbox        ║{_RESET}")
    _print(f"{_BOLD}{_PURPLE}  ╚══════════════════════════════════════╝{_RESET}")
    _print()

    t0 = time.time()

    try:
        output = run_code(
            _DEMO_SCRIPT,
            cpus=1,
            memory=512,
            quiet=False,
        )
        _print()
        # Print output to stdout (so it can be captured/piped)
        print(output)
        _print()

        elapsed = time.time() - t0
        _print(f"{_CHECK} Demo completed in {elapsed:.1f}s")
        _print()
        _print(f"{_DIM}Learn more:{_RESET}")
        _print(f"  {_ARROW} Run your own code:  {_CYAN}bunkervm run script.py{_RESET}")
        _print(f"  {_ARROW} Python API:          {_CYAN}from bunkervm import run_code{_RESET}")
        _print(f"  {_ARROW} AI agent wrapper:    {_CYAN}from bunkervm import secure_agent{_RESET}")
        _print()
        return 0

    except Exception as e:
        _print(f"\n{_CROSS} Demo failed: {e}")
        return 1


# ── Run Command ──


def cmd_run(args: argparse.Namespace) -> int:
    """Run a script or inline code inside a BunkerVM sandbox."""
    from .runtime import run_code

    # Get code to run
    if args.code:
        code = args.code
        language = args.language or "python"
    elif args.file:
        if not os.path.exists(args.file):
            _print(f"{_CROSS} File not found: {args.file}")
            return 1
        with open(args.file, "r") as f:
            code = f.read()
        # Detect language from extension
        ext = os.path.splitext(args.file)[1].lower()
        language = args.language or {
            ".py": "python",
            ".sh": "bash",
            ".bash": "bash",
            ".js": "node",
        }.get(ext, "python")
    else:
        _print(f"{_CROSS} Provide a file or use -c for inline code")
        _print(f"  Usage: bunkervm run script.py")
        _print(f"  Usage: bunkervm run -c \"print('hello')\"")
        return 1

    try:
        output = run_code(
            code,
            language=language,
            timeout=args.timeout,
            cpus=args.cpus,
            memory=args.memory,
            network=not args.no_network,
            quiet=args.quiet,
        )
        print(output)
        return 0
    except RuntimeError as e:
        _print(f"\n{_CROSS} {e}")
        return 1
    except KeyboardInterrupt:
        _print(f"\n{_YELLOW}Interrupted{_RESET}")
        return 130


# ── Info Command ──


def cmd_info(args: argparse.Namespace) -> int:
    """Show BunkerVM system info and readiness."""
    import platform

    _print(f"\n{_BOLD}BunkerVM System Check{_RESET}\n")

    # Version
    from . import __version__
    _print(f"  Version:    {_CYAN}{__version__}{_RESET}")
    _print(f"  Platform:   {platform.platform()}")
    _print(f"  Python:     {platform.python_version()}")

    # Architecture
    arch = platform.machine()
    if arch in ("x86_64", "amd64", "AMD64"):
        _print(f"  Arch:       {_CHECK} {arch}")
    else:
        _print(f"  Arch:       {_CROSS} {arch} (x86_64 required)")

    # Linux / KVM
    if sys.platform == "linux":
        _print(f"  Linux:      {_CHECK}")
        if os.path.exists("/dev/kvm"):
            _print(f"  KVM:        {_CHECK} /dev/kvm available")
            # Check permissions
            if os.access("/dev/kvm", os.R_OK | os.W_OK):
                _print(f"  KVM access: {_CHECK} readable & writable")
            else:
                _print(f"  KVM access: {_CROSS} permission denied (try: sudo chmod 666 /dev/kvm)")
        else:
            _print(f"  KVM:        {_CROSS} /dev/kvm not found")
            _print(f"              WSL2: Add nestedVirtualization=true to .wslconfig")
    else:
        _print(f"  Linux:      {_YELLOW}! Not on Linux (use WSL2 on Windows){_RESET}")

    # Bundle
    _print()
    from .bootstrap import BUNDLE_DIR, REQUIRED_FILES
    bundle_ok = True
    for name, filename in REQUIRED_FILES.items():
        path = BUNDLE_DIR / filename
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            _print(f"  {name:14s} {_CHECK} {path} ({size_mb:.1f} MB)")
        else:
            _print(f"  {name:14s} {_CROSS} not found")
            bundle_ok = False

    if not bundle_ok:
        _print(f"\n  {_YELLOW}Run 'bunkervm demo' to auto-download the bundle.{_RESET}")

    # Firecracker check
    _print()
    import shutil
    fc = shutil.which("firecracker")
    if fc:
        _print(f"  Firecracker: {_CHECK} {fc}")
    elif (BUNDLE_DIR / "firecracker").exists():
        _print(f"  Firecracker: {_CHECK} {BUNDLE_DIR / 'firecracker'}")
    else:
        _print(f"  Firecracker: {_CROSS} not found")

    _print()
    return 0


# ── VS Code Setup Command ──


_SUDOERS_FILE = "/etc/sudoers.d/bunkervm"


def _is_network_enabled() -> bool:
    """Check if passwordless sudo for networking commands is configured."""
    if sys.platform == "win32":
        # On Windows, check via WSL
        import subprocess
        try:
            result = subprocess.run(
                ["wsl", "-d", "Ubuntu", "--", "sudo", "-n", "ip", "link", "show"],
                capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
    else:
        try:
            import subprocess
            result = subprocess.run(
                ["sudo", "-n", "ip", "link", "show"],
                capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False


def cmd_vscode_setup(args: argparse.Namespace) -> int:
    """Generate .vscode/mcp.json for VS Code MCP integration."""
    import json
    import platform
    import shutil

    workspace = os.getcwd()
    vscode_dir = os.path.join(workspace, ".vscode")
    mcp_path = os.path.join(vscode_dir, "mcp.json")

    _print(f"\n{_BOLD}BunkerVM — VS Code MCP Setup{_RESET}\n")

    # Detect environment
    is_wsl = "microsoft" in platform.uname().release.lower()
    is_windows = sys.platform == "win32"
    python_bin = shutil.which("python3") or shutil.which("python") or "python3"

    if is_windows:
        # Running from Windows — need WSL wrapper
        config = {
            "servers": {
                "bunkervm": {
                    "command": "wsl",
                    "args": ["-d", "Ubuntu", "--", "python3", "-m", "bunkervm", "--no-network"]
                }
            }
        }
        _print(f"  Platform:  {_CYAN}Windows (using WSL2){_RESET}")
    else:
        # Linux or WSL directly
        config = {
            "servers": {
                "bunkervm": {
                    "command": python_bin,
                    "args": ["-m", "bunkervm", "--no-network"]
                }
            }
        }
        _print(f"  Platform:  {_CYAN}Linux{_RESET}")

    # Check if file already exists
    if os.path.exists(mcp_path):
        try:
            with open(mcp_path, "r") as f:
                existing = json.load(f)
            if "servers" in existing and "bunkervm" in existing.get("servers", {}):
                _print(f"  {_CHECK} BunkerVM already configured in {mcp_path}")
                _print(f"\n  {_DIM}To reconfigure, delete .vscode/mcp.json and run again.{_RESET}\n")
                return 0
            # Merge into existing config
            existing.setdefault("servers", {})
            existing["servers"]["bunkervm"] = config["servers"]["bunkervm"]
            config = existing
            _print(f"  {_ARROW} Merging into existing mcp.json")
        except (json.JSONDecodeError, OSError):
            _print(f"  {_YELLOW}! Existing mcp.json is invalid, overwriting{_RESET}")

    # Create .vscode/ if needed
    os.makedirs(vscode_dir, exist_ok=True)

    # Write config
    with open(mcp_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    _print(f"  {_CHECK} Created {mcp_path}")
    _print()
    _print(f"  {_BOLD}What's next:{_RESET}")
    _print(f"  1. Open this folder in VS Code")
    _print(f"  2. Open Copilot Chat (Ctrl+Shift+I)")
    _print(f"  3. Ask: {_CYAN}\"Run this Python script in the sandbox\"{_RESET}")
    _print(f"  4. Copilot will use BunkerVM's 8 sandboxed tools automatically")
    _print()
    _print(f"  {_DIM}Tools: sandbox_exec, sandbox_write_file, sandbox_read_file,{_RESET}")
    _print(f"  {_DIM}       sandbox_list_dir, sandbox_upload_file, sandbox_download_file,{_RESET}")
    _print(f"  {_DIM}       sandbox_status, sandbox_reset{_RESET}")
    _print()
    return 0


# ── Enable Network Command ──


def cmd_enable_network(args: argparse.Namespace) -> int:
    """Configure passwordless sudo for VM networking (one-time setup)."""
    import subprocess
    import getpass

    _print(f"\n{_BOLD}BunkerVM \u2014 Enable VM Networking{_RESET}\n")

    if sys.platform == "win32":
        _print(f"  {_YELLOW}! This command must be run inside WSL, not Windows.{_RESET}")
        _print(f"  Run: {_CYAN}wsl -d Ubuntu -- sudo bunkervm enable-network{_RESET}\n")
        return 1

    # Must be run as root
    if os.geteuid() != 0:
        _print(f"  {_CROSS} This command requires sudo.")
        _print(f"  Run: {_CYAN}sudo bunkervm enable-network{_RESET}\n")
        return 1

    # Get the actual user (not root)
    user = os.environ.get("SUDO_USER", getpass.getuser())

    # Check if already configured
    if os.path.exists(_SUDOERS_FILE):
        _print(f"  {_CHECK} Already configured: {_SUDOERS_FILE}")
        _print(f"  {_DIM}To reset, delete {_SUDOERS_FILE} and run again.{_RESET}\n")
        return 0

    # Find actual paths for ip, sysctl, iptables
    import shutil
    ip_bin = shutil.which("ip") or "/usr/sbin/ip"
    sysctl_bin = shutil.which("sysctl") or "/usr/sbin/sysctl"
    iptables_bin = shutil.which("iptables") or "/usr/sbin/iptables"

    sudoers_content = (
        f"# BunkerVM: allow passwordless networking for VM setup\n"
        f"# Created by: bunkervm enable-network\n"
        f"# Safe to remove: sudo rm {_SUDOERS_FILE}\n"
        f"{user} ALL=(ALL) NOPASSWD: {ip_bin}\n"
        f"{user} ALL=(ALL) NOPASSWD: {sysctl_bin}\n"
        f"{user} ALL=(ALL) NOPASSWD: {iptables_bin}\n"
    )

    # Write sudoers file
    try:
        with open(_SUDOERS_FILE, "w") as f:
            f.write(sudoers_content)
        os.chmod(_SUDOERS_FILE, 0o440)

        # Validate with visudo
        result = subprocess.run(
            ["visudo", "-c", "-f", _SUDOERS_FILE],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            os.remove(_SUDOERS_FILE)
            _print(f"  {_CROSS} Sudoers validation failed: {result.stderr.strip()}")
            return 1

    except OSError as e:
        _print(f"  {_CROSS} Failed to write {_SUDOERS_FILE}: {e}")
        return 1

    _print(f"  {_CHECK} Created {_SUDOERS_FILE}")
    _print(f"  {_CHECK} User '{user}' can now create VM networks without a password")
    _print()
    _print(f"  {_BOLD}Granted passwordless sudo for:{_RESET}")
    _print(f"    {_DIM}{ip_bin}{_RESET}       (TAP device setup)")
    _print(f"    {_DIM}{sysctl_bin}{_RESET}   (IP forwarding)")
    _print(f"    {_DIM}{iptables_bin}{_RESET} (NAT rules)")
    _print()
    _print(f"  {_BOLD}Next:{_RESET} Re-run {_CYAN}bunkervm vscode-setup{_RESET} to update VS Code config,")
    _print(f"        or restart the MCP server in VS Code.")
    _print()
    _print(f"  {_DIM}To undo: sudo rm {_SUDOERS_FILE}{_RESET}")
    _print()
    return 0


# ── Main CLI Parser ──


def main() -> int:
    """BunkerVM CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="bunkervm",
        description="BunkerVM — Hardware-isolated sandbox for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  bunkervm demo                        See it in action
  bunkervm run script.py               Run a script safely
  bunkervm run -c "print(42)"          Run inline code
  bunkervm server --transport sse      Start MCP server
  bunkervm info                        Check system readiness
  bunkervm vscode-setup                Set up VS Code MCP integration
  bunkervm enable-network              Enable VM networking (one-time, needs sudo)
""",
    )
    sub = parser.add_subparsers(dest="command")

    # ── demo ──
    demo_p = sub.add_parser("demo", help="See BunkerVM in action (10 seconds)")
    demo_p.set_defaults(func=cmd_demo)

    # ── run ──
    run_p = sub.add_parser("run", help="Run code inside a sandbox")
    run_p.add_argument("file", nargs="?", help="Script file to execute")
    run_p.add_argument("-c", "--code", help="Inline code to execute")
    run_p.add_argument("-l", "--language", choices=["python", "bash", "node"],
                       help="Language (auto-detected from extension)")
    run_p.add_argument("-t", "--timeout", type=int, default=30,
                       help="Execution timeout in seconds (default: 30)")
    run_p.add_argument("--cpus", type=int, default=1, help="vCPUs (default: 1)")
    run_p.add_argument("--memory", type=int, default=512, help="Memory in MB (default: 512)")
    run_p.add_argument("--no-network", action="store_true", help="Disable internet in VM")
    run_p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages")
    run_p.set_defaults(func=cmd_run)

    # ── server ──
    server_p = sub.add_parser("server", help="Start MCP server (full mode)")
    server_p.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    server_p.add_argument("--port", type=int, default=3000)
    server_p.add_argument("--config", default=None)
    server_p.add_argument("--no-network", action="store_true")
    server_p.add_argument("--skip-vm", action="store_true")
    server_p.add_argument("--cpus", type=int, default=None)
    server_p.add_argument("--memory", type=int, default=None)
    server_p.add_argument("--dashboard", action="store_true")
    server_p.add_argument("--dashboard-port", type=int, default=None)
    server_p.add_argument("-v", "--verbose", action="store_true")
    server_p.set_defaults(func=cmd_server)

    # ── info ──
    info_p = sub.add_parser("info", help="Show system info and readiness")
    info_p.set_defaults(func=cmd_info)

    # ── vscode-setup ──
    vs_p = sub.add_parser("vscode-setup", help="Set up VS Code MCP integration")
    vs_p.set_defaults(func=cmd_vscode_setup)

    # ── enable-network ──
    net_p = sub.add_parser("enable-network", help="Enable VM networking without sudo (one-time)")
    net_p.set_defaults(func=cmd_enable_network)

    args = parser.parse_args()

    if not args.command:
        # No subcommand — check if legacy __main__.py args are being used
        # For backward compat: `bunkervm --transport sse` still works
        if len(sys.argv) > 1 and sys.argv[1].startswith("--"):
            # Legacy mode — delegate to __main__.main()
            from .__main__ import main as legacy_main
            legacy_main()
            return 0
        parser.print_help()
        _print()
        _print(f"  {_ARROW} Quick start: {_CYAN}bunkervm demo{_RESET}")
        _print()
        return 0

    return args.func(args)


def cmd_server(args: argparse.Namespace) -> int:
    """Start the MCP server (delegates to existing __main__)."""
    # Reconstruct sys.argv for the legacy parser
    new_argv = ["bunkervm"]
    new_argv.extend(["--transport", args.transport])
    if args.port != 3000:
        new_argv.extend(["--port", str(args.port)])
    if args.config:
        new_argv.extend(["--config", args.config])
    if args.no_network:
        new_argv.append("--no-network")
    if args.skip_vm:
        new_argv.append("--skip-vm")
    if args.cpus:
        new_argv.extend(["--cpus", str(args.cpus)])
    if args.memory:
        new_argv.extend(["--memory", str(args.memory)])
    if args.dashboard:
        new_argv.append("--dashboard")
    if args.dashboard_port:
        new_argv.extend(["--dashboard-port", str(args.dashboard_port)])
    if args.verbose:
        new_argv.append("--verbose")

    sys.argv = new_argv

    from .__main__ import main as legacy_main
    legacy_main()
    return 0
