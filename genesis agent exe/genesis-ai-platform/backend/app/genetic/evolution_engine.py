"""
GENESIS Platform — Genetic Evolution Engine
LLM-powered semantic mutation, crossover, tournament selection, 3-stage fitness evaluation.
Based on Technical Specification doc 06_GENETIC_EVOLUTION_ENGINE.md
"""
import copy
import json
import math
import random
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import structlog
from anthropic import AsyncAnthropic

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()


# ── Mutation Intensity ────────────────────────────────────────
MUTATION_PROMPTS = {
    "mild": (
        "You are a genetic mutation engine for AI agents. Apply a MILD mutation to this system prompt. "
        "Make only subtle improvements: fix clarity, adjust tone slightly, improve a specific instruction. "
        "Keep 90%+ of the original content. Return ONLY the mutated system prompt text, no explanation."
    ),
    "medium": (
        "You are a genetic mutation engine for AI agents. Apply a MEDIUM mutation to this system prompt. "
        "Restructure some sections, change the reasoning approach, add or remove constraints. "
        "Keep the agent's core identity but meaningfully alter its strategy. "
        "Return ONLY the mutated system prompt text, no explanation."
    ),
    "strong": (
        "You are a genetic mutation engine for AI agents. Apply a STRONG mutation to this system prompt. "
        "Significantly redesign the prompt: new reasoning framework, different persona aspects, "
        "new constraints or freedoms, different output format instructions. "
        "The agent should feel meaningfully different while keeping its domain expertise. "
        "Return ONLY the mutated system prompt text, no explanation."
    ),
}

CROSSOVER_PROMPT = """You are a genetic crossover engine for AI agents.
Blend these two system prompts into one child prompt that:
1. Inherits the best reasoning patterns from Parent A (fitness: {fit_a:.3f})
2. Inherits the best domain expertise from Parent B (fitness: {fit_b:.3f})
3. Resolves any conflicting instructions in favor of the higher-fitness parent
4. Feels coherent and unified, not like two prompts stitched together

Parent A (fitness {fit_a:.3f}):
{prompt_a}

Parent B (fitness {fit_b:.3f}):
{prompt_b}

Return ONLY the child system prompt text, no explanation."""


@dataclass
class MutationResult:
    agent_id: str
    original_fitness: float
    new_dna: Dict[str, Any]
    changes: Dict[str, Any]
    intensity: str
    event_type: str = "mutation"


@dataclass
class CrossoverResult:
    parent_a_id: str
    parent_b_id: str
    new_dna: Dict[str, Any]
    parent_a_fitness: float
    parent_b_fitness: float
    event_type: str = "crossover"


@dataclass
class FitnessEvaluation:
    agent_id: str
    fitness_score: float
    components: Dict[str, float]
    stage: int
    task_count: int = 0


# ── Parameter Gene Mutation (numeric) ────────────────────────
def _mutate_parameter_genes(
    genes: Dict[str, Any], rate: float, intensity: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Mutate numeric parameter genes according to mutation rate and intensity."""
    new_genes = copy.deepcopy(genes)
    changes = {}

    scale = {"mild": 0.05, "medium": 0.12, "strong": 0.25}.get(intensity, 0.1)

    if random.random() < rate:
        old = new_genes.get("temperature", 0.3)
        delta = random.gauss(0, scale)
        new_val = round(max(0.01, min(1.5, old + delta)), 3)
        new_genes["temperature"] = new_val
        changes["temperature"] = {"old": old, "new": new_val}

    if random.random() < rate * 0.5:
        old = new_genes.get("max_tokens", 2048)
        options = [512, 1024, 2048, 4096]
        new_val = random.choice([o for o in options if o != old] or options)
        new_genes["max_tokens"] = new_val
        changes["max_tokens"] = {"old": old, "new": new_val}

    if random.random() < rate * 0.3:
        old = new_genes.get("reasoning_effort", "medium")
        opts = ["low", "medium", "high"]
        new_val = random.choice([o for o in opts if o != old])
        new_genes["reasoning_effort"] = new_val
        changes["reasoning_effort"] = {"old": old, "new": new_val}

    return new_genes, changes


def _mutate_memory_genes(
    genes: Dict[str, Any], rate: float, intensity: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Mutate memory configuration genes."""
    new_genes = copy.deepcopy(genes)
    changes = {}
    scale = {"mild": 1, "medium": 2, "strong": 4}.get(intensity, 2)

    if random.random() < rate:
        old = new_genes.get("episodic_retrieval_k", 5)
        delta = random.randint(-scale, scale)
        new_val = max(1, min(20, old + delta))
        new_genes["episodic_retrieval_k"] = new_val
        changes["episodic_retrieval_k"] = {"old": old, "new": new_val}

    if random.random() < rate * 0.6:
        old = new_genes.get("semantic_depth", 3)
        delta = random.choice([-1, 1])
        new_val = max(1, min(8, old + delta))
        new_genes["semantic_depth"] = new_val
        changes["semantic_depth"] = {"old": old, "new": new_val}

    return new_genes, changes


def _mutate_evolution_genes(
    genes: Dict[str, Any], rate: float, intensity: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Mutate the agent's own evolution meta-genes."""
    new_genes = copy.deepcopy(genes)
    changes = {}

    if random.random() < rate * 0.4:
        old = new_genes.get("mutation_rate", 0.1)
        scale = {"mild": 0.01, "medium": 0.03, "strong": 0.06}.get(intensity, 0.02)
        new_val = round(max(0.01, min(0.3, old + random.gauss(0, scale))), 3)
        new_genes["mutation_rate"] = new_val
        changes["mutation_rate"] = {"old": old, "new": new_val}

    return new_genes, changes


# ── Genetic Evolution Engine ──────────────────────────────────
class GeneticEvolutionEngine:
    """
    Full genetic evolution pipeline:
    - Tournament selection with elitism
    - LLM-powered semantic prompt mutation (mild/medium/strong)
    - LLM-powered semantic crossover (fitness-weighted blending)
    - 3-stage hierarchical fitness evaluation
    """

    def __init__(self, llm: AsyncAnthropic):
        self.llm = llm

    # ── Mutation ──────────────────────────────────────────────
    async def mutate_prompt_gene(
        self, system_prompt: str, intensity: str = "medium"
    ) -> str:
        """LLM-powered semantic mutation of a system prompt."""
        mutation_sys = MUTATION_PROMPTS.get(intensity, MUTATION_PROMPTS["medium"])
        try:
            msg = await self.llm.messages.create(
                model=settings.router_model,
                max_tokens=1500,
                system=mutation_sys,
                messages=[{"role": "user", "content": f"Original prompt:\n{system_prompt}"}],
            )
            return msg.content[0].text.strip() if msg.content else system_prompt
        except Exception as e:
            log.warning("evolution.mutate_prompt.failed", error=str(e))
            return system_prompt

    async def mutate_agent(
        self,
        agent: Dict[str, Any],
        intensity: str = "medium",
        target_genes: Optional[List[str]] = None,
    ) -> MutationResult:
        """
        Full agent mutation across all gene types.
        target_genes: which gene groups to mutate (None = all)
        """
        dna = copy.deepcopy(agent.get("dna", {}))
        rate = dna.get("evolution_genes", {}).get("mutation_rate", settings.evolution_default_mutation_rate)
        all_changes: Dict[str, Any] = {}

        genes_to_mutate = target_genes or ["prompt", "parameter", "memory", "evolution"]

        # 1. Prompt gene mutation (LLM-powered)
        if "prompt" in genes_to_mutate and random.random() < rate:
            old_prompt = dna.get("prompt_genes", {}).get("system_prompt", "")
            new_prompt = await self.mutate_prompt_gene(old_prompt, intensity)
            if new_prompt != old_prompt:
                dna.setdefault("prompt_genes", {})["system_prompt"] = new_prompt
                all_changes["system_prompt"] = {
                    "old_length": len(old_prompt),
                    "new_length": len(new_prompt),
                    "intensity": intensity,
                }
            # Mutate reasoning pattern occasionally
            if random.random() < rate * 0.3:
                old_pattern = dna["prompt_genes"].get("reasoning_pattern", "chain-of-thought")
                patterns = ["chain-of-thought", "tree-of-thought", "react", "plan-and-execute"]
                new_pattern = random.choice([p for p in patterns if p != old_pattern])
                dna["prompt_genes"]["reasoning_pattern"] = new_pattern
                all_changes["reasoning_pattern"] = {"old": old_pattern, "new": new_pattern}

        # 2. Parameter gene mutation
        if "parameter" in genes_to_mutate:
            new_params, param_changes = _mutate_parameter_genes(
                dna.get("parameter_genes", {}), rate, intensity
            )
            if param_changes:
                dna["parameter_genes"] = new_params
                all_changes["parameter_genes"] = param_changes

        # 3. Memory gene mutation
        if "memory" in genes_to_mutate:
            new_mem, mem_changes = _mutate_memory_genes(
                dna.get("memory_genes", {}), rate, intensity
            )
            if mem_changes:
                dna["memory_genes"] = new_mem
                all_changes["memory_genes"] = mem_changes

        # 4. Evolution gene mutation (meta-evolution)
        if "evolution" in genes_to_mutate:
            new_evo, evo_changes = _mutate_evolution_genes(
                dna.get("evolution_genes", {}), rate, intensity
            )
            if evo_changes:
                dna["evolution_genes"] = new_evo
                all_changes["evolution_genes"] = evo_changes

        return MutationResult(
            agent_id=str(agent["id"]),
            original_fitness=agent.get("fitness_score", 0.5),
            new_dna=dna,
            changes=all_changes,
            intensity=intensity,
        )

    # ── Crossover ─────────────────────────────────────────────
    async def crossover(
        self, parent_a: Dict[str, Any], parent_b: Dict[str, Any]
    ) -> CrossoverResult:
        """
        LLM-powered semantic crossover between two parent agents.
        Fitness-weighted gene inheritance.
        """
        fit_a = parent_a.get("fitness_score", 0.5)
        fit_b = parent_b.get("fitness_score", 0.5)
        total = fit_a + fit_b if (fit_a + fit_b) > 0 else 1.0
        weight_a = fit_a / total  # Parent A's relative contribution

        dna_a = parent_a.get("dna", {})
        dna_b = parent_b.get("dna", {})
        child_dna: Dict[str, Any] = {}

        # 1. Prompt crossover (LLM-powered semantic blend)
        prompt_a = dna_a.get("prompt_genes", {}).get("system_prompt", "")
        prompt_b = dna_b.get("prompt_genes", {}).get("system_prompt", "")
        try:
            msg = await self.llm.messages.create(
                model=settings.router_model,
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": CROSSOVER_PROMPT.format(
                        fit_a=fit_a, fit_b=fit_b,
                        prompt_a=prompt_a, prompt_b=prompt_b
                    )
                }],
            )
            child_prompt = msg.content[0].text.strip() if msg.content else prompt_a
        except Exception:
            child_prompt = prompt_a if weight_a >= 0.5 else prompt_b

        # Inherit reasoning pattern from higher-fitness parent
        pattern = (
            dna_a.get("prompt_genes", {}).get("reasoning_pattern", "chain-of-thought")
            if weight_a >= 0.5
            else dna_b.get("prompt_genes", {}).get("reasoning_pattern", "chain-of-thought")
        )

        child_dna["prompt_genes"] = {
            **dna_a.get("prompt_genes", {}),
            "system_prompt": child_prompt,
            "reasoning_pattern": pattern,
        }

        # 2. Parameter crossover (fitness-weighted interpolation)
        params_a = dna_a.get("parameter_genes", {})
        params_b = dna_b.get("parameter_genes", {})
        child_dna["parameter_genes"] = {
            "temperature": round(
                params_a.get("temperature", 0.3) * weight_a +
                params_b.get("temperature", 0.3) * (1 - weight_a), 3
            ),
            "max_tokens": int(
                params_a.get("max_tokens", 2048) * weight_a +
                params_b.get("max_tokens", 2048) * (1 - weight_a)
            ),
            "reasoning_effort": (
                params_a.get("reasoning_effort", "medium")
                if weight_a >= 0.5
                else params_b.get("reasoning_effort", "medium")
            ),
        }

        # 3. Memory crossover (arithmetic blend)
        mem_a = dna_a.get("memory_genes", {})
        mem_b = dna_b.get("memory_genes", {})
        child_dna["memory_genes"] = {
            "working_memory_size": round(
                mem_a.get("working_memory_size", 10) * weight_a +
                mem_b.get("working_memory_size", 10) * (1 - weight_a)
            ),
            "episodic_retrieval_k": round(
                mem_a.get("episodic_retrieval_k", 5) * weight_a +
                mem_b.get("episodic_retrieval_k", 5) * (1 - weight_a)
            ),
            "semantic_depth": round(
                mem_a.get("semantic_depth", 3) * weight_a +
                mem_b.get("semantic_depth", 3) * (1 - weight_a)
            ),
            "consolidation_frequency": round(
                mem_a.get("consolidation_frequency", 100) * weight_a +
                mem_b.get("consolidation_frequency", 100) * (1 - weight_a)
            ),
        }

        # 4. Tool genes from fitter parent
        child_dna["tool_genes"] = (
            dna_a.get("tool_genes", {}) if weight_a >= 0.5
            else dna_b.get("tool_genes", {})
        )

        # 5. Evolution genes (blend mutation rates)
        evo_a = dna_a.get("evolution_genes", {})
        evo_b = dna_b.get("evolution_genes", {})
        child_dna["evolution_genes"] = {
            "mutation_rate": round(
                evo_a.get("mutation_rate", 0.1) * weight_a +
                evo_b.get("mutation_rate", 0.1) * (1 - weight_a), 3
            ),
            "fitness_weights": evo_a.get("fitness_weights", {}) if weight_a >= 0.5 else evo_b.get("fitness_weights", {}),
            "crossover_enabled": True,
        }

        return CrossoverResult(
            parent_a_id=str(parent_a["id"]),
            parent_b_id=str(parent_b["id"]),
            new_dna=child_dna,
            parent_a_fitness=fit_a,
            parent_b_fitness=fit_b,
        )

    # ── Fitness Evaluation ────────────────────────────────────
    async def evaluate_fitness_stage1(
        self, agent: Dict[str, Any], task_history: List[Dict[str, Any]]
    ) -> FitnessEvaluation:
        """
        Stage 1: LLM judge evaluates agent based on recent task history.
        Scores across: response quality, reasoning clarity, task completion.
        """
        if not task_history:
            return FitnessEvaluation(
                agent_id=str(agent["id"]),
                fitness_score=agent.get("fitness_score", 0.5),
                components={"history": 0.0},
                stage=1,
                task_count=0,
            )

        # Sample up to 3 recent tasks for evaluation
        sample = task_history[-3:]
        task_summary = "\n\n".join([
            f"Task: {t.get('task_description','')[:200]}\n"
            f"Output: {(t.get('output') or {}).get('response','')[:300]}\n"
            f"Latency: {t.get('latency_ms',0)}ms | Tokens: {t.get('tokens_output',0)}"
            for t in sample
        ])

        eval_prompt = f"""Evaluate this AI agent's performance on recent tasks. Score 0.0-1.0.

Agent type: {agent.get('type','unknown')}
Agent generation: {agent.get('generation',1)}

Recent task performance:
{task_summary}

Return ONLY valid JSON:
{{
  "overall": 0.0-1.0,
  "response_quality": 0.0-1.0,
  "reasoning_clarity": 0.0-1.0,
  "task_completion": 0.0-1.0,
  "efficiency": 0.0-1.0,
  "rationale": "one sentence"
}}"""

        try:
            msg = await self.llm.messages.create(
                model=settings.router_model,
                max_tokens=300,
                messages=[{"role": "user", "content": eval_prompt}],
            )
            text = msg.content[0].text.strip() if msg.content else "{}"
            import re
            json_match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
            scores = json.loads(json_match.group()) if json_match else {}

            overall = float(scores.get("overall", 0.5))
            components = {
                "response_quality": float(scores.get("response_quality", 0.5)),
                "reasoning_clarity": float(scores.get("reasoning_clarity", 0.5)),
                "task_completion": float(scores.get("task_completion", 0.5)),
                "efficiency": float(scores.get("efficiency", 0.5)),
            }
        except Exception as e:
            log.warning("fitness.stage1.failed", error=str(e))
            # Fall back to heuristic from task metrics
            avg_latency = sum(t.get("latency_ms", 5000) for t in sample) / len(sample)
            latency_score = max(0.1, 1.0 - avg_latency / 30000)
            token_score = min(1.0, sum(t.get("tokens_output", 0) for t in sample) / (len(sample) * 600))
            overall = 0.5 * latency_score + 0.5 * token_score
            components = {"latency": latency_score, "token_efficiency": token_score}

        return FitnessEvaluation(
            agent_id=str(agent["id"]),
            fitness_score=round(overall, 4),
            components=components,
            stage=1,
            task_count=len(task_history),
        )

    async def evaluate_fitness_stage2(
        self,
        agent: Dict[str, Any],
        stage1_score: float,
        benchmark_tasks: Optional[List[str]] = None,
        llm: Optional[AsyncAnthropic] = None,
    ) -> FitnessEvaluation:
        """
        Stage 2: Sandbox simulation — run agent on benchmark tasks and score output.
        Uses lightweight tasks to avoid token cost explosion.
        """
        if llm is None:
            llm = self.llm

        benchmarks = benchmark_tasks or _get_benchmark_tasks(agent.get("type", "research"))

        scores = []
        for bench_task in benchmarks[:2]:  # Limit to 2 for cost
            try:
                dna = agent.get("dna", {})
                system = dna.get("prompt_genes", {}).get("system_prompt", "You are a helpful assistant.")
                params = dna.get("parameter_genes", {})

                msg = await llm.messages.create(
                    model=settings.router_model,  # Use cheaper model for sandbox
                    max_tokens=min(params.get("max_tokens", 512), 512),
                    system=system,
                    messages=[{"role": "user", "content": bench_task["task"]}],
                )
                response = msg.content[0].text if msg.content else ""

                # Score against expected criteria
                criteria = bench_task.get("criteria", [])
                criteria_score = sum(
                    1 for c in criteria
                    if c.lower() in response.lower()
                ) / max(1, len(criteria))

                length_score = min(1.0, len(response) / bench_task.get("min_length", 200))
                scores.append(0.6 * criteria_score + 0.4 * length_score)
            except Exception as e:
                log.warning("fitness.stage2.task.failed", error=str(e))
                scores.append(0.3)

        stage2_score = sum(scores) / max(1, len(scores)) if scores else 0.5
        # Weighted blend: 40% stage1 (LLM judge) + 60% stage2 (sandbox)
        combined = 0.4 * stage1_score + 0.6 * stage2_score

        return FitnessEvaluation(
            agent_id=str(agent["id"]),
            fitness_score=round(combined, 4),
            components={
                "stage1_llm_judge": stage1_score,
                "stage2_sandbox": stage2_score,
                "benchmark_tasks": len(scores),
            },
            stage=2,
            task_count=len(scores),
        )

    # ── Selection ─────────────────────────────────────────────
    def tournament_selection(
        self,
        agents: List[Dict[str, Any]],
        tournament_size: int = 3,
        n_select: int = 2,
    ) -> List[Dict[str, Any]]:
        """Tournament selection: randomly sample k agents, keep the fittest."""
        selected = []
        available = agents.copy()

        for _ in range(n_select):
            if not available:
                break
            tournament = random.sample(available, min(tournament_size, len(available)))
            winner = max(tournament, key=lambda a: a.get("fitness_score", 0))
            selected.append(winner)
            available = [a for a in available if str(a.get("id")) != str(winner.get("id"))]

        return selected

    def select_elites(
        self, agents: List[Dict[str, Any]], n: int = 2
    ) -> List[Dict[str, Any]]:
        """Elitism: always preserve the top N agents unchanged."""
        return sorted(agents, key=lambda a: a.get("fitness_score", 0), reverse=True)[:n]

    def compute_population_diversity(self, agents: List[Dict[str, Any]]) -> float:
        """
        Measure population diversity via fitness variance.
        Low diversity → risk of premature convergence.
        """
        if len(agents) < 2:
            return 1.0
        fitnesses = [a.get("fitness_score", 0.5) for a in agents]
        mean = sum(fitnesses) / len(fitnesses)
        variance = sum((f - mean) ** 2 for f in fitnesses) / len(fitnesses)
        std = math.sqrt(variance)
        # Normalize: std of 0.2+ = high diversity (1.0), std of 0 = no diversity (0.0)
        return min(1.0, std / 0.2)

    # ── Full Evolution Cycle ──────────────────────────────────
    async def run_generation(
        self,
        agents: List[Dict[str, Any]],
        task_history_by_agent: Dict[str, List[Dict[str, Any]]],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a complete generation cycle across the agent population.
        Returns updated agents + evolution stats.
        """
        cfg = config or {}
        elitism_count = cfg.get("elitism_count", settings.evolution_elitism_count)
        selection_pressure = cfg.get("selection_pressure", settings.evolution_selection_pressure)
        strategy = cfg.get("strategy", "full")

        events: List[Dict[str, Any]] = []
        new_agents: List[Dict[str, Any]] = []

        # Phase 1: Evaluate fitness for all agents
        log.info("evolution.generation.start", n_agents=len(agents))
        for agent in agents:
            task_history = task_history_by_agent.get(str(agent.get("id")), [])
            eval_result = await self.evaluate_fitness_stage1(agent, task_history)
            agent["fitness_score"] = eval_result.fitness_score
            events.append({
                "event_type": "evaluation",
                "agent_id": str(agent.get("id")),
                "new_fitness": eval_result.fitness_score,
                "components": eval_result.components,
            })

        # Phase 2: Preserve elites
        elites = self.select_elites(agents, n=elitism_count)
        for elite in elites:
            updated = copy.deepcopy(elite)
            updated["generation"] = elite.get("generation", 1) + 1
            new_agents.append(updated)
            events.append({
                "event_type": "selection",
                "agent_id": str(elite.get("id")),
                "old_fitness": elite.get("fitness_score"),
                "new_fitness": elite.get("fitness_score"),
                "changes": {"elite": True},
            })

        # Phase 3: Produce offspring for non-elites
        non_elites = [a for a in agents if str(a.get("id")) not in {str(e.get("id")) for e in elites}]
        mutations_applied = 0
        crossovers_applied = 0

        for agent in non_elites:
            roll = random.random()

            if strategy == "mutation_only" or roll < 0.4:
                # Mutation
                intensity = (
                    "mild" if agent.get("fitness_score", 0.5) > 0.75 else
                    "medium" if agent.get("fitness_score", 0.5) > 0.5 else
                    "strong"
                )
                try:
                    mut_result = await self.mutate_agent(agent, intensity=intensity)
                    child = copy.deepcopy(agent)
                    child["id"] = uuid.uuid4()
                    child["dna"] = mut_result.new_dna
                    child["generation"] = agent.get("generation", 1) + 1
                    child["parent_ids"] = [agent.get("id")]
                    child["fitness_score"] = agent.get("fitness_score", 0.5) * random.uniform(0.95, 1.08)
                    child["fitness_score"] = min(0.99, max(0.01, child["fitness_score"]))
                    new_agents.append(child)
                    mutations_applied += 1
                    events.append({
                        "event_type": "mutation",
                        "parent_ids": [str(agent.get("id"))],
                        "child_id": str(child["id"]),
                        "old_fitness": agent.get("fitness_score"),
                        "new_fitness": child["fitness_score"],
                        "changes": mut_result.changes,
                        "intensity": intensity,
                    })
                except Exception as e:
                    log.warning("evolution.mutation.failed", error=str(e))
                    new_agents.append(agent)

            elif strategy != "mutation_only" and roll >= 0.4 and len(elites) >= 1:
                # Crossover with an elite
                parent_b = random.choice(elites)
                try:
                    xo_result = await self.crossover(agent, parent_b)
                    child = copy.deepcopy(agent)
                    child["id"] = uuid.uuid4()
                    child["dna"] = xo_result.new_dna
                    child["generation"] = max(agent.get("generation", 1), parent_b.get("generation", 1)) + 1
                    child["parent_ids"] = [agent.get("id"), parent_b.get("id")]
                    # Expected fitness between parents, slight improvement
                    expected = (xo_result.parent_a_fitness + xo_result.parent_b_fitness) / 2
                    child["fitness_score"] = min(0.99, expected * random.uniform(0.98, 1.1))
                    new_agents.append(child)
                    crossovers_applied += 1
                    events.append({
                        "event_type": "crossover",
                        "parent_ids": [str(agent.get("id")), str(parent_b.get("id"))],
                        "child_id": str(child["id"]),
                        "old_fitness": agent.get("fitness_score"),
                        "new_fitness": child["fitness_score"],
                        "changes": {
                            "parent_a_fitness": xo_result.parent_a_fitness,
                            "parent_b_fitness": xo_result.parent_b_fitness,
                        },
                    })
                except Exception as e:
                    log.warning("evolution.crossover.failed", error=str(e))
                    new_agents.append(agent)

        # Phase 4: Compute population stats
        fitnesses = [a.get("fitness_score", 0.5) for a in new_agents]
        diversity = self.compute_population_diversity(new_agents)
        avg_fit = sum(fitnesses) / max(1, len(fitnesses))
        max_fit = max(fitnesses) if fitnesses else 0
        min_fit = min(fitnesses) if fitnesses else 0
        variance = sum((f - avg_fit) ** 2 for f in fitnesses) / max(1, len(fitnesses))

        log.info("evolution.generation.complete",
            n_new=len(new_agents), mutations=mutations_applied,
            crossovers=crossovers_applied, avg_fitness=avg_fit, diversity=diversity
        )

        return {
            "new_agents": new_agents,
            "events": events,
            "stats": {
                "avg_fitness": round(avg_fit, 4),
                "max_fitness": round(max_fit, 4),
                "min_fitness": round(min_fit, 4),
                "std_fitness": round(math.sqrt(variance), 4),
                "diversity_score": round(diversity, 4),
                "mutations_applied": mutations_applied,
                "crossovers_applied": crossovers_applied,
                "selections_performed": len(elites),
                "new_agents_created": len(new_agents),
                "agents_retired": len(agents) - len(new_agents),
                "population_size": len(new_agents),
            },
        }


# ── Benchmark Tasks per Agent Type ───────────────────────────
def _get_benchmark_tasks(agent_type: str) -> List[Dict[str, Any]]:
    benchmarks = {
        "research": [
            {
                "task": "What are the three main differences between supervised and unsupervised learning?",
                "criteria": ["supervised", "unsupervised", "labeled", "clustering"],
                "min_length": 150,
            },
            {
                "task": "Summarize the key benefits of microservices architecture in 3 bullet points.",
                "criteria": ["scalability", "deployment", "service", "independent"],
                "min_length": 100,
            },
        ],
        "code": [
            {
                "task": "Write a Python function to find all prime numbers up to n using the Sieve of Eratosthenes.",
                "criteria": ["def ", "sieve", "prime", "return", "range"],
                "min_length": 100,
            },
            {
                "task": "Write a TypeScript interface and class for a Queue data structure with enqueue, dequeue, peek methods.",
                "criteria": ["interface", "class", "enqueue", "dequeue", "peek"],
                "min_length": 150,
            },
        ],
        "analysis": [
            {
                "task": "Analyze the trade-offs between relational and NoSQL databases for a high-traffic e-commerce platform.",
                "criteria": ["ACID", "scalability", "schema", "consistency", "trade-off"],
                "min_length": 200,
            },
        ],
        "creative": [
            {
                "task": "Write a 100-word product description for an AI-powered coffee maker that learns your preferences.",
                "criteria": ["AI", "personalized", "coffee", "smart", "learns"],
                "min_length": 80,
            },
        ],
        "skill_builder": [
            {
                "task": "Design a skill specification for an agent that can extract structured data from PDF invoices. Include inputs, outputs, and steps.",
                "criteria": ["input", "output", "step", "PDF", "extract"],
                "min_length": 200,
            },
        ],
        "router": [
            {
                "task": 'Route this task to the correct agent: "Write a Python script to analyze sales data from a CSV file." Return JSON only: {"selectedAgent":"type","reasoning":"...","confidence":0.0}',
                "criteria": ["code", "analysis", "selectedAgent"],
                "min_length": 50,
            },
        ],
    }
    return benchmarks.get(agent_type, benchmarks["research"])
