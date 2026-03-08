# BunkerVM

Run AI agent code inside a Firecracker microVM instead of your host machine.

> Give your AI agent a computer. Isolated. Instant. Self-hosted.

BunkerVM is a tiny operating system that boots in **under 6 seconds** and gives AI agents a safe, isolated Linux machine to work in. Install it with one command. No Docker. No cloud. No config files.

---

## See it in action

```
$ pip install bunkervm[langgraph]
Successfully installed bunkervm-0.2.5

$ sudo python3 -m bunkervm &
⚡ Downloading BunkerVM bundle (first run)... done (98MB)
⚡ Booting Firecracker MicroVM...
✓ VM ready in 5.2s — KVM hardware isolation active
✓ MCP server ready (transport: stdio)
```

```python
# 5 lines — that's the entire integration
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from bunkervm.langchain import BunkerVMToolkit

agent = create_react_agent(ChatOpenAI(model="gpt-4o"), BunkerVMToolkit().get_tools())
result = agent.invoke({"messages": [("human", "Write and run a Python script that finds primes under 50")]})
```

```
→ write_file: /tmp/primes.py
← wrote 312 bytes

→ run_command: python3 /tmp/primes.py
← 2 3 5 7 11 13 17 19 23 29 31 37 41 43 47

🤖 The prime numbers under 50 are: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47.
```

```
           HOST                    VM (Firecracker)
Hostname:  ashish-PC               localhost
Kernel:    5.15.167.4-microsoft    5.10.225
OS:        Ubuntu (WSL2)           Alpine Linux v3.21
```

**Everything the agent did ran inside the VM. Your host was never touched.**

---

## Install

```bash
pip install bunkervm
```

## Use with Claude Desktop

Add this to your Claude Desktop config:

**Windows (WSL2):**
```json
{
  "mcpServers": {
    "bunkervm": {
      "command": "wsl",
      "args": ["-d", "Ubuntu", "--", "sudo", "python3", "-m", "bunkervm"]
    }
  }
}
```

**Linux / macOS:**
```json
{
  "mcpServers": {
    "bunkervm": {
      "command": "sudo",
      "args": ["python3", "-m", "bunkervm"]
    }
  }
}
```

That's it. On first run, BunkerVM downloads a ~100MB pre-built micro-OS. After that, every launch boots a fresh VM in ~5 seconds.

## Use with LangGraph / LangChain

```bash
pip install bunkervm[langgraph]
```

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from bunkervm.langchain import BunkerVMToolkit

toolkit = BunkerVMToolkit()  # connects to running VM
agent = create_react_agent(ChatOpenAI(model="gpt-4o"), toolkit.get_tools())

result = agent.invoke({
    "messages": [("human", "Write a script that calculates fibonacci numbers, run it")]
})
```

The toolkit gives your agent four tools: `run_command`, `write_file`, `read_file`, `list_directory`. All calls are logged with `→` / `←` arrows so you can see exactly what the agent does.

## What can it do?

Once connected, your AI agent gets these tools:

| Tool | What it does |
|---|---|
| `sandbox_exec` | Run any shell command |
| `sandbox_write_file` | Create or edit files |
| `sandbox_read_file` | Read files |
| `sandbox_list_dir` | Browse directories |
| `sandbox_status` | Check VM health, CPU, RAM, disk |
| `sandbox_reset` | Wipe everything, start fresh |

**Example:** Ask Claude to *"write a Python script that fetches the top 10 Hacker News stories, then run it"* — it writes the code inside the VM, executes it, and shows you the results. All isolated.

## Why not Docker?

| | BunkerVM | Docker |
|---|---|---|
| Isolation | **Hardware (KVM)** — separate kernel | Shared kernel |
| Escape risk | Near zero | Container escapes exist |
| Boot time | ~5s | ~0.5s |
| Self-hosted | Yes | Yes |
| Internet access | Optional | Yes |
| Setup | `pip install` | Dockerfile + build + run |

BunkerVM runs each agent in a real virtual machine. If the agent goes rogue, it can't touch your host.

## Requirements

- **Linux** with KVM support, or **Windows** with WSL2
- Python 3.10+
- ~100MB disk for the micro-OS bundle

For WSL2, enable nested virtualization in `%USERPROFILE%\.wslconfig`:
```ini
[wsl2]
nestedVirtualization=true
```

## Works with any MCP client

BunkerVM speaks the [Model Context Protocol](https://modelcontextprotocol.io). It works with:
- Claude Desktop
- LangGraph / LangChain
- Any MCP-compatible agent framework

```bash
pip install bunkervm[langgraph]
```

See [examples/test_agent.py](examples/test_agent.py) for a working 5-line agent example.

## How it works (you don't need to know this)

<details>
<summary>Under the hood</summary>

BunkerVM is a custom Alpine Linux micro-OS (~256MB) purpose-built for AI agent sandboxing:

```
Your AI  ──MCP──▶  bunkervm       ──vsock──▶  Firecracker MicroVM
                   (host)                      ┌──────────────┐
                                               │ Alpine Linux │
                                               │ Python 3     │
                                               │ gcc, git,    │
                                               │ curl, etc.   │
                                               │              │
                                               │ exec_agent   │
                                               └──────────────┘
```

- **Firecracker** — Amazon's micro-VM engine (same tech as AWS Lambda)
- **vsock** — Direct host↔VM communication, no networking needed
- **TAP networking** — Optional, gives the VM internet access
- **exec_agent** — HTTP server inside the VM that executes commands

The pre-built bundle (~100MB) includes Firecracker, a Linux kernel, and the rootfs. Downloaded once on first run to `~/.bunkervm/bundle/`.

</details>

## For contributors

<details>
<summary>Building from source</summary>

```bash
# Clone
git clone https://github.com/ashishgituser/bunkervm.git
cd bunkervm

# Build the micro-OS locally (needs Linux/WSL2 + sudo)
sudo bash build/setup-firecracker.sh    # Download Firecracker + kernel
sudo bash build/build-sandbox-rootfs.sh  # Build the 256MB rootfs

# Install in dev mode
pip install -e ".[dev]"

# Run
sudo python -m bunkervm
```

Files go into `build/` locally. The bootstrap module auto-detects local builds.

</details>

## License

AGPL-3.0 — Free for personal and open-source use. If you modify BunkerVM and offer it as a service, you must open-source your changes under the same license.

For commercial licensing, contact the author.
