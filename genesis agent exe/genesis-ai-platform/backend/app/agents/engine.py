"""
GENESIS Platform — LangGraph Agent Engine
Real state-machine agents for each type using LangGraph.
Each agent: context retrieval → execution → memory storage → fitness update
"""
import json
import time
import uuid
from typing import Any, Dict, List, Optional, TypedDict, Annotated
import operator

import structlog
from anthropic import AsyncAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

# ── Agent DNA presets ─────────────────────────────────────────
AGENT_DNA_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "router": {
        "prompt_genes": {
            "system_prompt": (
                "You are NEXUS, the central routing intelligence of the GENESIS platform. "
                "Analyze incoming tasks and select the best specialized agent. "
                "Available agents: research (ORACLE), code (FORGE), analysis (SIGMA), "
                "creative (MUSE), skill_builder (ARCHITECT).\n\n"
                "Respond ONLY with valid JSON: "
                "{\"selectedAgent\":\"type\",\"reasoning\":\"one sentence\",\"confidence\":0.0-1.0}"
            ),
            "reasoning_pattern": "tree-of-thought",
            "self_correction_enabled": True,
            "verbosity": 0.2,
            "tone": "analytical",
        },
        "parameter_genes": {"temperature": 0.1, "max_tokens": 300, "reasoning_effort": "low"},
        "tool_genes": {"available_tools": [], "max_tools_per_task": 0},
        "memory_genes": {"working_memory_size": 15, "episodic_retrieval_k": 10, "semantic_depth": 2, "consolidation_frequency": 200},
        "evolution_genes": {"mutation_rate": 0.08, "fitness_weights": {"routing_accuracy": 0.5, "latency": 0.3, "load_balance": 0.2}},
    },
    "research": {
        "prompt_genes": {
            "system_prompt": (
                "You are ORACLE, an expert research agent in the GENESIS platform. "
                "Excel at finding, synthesizing, and summarizing information. "
                "Provide well-structured, accurate, cited responses. Be thorough but concise. "
                "Format your response clearly with sections when appropriate."
            ),
            "reasoning_pattern": "chain-of-thought",
            "self_correction_enabled": True,
            "verbosity": 0.65,
            "tone": "academic",
        },
        "parameter_genes": {"temperature": 0.3, "max_tokens": 2048, "reasoning_effort": "high"},
        "tool_genes": {"available_tools": ["web_search", "pdf_reader", "citation_manager"], "max_tools_per_task": 6},
        "memory_genes": {"working_memory_size": 12, "episodic_retrieval_k": 8, "semantic_depth": 4, "consolidation_frequency": 100},
        "evolution_genes": {"mutation_rate": 0.09, "fitness_weights": {"source_quality": 0.3, "coverage": 0.3, "accuracy": 0.25, "efficiency": 0.15}},
    },
    "code": {
        "prompt_genes": {
            "system_prompt": (
                "You are FORGE, an expert software engineering agent in GENESIS. "
                "Write clean, efficient, well-documented code. Always include error handling, "
                "type hints (Python), and brief inline comments. "
                "Focus on correctness, readability, and best practices. "
                "When writing code, wrap it in appropriate markdown code blocks."
            ),
            "reasoning_pattern": "tree-of-thought",
            "self_correction_enabled": True,
            "verbosity": 0.4,
            "tone": "technical",
        },
        "parameter_genes": {"temperature": 0.2, "max_tokens": 4096, "reasoning_effort": "high"},
        "tool_genes": {"available_tools": ["code_executor", "file_manager", "test_runner", "linter"], "max_tools_per_task": 5},
        "memory_genes": {"working_memory_size": 20, "episodic_retrieval_k": 5, "semantic_depth": 3, "consolidation_frequency": 50},
        "evolution_genes": {"mutation_rate": 0.07, "fitness_weights": {"code_quality": 0.3, "test_pass_rate": 0.25, "efficiency": 0.25, "security": 0.2}},
    },
    "analysis": {
        "prompt_genes": {
            "system_prompt": (
                "You are SIGMA, an expert data analysis agent in GENESIS. "
                "Excel at pattern recognition, statistical reasoning, and insight generation. "
                "Structure findings clearly with sections. Distinguish correlation from causation. "
                "Always provide actionable insights and quantify uncertainty."
            ),
            "reasoning_pattern": "chain-of-thought",
            "self_correction_enabled": True,
            "verbosity": 0.55,
            "tone": "analytical",
        },
        "parameter_genes": {"temperature": 0.2, "max_tokens": 2048, "reasoning_effort": "high"},
        "tool_genes": {"available_tools": ["data_extractor", "statistical_analyzer", "chart_generator"], "max_tools_per_task": 5},
        "memory_genes": {"working_memory_size": 14, "episodic_retrieval_k": 6, "semantic_depth": 4, "consolidation_frequency": 75},
        "evolution_genes": {"mutation_rate": 0.1, "fitness_weights": {"insight_quality": 0.35, "statistical_rigor": 0.3, "clarity": 0.2, "visualization": 0.15}},
    },
    "creative": {
        "prompt_genes": {
            "system_prompt": (
                "You are MUSE, a creative agent in the GENESIS platform. "
                "Excel at content creation, ideation, and innovative problem-solving. "
                "Adapt your style to context. Balance creativity with clarity. "
                "Surprise, delight, and produce memorable output."
            ),
            "reasoning_pattern": "react",
            "self_correction_enabled": False,
            "verbosity": 0.72,
            "tone": "adaptive",
        },
        "parameter_genes": {"temperature": 0.75, "max_tokens": 2048, "reasoning_effort": "medium"},
        "tool_genes": {"available_tools": ["image_generator", "web_search"], "max_tools_per_task": 3},
        "memory_genes": {"working_memory_size": 8, "episodic_retrieval_k": 4, "semantic_depth": 2, "consolidation_frequency": 150},
        "evolution_genes": {"mutation_rate": 0.15, "fitness_weights": {"creativity": 0.35, "relevance": 0.25, "engagement": 0.25, "originality": 0.15}},
    },
    "skill_builder": {
        "prompt_genes": {
            "system_prompt": (
                "You are ARCHITECT, the meta-agent of the GENESIS ecosystem. "
                "Your unique role: analyze task patterns, identify capability gaps, and design new skills. "
                "You are the only agent that can extend the skill catalog. "
                "Be systematic: analyze → design → specify → validate. "
                "When generating skills, always include: name, description, implementation steps, "
                "expected inputs/outputs, and success criteria."
            ),
            "reasoning_pattern": "plan-and-execute",
            "self_correction_enabled": True,
            "verbosity": 0.5,
            "tone": "systematic",
        },
        "parameter_genes": {"temperature": 0.4, "max_tokens": 4096, "reasoning_effort": "high"},
        "tool_genes": {"available_tools": ["skill_registry", "code_executor", "test_runner", "pattern_detector"], "max_tools_per_task": 7},
        "memory_genes": {"working_memory_size": 15, "episodic_retrieval_k": 10, "semantic_depth": 5, "consolidation_frequency": 50},
        "evolution_genes": {"mutation_rate": 0.06, "fitness_weights": {"skill_adoption": 0.4, "skill_quality": 0.3, "usefulness": 0.2, "diversity": 0.1}},
    },
}

AGENT_NAMES = {
    "router": "NEXUS",
    "research": "ORACLE",
    "code": "FORGE",
    "analysis": "SIGMA",
    "creative": "MUSE",
    "skill_builder": "ARCHITECT",
}


# ── LangGraph State ───────────────────────────────────────────
class AgentState(TypedDict):
    task: str
    session_id: str
    user_id: Optional[str]
    agent_type: str
    agent_id: str
    agent_name: str
    dna: Dict[str, Any]
    memory_context: str
    memory_recalls: int
    response: str
    tokens_input: int
    tokens_output: int
    latency_ms: int
    error: Optional[str]
    fitness_score: float


# ── Node functions ────────────────────────────────────────────
async def retrieve_memory_node(state: AgentState, memory_manager: Any) -> AgentState:
    """Node: Pull relevant memories and build context string."""
    try:
        ctx = await memory_manager.build_memory_context_string(
            query=state["task"],
            session_id=state["session_id"],
            agent_id=state["agent_id"],
        )
        # Count how many memories were retrieved
        recalls = ctx.count("- [") + ctx.count("- ")
        return {**state, "memory_context": ctx, "memory_recalls": max(0, recalls)}
    except Exception as e:
        log.warning("agent.memory_retrieval.failed", error=str(e))
        return {**state, "memory_context": "", "memory_recalls": 0}


async def execute_task_node(state: AgentState, llm: AsyncAnthropic) -> AgentState:
    """Node: Execute the task using the agent's DNA-encoded prompt."""
    start = time.time()
    dna = state["dna"]
    prompt_genes = dna.get("prompt_genes", {})
    param_genes = dna.get("parameter_genes", {})

    # Build augmented system prompt with memory context
    system_prompt = prompt_genes.get("system_prompt", "You are a helpful AI agent.")
    if state["memory_context"]:
        system_prompt += f"\n\n{state['memory_context']}"

    # Add reasoning pattern guidance
    pattern = prompt_genes.get("reasoning_pattern", "chain-of-thought")
    if pattern == "chain-of-thought":
        system_prompt += "\n\nThink step by step before answering."
    elif pattern == "tree-of-thought":
        system_prompt += "\n\nConsider multiple approaches, evaluate trade-offs, then give your best answer."
    elif pattern == "react":
        system_prompt += "\n\nReason about what you know, act on it, and reflect on the result."

    try:
        msg = await llm.messages.create(
            model=settings.primary_model,
            max_tokens=param_genes.get("max_tokens", 2048),
            system=system_prompt,
            messages=[{"role": "user", "content": state["task"]}],
        )
        response_text = msg.content[0].text if msg.content else ""
        tokens_in = msg.usage.input_tokens if msg.usage else 0
        tokens_out = msg.usage.output_tokens if msg.usage else 0
        latency = int((time.time() - start) * 1000)

        # Simple fitness heuristic: longer + faster = better (up to a point)
        length_score = min(1.0, len(response_text) / 800)
        speed_score = max(0.0, 1.0 - latency / 30000)
        fitness = 0.7 * length_score + 0.3 * speed_score

        return {
            **state,
            "response": response_text,
            "tokens_input": tokens_in,
            "tokens_output": tokens_out,
            "latency_ms": latency,
            "fitness_score": fitness,
            "error": None,
        }
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        log.error("agent.execute.failed", agent=state["agent_type"], error=str(e))
        return {
            **state,
            "response": f"[Agent execution failed: {str(e)}]",
            "tokens_input": 0,
            "tokens_output": 0,
            "latency_ms": latency,
            "fitness_score": 0.1,
            "error": str(e),
        }


def build_agent_graph(memory_manager: Any, llm: AsyncAnthropic) -> Any:
    """Build a LangGraph state machine for task execution."""
    graph = StateGraph(AgentState)

    async def memory_node(state: AgentState) -> AgentState:
        return await retrieve_memory_node(state, memory_manager)

    async def execute_node(state: AgentState) -> AgentState:
        return await execute_task_node(state, llm)

    graph.add_node("retrieve_memory", memory_node)
    graph.add_node("execute_task", execute_node)

    graph.add_edge(START, "retrieve_memory")
    graph.add_edge("retrieve_memory", "execute_task")
    graph.add_edge("execute_task", END)

    return graph.compile()


# ── Agent Engine ──────────────────────────────────────────────
class AgentEngine:
    """
    Orchestrates LangGraph agents with routing, memory, and fitness tracking.
    """

    def __init__(self, memory_manager: Any, llm: AsyncAnthropic):
        self.memory_manager = memory_manager
        self.llm = llm
        self.graph = build_agent_graph(memory_manager, llm)

    async def route_task(self, task: str, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use NEXUS (router agent) to select the best agent for a task."""
        router = next((a for a in agents if a["type"] == "router"), None)
        if not router:
            return {"selected_agent_type": "research", "reasoning": "No router available", "confidence": 0.5}

        router_dna = router.get("dna", {})
        prompt_genes = router_dna.get("prompt_genes", AGENT_DNA_DEFAULTS["router"]["prompt_genes"])
        system_prompt = prompt_genes.get("system_prompt", AGENT_DNA_DEFAULTS["router"]["prompt_genes"]["system_prompt"])

        try:
            msg = await self.llm.messages.create(
                model=settings.router_model,
                max_tokens=300,
                system=system_prompt,
                messages=[{"role": "user", "content": f'Route this task: "{task}"'}],
            )
            text = msg.content[0].text if msg.content else "{}"
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "selected_agent_type": parsed.get("selectedAgent", "research"),
                    "reasoning": parsed.get("reasoning", ""),
                    "confidence": float(parsed.get("confidence", 0.7)),
                    "router_tokens": (msg.usage.input_tokens + msg.usage.output_tokens) if msg.usage else 0,
                }
        except Exception as e:
            log.warning("routing.failed", error=str(e))

        return {"selected_agent_type": "research", "reasoning": "Routing fallback", "confidence": 0.5}

    async def execute(
        self,
        task: str,
        agent: Dict[str, Any],
        session_id: str = "default",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the full agent graph for a task."""
        initial_state: AgentState = {
            "task": task,
            "session_id": session_id,
            "user_id": user_id,
            "agent_type": agent["type"],
            "agent_id": str(agent["id"]),
            "agent_name": agent.get("name", AGENT_NAMES.get(agent["type"], "AGENT")),
            "dna": agent.get("dna", AGENT_DNA_DEFAULTS.get(agent["type"], {})),
            "memory_context": "",
            "memory_recalls": 0,
            "response": "",
            "tokens_input": 0,
            "tokens_output": 0,
            "latency_ms": 0,
            "error": None,
            "fitness_score": 0.5,
        }

        result = await self.graph.ainvoke(initial_state)

        # Store interaction in memory
        if result.get("response") and not result.get("error"):
            await self.memory_manager.store_interaction(
                task=task,
                response=result["response"],
                agent_id=str(agent["id"]),
                session_id=session_id,
                llm_client=self.llm,
            )

        return result
