# Mock BaseAgent for standalone running if google.adk isn't fully installed
class BaseAgent:
    def __init__(self, name, **kwargs): self.name = name

from typing import Any
from aiops_agent import config
from aiops_agent.observability.engine import TELEMETRY
from aiops_agent.adapters.gemini_adapter import InstrumentedAdapter
from aiops_agent.prompts import agent_prompts

class OpsOrchestrator(BaseAgent):
    def __init__(self):
        super().__init__(name="ops_orchestrator")
        # Initialize sub-agents
        self.monitor = InstrumentedAdapter("Monitor", agent_prompts.PROMPT_MONITOR)
        self.diagnose = InstrumentedAdapter("Diagnose", agent_prompts.PROMPT_DIAGNOSE)
        self.remediate = InstrumentedAdapter("Remediate", agent_prompts.PROMPT_REMEDIATE)
        self.verify = InstrumentedAdapter("Verify", agent_prompts.PROMPT_VERIFY)
        self.report = InstrumentedAdapter("Report", agent_prompts.PROMPT_REPORT)
        self.max_loops = config.MAX_LOOPS

    async def run(self, input_text: str):
        """Main execution entry point"""
        TELEMETRY.start_trace()
        TELEMETRY.log("INFO", "ORCHESTRATOR", f"Processing", {"input": input_text})

        # 1. Monitor
        monitor_out = await self.monitor.call(input_text)
        
        # 2. Diagnose
        diagnose_out = await self.diagnose.call({"incident": input_text})
        plan = diagnose_out.get("plan", ["unknown"])
        TELEMETRY.log("INFO", "ORCHESTRATOR", f"Plan", {"plan": plan})

        resolved = False
        
        # 3. Remediation Loop
        for i in range(self.max_loops):
            TELEMETRY.log("WARN", "ORCHESTRATOR", f"Loop {i+1}")
            
            # Remediate (Triggers Human Approval)
            remediate_out = await self.remediate.call({"plan": plan})
            
            # Verify
            verify_out = await self.verify.call({"tool_output": remediate_out.get("tool_output", "")})
            
            if verify_out.get("resolved", False):
                TELEMETRY.log("SUCCESS", "DECISION", "Resolved")
                resolved = True
                break
            else:
                TELEMETRY.log("ERROR", "DECISION", "Failed. Retrying...")

        # 4. Report
        report_out = await self.report.call({"resolved": resolved})
        
        # 5. Finalize
        TELEMETRY.get_summary()
        TELEMETRY.get_dashboard()
        return report_out
