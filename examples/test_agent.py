"""Simple BunkerVM + LangGraph test — AI agent runs code in a secure VM."""
import os, socket, json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

load_dotenv()

# ── Talk to the VM via vsock ──
def vm_request(method, path, body=None):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(30)
    s.connect("/tmp/bunkervm-vsock.sock")
    s.sendall(b"CONNECT 8080\n")
    if b"OK" not in s.recv(256):
        raise Exception("VM handshake failed")
    if body:
        payload = json.dumps(body).encode()
        req = f"{method} {path} HTTP/1.0\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: {len(payload)}\r\nConnection: close\r\n\r\n".encode() + payload
    else:
        req = f"{method} {path} HTTP/1.0\r\nHost: localhost\r\nConnection: close\r\n\r\n".encode()
    s.sendall(req)
    data = b""
    while True:
        chunk = s.recv(65536)
        if not chunk: break
        data += chunk
    s.close()
    parts = data.split(b"\r\n\r\n", 1)
    return json.loads(parts[1]) if len(parts) > 1 else {}

# ── Tools the AI agent can use ──
@tool
def run_command(command: str) -> str:
    """Run a shell command inside the secure BunkerVM sandbox."""
    r = vm_request("POST", "/exec", {"command": command})
    return r.get("stdout", "") + r.get("stderr", "")

@tool
def write_file(path: str, content: str) -> str:
    """Write a file inside the BunkerVM sandbox."""
    r = vm_request("POST", "/write", {"path": path, "content": content})
    return f"Written {r.get('bytes_written', 0)} bytes to {path}"

@tool
def read_file(path: str) -> str:
    """Read a file from the BunkerVM sandbox."""
    r = vm_request("POST", "/read", {"path": path})
    return r.get("content", "")

# ── Build the LangGraph agent ──
tools = [run_command, write_file, read_file]
llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(tools)

def agent(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

def should_continue(state: MessagesState):
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

graph = StateGraph(MessagesState)
graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")
app = graph.compile()

# ── Run it ──
print("\n🔒 BunkerVM + LangGraph Test\n")
task = "Write a Python script that finds all prime numbers under 100, save it to /tmp/primes.py, run it, and show me the results."
print(f"Task: {task}\n")

result = app.invoke({"messages": [
    SystemMessage(content="You are a coding assistant. You run code inside a secure VM sandbox. Use the tools to write and execute code."),
    HumanMessage(content=task),
]})

# Print the final response
for msg in result["messages"]:
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"  [Tool: {tc['name']}] {tc['args'].get('command', tc['args'].get('path', ''))}")
    elif hasattr(msg, "content") and msg.content and msg.type == "ai":
        print(f"\n🤖 Agent: {msg.content}")
    elif msg.type == "tool":
        print(f"  → {msg.content[:200]}")

print("\n✅ Done!")
