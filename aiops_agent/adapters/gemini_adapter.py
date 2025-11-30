import asyncio
import json
import re
import time
import sys
import google.generativeai as genai
from typing import Any, Dict
from aiops_agent import config
from aiops_agent.observability.engine import TELEMETRY
from aiops_agent.infrastructure.state_store import STATE
from aiops_agent.infrastructure.message_bus import BUS

class InstrumentedAdapter:
    def __init__(self, name, instruction):
        self.name = name
        self.instruction = instruction
        try: self.model = genai.GenerativeModel(config.MODEL_PRIMARY)
        except: self.model = genai.GenerativeModel(config.MODEL_FALLBACK)

    async def call(self, input_data: Any) -> Dict:
        span = TELEMETRY.start_span(self.name)
        TELEMETRY.log("INFO", self.name, "Input Received", {"data": str(input_data)[:50] + "..."})

        inbox = BUS.consume(self.name)
        history_context = ""
        if "incident" in str(input_data):
            history_context = STATE.search_history("payments")

        system_prompt = (
            f"{self.instruction}\n"
            "CAPABILITIES: {db_write, bus_publish, db_archive, tool_exec}\n"
            "IMPORTANT: Output ONLY valid JSON.\n\n"
            f"--- INBOX ---\n{str(inbox)}\n"
            f"--- RAG HISTORY ---\n{history_context}\n"
        )
        full_prompt = f"{system_prompt}\n\nTask Input: {str(input_data)}"

        try:
            TELEMETRY.log("INFO", self.name, "Generating (Thinking)...")
            response = await asyncio.to_thread(self.model.generate_content, full_prompt)
            result_json = self._clean_json(response.text)
        except Exception as e:
            TELEMETRY.log("ERROR", self.name, f"Generation Failed: {e}")
            result_json = {}

        TELEMETRY.log("INFO", self.name, "Output Generated", {"keys": list(result_json.keys())})
        meta_actions = self._handle_side_effects(result_json)
        
        TELEMETRY.end_span(span, full_prompt, response.text if 'response' in locals() else "", metadata={"actions": meta_actions})
        return result_json

    def _handle_side_effects(self, result_json):
        meta_actions = []
        if "db_write" in result_json:
            for k, v in result_json["db_write"].items():
                STATE.save_fact(k, v)
                meta_actions.append("db_write")
        if "db_archive" in result_json:
            arc = result_json["db_archive"]
            STATE.archive_incident(arc.get("summary"), arc.get("resolution"))
            meta_actions.append("db_archive")
        if "bus_publish" in result_json:
            pub = result_json["bus_publish"]
            BUS.publish(self.name, pub.get("to"), pub.get("msg"))
            meta_actions.append("bus_publish")
        if "tool_exec" in result_json:
            self._handle_tool(result_json)
            meta_actions.append(f"tool:{result_json['tool_exec']['name']}")
        return meta_actions

    def _handle_tool(self, result_json):
        tool = result_json["tool_exec"]
        t_name = tool.get("name")
        
        # --- HARDCODED MOCK APPROVAL ---
        print(f"\n{'!'*60}")
        print(f"    ⚠️  [APPROVAL REQUIRED] Agent wants to execute: '{t_name}'")
        print(f"    >> [Auto-Approving for Demo] User simulated typing 'y'...")
        print(f"{'!'*60}\n")
        sys.stdout.flush()
        
        time.sleep(1.5) # Simulate "reading" time
        approval = 'y'  # <--- HARDCODED "YES"

        if approval == 'y':
            TELEMETRY.log("WARN", "TOOL_EXEC", f"Starting: {t_name}")
            time.sleep(0.5) 
            if t_name == "restart_service": result = "Service PID 404 restarted."
            elif t_name == "scale_pods": result = "Deployment scaled to 10 replicas."
            else: result = "Tool not found."
            result_json["tool_output"] = result
            TELEMETRY.log("SUCCESS", "TOOL_EXEC", "Finished")
        else:
            TELEMETRY.log("WARN", "TOOL_EXEC", "Denied by user")
            result_json["tool_output"] = "User denied action."
            result_json["status"] = "denied"

    def _clean_json(self, text):
        try: return json.loads(re.sub(r"```json|```", "", text).strip())
        except: return {}
