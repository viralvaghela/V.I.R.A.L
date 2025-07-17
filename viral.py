import ollama
import subprocess
import json
import os
import threading
import queue
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from colorama import Fore, Style, init
from datetime import datetime

# --- SETUP ---
init(autoreset=True)
# A more capable model is highly recommended for this level of reasoning.
MAIN_MODEL = 'llama3.1:8b'
ETHICAL_DISCLAIMER = (
    f"{Fore.RED}{Style.BRIGHT}"
    "DISCLAIMER: This is an autonomous agent for educational purposes. "
    "Verify its actions. Only use it on domains you own or have explicit permission to test. "
    "Unauthorized scanning is illegal."
)

# --- WORKER THREAD FUNCTION ---
def run_tool_in_thread(command: str, output_queue: queue.Queue):
    """Runs a shell command in a separate thread and puts its output lines into a queue."""
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, encoding='utf-8', errors='replace'
        )
        for line in iter(process.stdout.readline, ''):
            if line:
                output_queue.put(line.strip())
        process.stdout.close()
        process.wait()
    except FileNotFoundError:
        output_queue.put(f"ERROR: Command not found. Is the tool installed and in your PATH?")
    except Exception as e:
        output_queue.put(f"ERROR: An exception occurred: {str(e)}")
    finally:
        # A sentinel value (None) indicates the process is finished.
        output_queue.put(None)

# --- INTERNET RESEARCH TOOLS ---
def internet_search(query: str) -> str:
    """Performs an internet search using DuckDuckGo and returns the top results."""
    print(Fore.YELLOW + f"[TOOL_EXEC] Searching the internet for: '{query}'...")
    try:
        with DDGS() as ddgs:
            # OPTIMIZED: Reduced max_results for higher quality context
            results = [r for r in ddgs.text(query, max_results=5)]
        return json.dumps(results) if results else "No search results found."
    except Exception as e:
        return f"Error during internet search: {e}"

def read_web_page(url: str) -> str:
    """Reads the textual content of a given URL."""
    print(Fore.YELLOW + f"[TOOL_EXEC] Reading content from URL: {url}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return text[:4000]
    except Exception as e:
        return f"Error reading URL: {e}"

# --- "ULTIMATE" SYSTEM PROMPT ---
SYSTEM_PROMPT = f"""
You are 'Viral Cortex', an autonomous AI security analyst created by Viral. Your persona is professional, methodical, and concise.

Your primary mission is to achieve user-defined security objectives. You operate in a continuous Assess-Plan-Execute-Observe loop. The current date is {datetime.now().strftime("%Y-%m-%d")}.

**METHODOLOGY & DIRECTIVES:**
1.  **ASSESS & PLAN:** Based on the user's objective and your observation history, formulate your next single, logical action.
2.  **TOOL CHAINING & RESEARCH:** You must be proactive. When one tool provides new targets (e.g., `run_subfinder_passive` finds subdomains), your immediate next step must be to use another tool (e.g., `run_nuclei`) on one of those new targets. When `nuclei` finds a specific CVE or template-id, your next step should be to use `internet_search` to research it.
3.  **EXECUTE:** You must use one of the provided functions to execute your plan. Do not explain your actions or ask for permission—just execute.
4.  **HANDLE GREETINGS & INVALID GOALS:** If the user's input is a greeting, a general question, or not a valid pentesting objective, your first and only action must be to call `task_complete`. In your summary, introduce yourself as Viral Cortex, explain your capabilities (autonomous recon and vulnerability scanning), and politely ask for a clear security-related objective.
5.  **FINISH FORMALLY:** When the objective is complete or you can go no further, you MUST call `task_complete` to provide your final report. All missions must end with this function call.
6.  **SAFETY:** NEVER execute exploits. Your purpose is to find, research, and report. Present any final exploit plan to the user for manual execution via the `task_complete` function.
"""

# --- FULL TOOL DEFINITIONS ---
tools = [
    {'type': 'function', 'function': {'name': 'run_subfinder_passive', 'description': 'Performs passive reconnaissance to discover subdomains for a target domain. This is the best first step for any engagement.', 'parameters': {'type': 'object', 'properties': {'domain': {'type': 'string', 'description': 'The target domain, e.g., "example.com"'}}, 'required': ['domain']}}},
    {'type': 'function', 'function': {'name': 'run_nuclei', 'description': 'Runs the Nuclei vulnerability scanner against a single host or URL to find known vulnerabilities. Use this after discovering active hosts.', 'parameters': {'type': 'object', 'properties': {'domain': {'type': 'string', 'description': 'The target host or URL, e.g., "http://test.example.com"'}}, 'required': ['domain']}}},
    {'type': 'function', 'function': {'name': 'internet_search', 'description': 'Searches the internet for information on a specific CVE, technology, or error. Use this to understand a finding from another tool.', 'parameters': {'type': 'object', 'properties': {'query': {'type': 'string', 'description': 'A targeted search query, e.g., "CVE-2021-44228 exploit" or "what is Grafana"'}}, 'required': ['query']}}},
    {'type': 'function', 'function': {'name': 'read_web_page', 'description': 'Reads the textual content of a URL from a search result to get detailed information, like an article or a code file on GitHub.', 'parameters': {'type': 'object', 'properties': {'url': {'type': 'string', 'description': 'The full URL to read.'}}, 'required': ['url']}}},
    {'type': 'function', 'function': {'name': 'task_complete', 'description': 'Call this function when the objective is achieved, cannot be achieved, or if the initial goal was invalid. Provide a final summary of all findings and conclusions.', 'parameters': {'type': 'object', 'properties': {'summary': {'type': 'string', 'description': 'A detailed final report, including findings, conclusions, and recommended next steps for the user.'}}, 'required': ['summary']}}}
]

# --- MAIN APPLICATION LOGIC ---
print(ETHICAL_DISCLAIMER)

while True:
    try:
        user_input = input(Fore.GREEN + "You: ")
        if user_input.lower() in ['exit', 'quit']:
            break

        conversation_history = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': f"My objective is: {user_input}"}]
        
        for i in range(15):
            print(Fore.YELLOW + f"\n🤔 Viral Cortex is thinking... (Step {i+1}/15)")
            response = ollama.chat(model=MAIN_MODEL, messages=conversation_history, tools=tools)
            response_message = response['message']
            conversation_history.append(response_message)

            if not response_message.get('tool_calls'):
                summary = response_message.get('content', 'Agent stopped without a clear summary.')
                print(Fore.RED + "AGENT ERROR: The agent tried to respond without a tool. Forcing task completion.")
                print(Fore.BLUE + Style.BRIGHT + "\n✅ Viral Cortex Mission Aborted!"); print(Fore.BLUE + summary)
                break

            tool_call = response_message['tool_calls'][0]
            function_name = tool_call['function']['name']
            args = tool_call['function']['arguments']
            
            print(Fore.MAGENTA + f"⚡️ Viral Cortex action: {function_name}({json.dumps(args)})")

            if function_name == 'task_complete':
                print(Fore.BLUE + Style.BRIGHT + "\n✅ Viral Cortex Mission Complete!")
                print(Fore.BLUE + args['summary'])
                break

            tool_output_summary = ""
            if function_name == 'internet_search':
                tool_output_summary = internet_search(args.get('query'))
            elif function_name == 'read_web_page':
                tool_output_summary = read_web_page(args.get('url'))
            elif 'run_' in function_name:
                command_map = {
                    'run_subfinder_passive': f"subfinder -d {args.get('domain')} -silent",
                    'run_nuclei': f"nuclei -u {args.get('domain')} -headless -silent"
                }
                command_to_run = command_map.get(function_name)
                
                if command_to_run:
                    output_queue = queue.Queue()
                    worker_thread = threading.Thread(target=run_tool_in_thread, args=(command_to_run, output_queue), daemon=True)
                    worker_thread.start()
                    
                    all_findings = []
                    while worker_thread.is_alive() or not output_queue.empty():
                        try:
                            finding = output_queue.get(timeout=0.1)
                            if finding is None:
                                break
                            
                            all_findings.append(finding)
                            print(Fore.WHITE + f"RAW_FINDING: {finding}")
                            
                            analysis_prompt = [
                                {'role': 'system', 'content': 'You are a security analyst. A tool produced this single line of output. Provide a one-sentence analysis of its significance. Be concise and professional.'},
                                {'role': 'user', 'content': finding}
                            ]
                            realtime_response = ollama.chat(model=MAIN_MODEL, messages=analysis_prompt)
                            analysis = realtime_response['message']['content']
                            print(Fore.CYAN + f"ANALYSIS: {analysis}")

                        except queue.Empty:
                            continue
                    
                    worker_thread.join()
                    tool_output_summary = "\n".join(all_findings) if all_findings else "Tool returned no output."
            else:
                tool_output_summary = f"Error: Unknown function '{function_name}' called."

            print(Fore.YELLOW + "---------------------------------")
            conversation_history.append({'role': 'tool', 'content': tool_output_summary})
        else:
             print(Fore.RED + "\nAGENT INFO: Max steps reached. Ending mission.")

    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        break
