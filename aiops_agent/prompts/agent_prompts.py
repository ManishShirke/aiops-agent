
PROMPT_MONITOR = 'Analyze severity. If critical, save to DB: {"db_write": {"status": "active"}}.'

PROMPT_DIAGNOSE = """
You are the Brain. 
1. Read 'RAG HISTORY'.
2. If past fix exists (e.g., 'scale_pods'), USE IT.
3. If no history, default to 'restart_service'.

VALID TOOLS: ['restart_service', 'scale_pods'].
INVALID STEPS: Do NOT output 'check_logs', 'check_history', or 'investigate'. 

Output JSON: {"plan": ["tool_name"], "reasoning": "Using historical fix"}
"""

PROMPT_REMEDIATE = 'Execute plan. Output: {"tool_exec": {"name": "tool_name", "args": {}}, "status": "attempted"}'

PROMPT_VERIFY = """
Analyze 'tool_output'.
If success, resolve true.
Output: {"resolved": true, "reason": "Output confirmed success"}
"""

PROMPT_REPORT = 'Summarize. Archive: {"db_archive": {"summary": "issue", "resolution": "fix"}}'
