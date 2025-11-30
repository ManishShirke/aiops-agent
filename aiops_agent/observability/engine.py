import time
import uuid
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Span:
    trace_id: str
    span_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: Dict = field(default_factory=dict)
    
    @property
    def duration_ms(self):
        if self.end_time: return round((self.end_time - self.start_time) * 1000, 2)
        return 0.0

class ObservabilityEngine:
    def __init__(self):
        self.spans: List[Span] = []
        self.active_trace_id = None
        self.current_span_id = None

    def start_trace(self):
        self.active_trace_id = str(uuid.uuid4())[:8]
        print(f"\n{'='*80}")
        print(f"📡 [TRACE START] ID: {self.active_trace_id}")
        print(f"{'='*80}\n")

    def log(self, level, component, message, context=None):
        tid = self.active_trace_id or "NO_TRACE"
        sid = self.current_span_id or "ROOT"
        
        # ANSI Colors for Console
        colors = {"INFO": "\033[94m", "WARN": "\033[93m", "ERROR": "\033[91m", "SUCCESS": "\033[92m", "RESET": "\033[0m"}
        c = colors.get(level, colors["RESET"])
        
        timestamp = time.strftime("%H:%M:%S")
        ctx_str = f" | {json.dumps(context)}" if context else ""
        
        print(f"{timestamp} | {tid}::{sid} | {c}{level:<7}\033[0m | {component:<15} | {message}{ctx_str}")

    # Legacy support method
    def log_event(self, source, message):
        self.log("INFO", source, message)

    def start_span(self, name):
        sid = str(uuid.uuid4())[:6]
        self.current_span_id = sid
        span = Span(
            trace_id=self.active_trace_id,
            span_id=sid,
            name=name,
            start_time=time.perf_counter()
        )
        self.log("INFO", "TELEMETRY", f"Starting Span: {name}")
        return span

    def end_span(self, span: Span, input_text: str, output_text: str, metadata=None):
        span.end_time = time.perf_counter()
        # Rough token estimation (4 chars ~= 1 token)
        span.input_tokens = len(str(input_text)) // 4
        span.output_tokens = len(str(output_text)) // 4
        
        if metadata: span.metadata = metadata
        self.spans.append(span)
        self.current_span_id = None 
        
        self.log("SUCCESS", "TELEMETRY", f"Finished Span: {span.name} in {span.duration_ms}ms", 
                 {"tokens_in": span.input_tokens, "tokens_out": span.output_tokens})

    def get_summary(self):
        print("\n" + "="*80)
        print(f"📊 SYSTEM SUMMARY (Trace: {self.active_trace_id})")
        print("="*80)
        
        total_lat = sum(s.duration_ms for s in self.spans)
        total_in = sum(s.input_tokens for s in self.spans)
        total_out = sum(s.output_tokens for s in self.spans)
        
        print(f"1. Total Latency:      {round(total_lat/1000, 2)}s")
        print(f"2. Total Tokens:       {total_in + total_out} ({total_in} in / {total_out} out)")
        print(f"3. Spans Executed:     {len(self.spans)}")
        
        # Feature: Tool Latency Aggregation
        tool_spans = [s for s in self.spans if "tool_exec" in str(s.metadata)]
        if tool_spans:
            print("\n🛠️  TOOL PERFORMANCE:")
            for s in tool_spans:
                # Find the tool name from metadata if possible, else span name
                print(f"   - {s.name} Action: {s.duration_ms}ms")
        print("="*80 + "\n")

    def get_dashboard(self):
        print("\n" + "="*80)
        print(f"📊 DASHBOARD (Trace: {self.active_trace_id})")
        print("="*80)
        print(f"{'SPAN ID':<8} | {'AGENT':<15} | {'LATENCY':<10} | {'META'}")
        print("-" * 80)
        total = 0 
        for s in self.spans:
            meta = json.dumps(s.metadata)
            print(f"{s.span_id:<8} | {s.name:<15} | {str(s.duration_ms)+'ms':<10} | {meta}")
            total += s.duration_ms
        print("-" * 80)
        print(f"TOTAL LATENCY: {round(total/1000, 2)}s")
        print("="*80 + "\n")

# Global Singleton
TELEMETRY = ObservabilityEngine()
