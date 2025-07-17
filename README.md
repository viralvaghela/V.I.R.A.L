# Viral Cortex - Autonomous AI Pentesting Agent

**Viral Cortex** is an advanced, autonomous AI security analyst designed for offensive security operations. Powered by a Large Language Model (LLM), this agent can independently plan and execute a multi-step penetration testing methodology, from initial reconnaissance to vulnerability scanning and research. It was created by Viral and leverages powerful open-source tools to achieve its objectives.

---

## Ethical Disclaimer

This tool is intended for **educational purposes and authorized security assessments only**. Running scans against systems or networks without explicit, written permission from the owner is illegal. The user assumes all responsibility for any actions performed using this tool. The creator, Viral, is not responsible for any misuse or damage.

---

## Features

* **Autonomous Operation**: Give Viral Cortex a high-level goal (e.g., "Assess example.com for vulnerabilities"), and it will independently create and execute a plan to achieve it.
* **Intelligent Tool Chaining**: The agent is proactive. After finding subdomains with `subfinder`, it automatically knows to start scanning those targets with `nuclei`.
* **Real-time Internet Research**: When it discovers a potential CVE or an unknown technology, Viral Cortex uses its built-in search tools to research the finding, read articles, and understand the potential impact before proceeding.
* **Live Analysis Stream**: Don't just wait for a final report. As tools like `nuclei` stream their findings, the agent provides a real-time, line-by-line analysis of each discovery's significance.
* **Safety First**: The agent will never attempt to execute an exploit. Its final step is always to report its findings and present a detailed manual action plan for the human operator.
* **Conversational Handling**: The agent can recognize when it's not being given a valid pentesting task and will respond conversationally, explaining its capabilities.

---

## Project Status & Roadmap

This section outlines the current capabilities of Viral Cortex and the exciting plans for its future development.

### What's Done (Current Features)

* **Autonomous Agent Core**: The foundational Assess-Plan-Execute-Observe loop that allows the agent to operate independently.
* **Dynamic Tool Integration**: A flexible system for adding and describing command-line tools to the agent.
* **Core Toolset**:
    * `subfinder` for passive subdomain reconnaissance.
    * `nuclei` for fast, template-based vulnerability scanning.
* **Internet Research Module**:
    * `internet_search` to gather intelligence on findings.
    * `read_web_page` to extract information from articles and code repositories.
* **Real-time Analysis**: A multi-threading architecture that provides live, AI-driven analysis of tool output as it happens.

### In Progress & Future Plans

The vision for Viral Cortex is to make it an even more powerful and indispensable tool for security professionals. Here are some of the features in the pipeline:

* **Expand the Toolkit**:
    * **Active Reconnaissance**: Integrate `nmap` for port scanning and service enumeration.
    * **Web Discovery**: Add `httpx` for tech stack detection and `dirsearch` for content discovery.
    * **API Integrations**: Connect to services like Shodan, VirusTotal, and GreyNoise for enhanced intelligence gathering.
* **Long-Term Memory**:
    * Implement a vector database (e.g., ChromaDB, FAISS) to give the agent a persistent memory. It could remember findings from previous scans on a target to inform future assessments.
* **Advanced Attack Planning**:
    * Move beyond simple tool-chaining to more complex attack plan generation. The agent could create a graph of possible attack paths and choose the most promising one.
* **Exploit Analysis & Modification**:
    * Enhance the agent's ability to not just find exploit PoCs, but to analyze the code, identify key parameters, and suggest modifications for the specific target environment.
* **Formal Reporting**:
    * Add a `generate_report` tool that allows the agent to compile all its findings, analysis, and conclusions into a formal Markdown or PDF report at the end of a mission.

---

## Setup & Installation

Follow these steps to get Viral Cortex up and running.

### 1. Prerequisites: Install Core Tools

Viral Cortex depends on two powerful, community-trusted security tools. You must install them and ensure they are available in your system's `PATH`.

* **Subfinder**:
    ```bash
    go install -v https://github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    ```
* **Nuclei**:
    ```bash
    go install -v https://github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    ```

### 2. Install Python Dependencies

The agent requires several Python libraries. It's recommended to use a virtual environment.

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install all required packages
pip install ollama requests beautifulsoup4 ddgs colorama
```

### 3. Get Ollama

This agent requires a running Ollama instance to function.

1.  Download and install [Ollama](https://ollama.com/).
2.  Pull the model used by the agent:
    ```bash
    ollama pull llama3.1:8b
    ```

### 4. Run the Agent

Once everything is installed, you can start the agent:

```bash
python ./viral_cortex_agent.py
```

---

## How to Use

Simply state your high-level objective at the prompt. The agent will take it from there.

#### Example 1: Simple Reconnaissance

> **You:** `Find subdomains for example.com`

Viral Cortex will run `subfinder`, display the results, and then use its `task_complete` function to provide a summary, as the goal was simple and has been achieved.

#### Example 2: Full Autonomous Assessment

> **You:** `Perform a full assessment of example.com`

This will trigger the agent's full capabilities:
1.  It will start by running `run_subfinder_passive` to find subdomains.
2.  After observing the results, it will pick a subdomain from the list and use `run_nuclei` to scan it.
3.  If `nuclei` finds a specific vulnerability (e.g., `[CVE-2023-1234]`), the agent will automatically use `internet_search` to learn more about it.
4.  It will then use `read_web_page` to study an exploit PoC on GitHub.
5.  Finally, it will call `task_complete` to provide a full report, including the vulnerability details and the manual steps you should take to verify or exploit it.

#### Example 3: Conversational Interaction

> **You:** `hello what are you?`

The agent will recognize this is not a task and will respond by introducing itself and explaining its purpose, before waiting for a valid pentesting goal.

---

## Architecture Overview

* **System Prompt**: The agent's "brain" is a detailed system prompt that defines its persona (`Viral Cortex`), its methodology (Assess -> Plan -> Research -> Execute -> Observe), and its critical safety directives.
* **Autonomous Loop**: The agent runs in a loop, continuously making observations, planning its next action, and executing a tool until its main goal is complete.
* **Tool Abstraction**: All external tools (`subfinder`, `nuclei`, web search) are wrapped in Python functions, which are then described to the LLM in a structured format it can understand and choose from.
* **Real-time Analysis**: A multi-threading approach is used to run blocking command-line tools. The main thread streams the tool's output while simultaneously making quick, secondary LLM calls to analyze each line as it appears.
