# GENESIS AI PLATFORM — Genetic Evolution Engine
## Deep Technical Design for Semantic Genetic Algorithms

**Version:** 1.0  
**Date:** April 2026  
**Classification:** Technical Deep Dive  
**Related Documents:** 01_MASTER_PROJECT_PLAN.md, 02_SYSTEM_ARCHITECTURE.md

---

## 1. EVOLUTION ENGINE OVERVIEW

### 1.1 Design Philosophy

The Genetic Evolution Engine is the **heart of GENESIS** — the component that transforms static agents into a living, adapting population. Unlike traditional genetic algorithms that operate on bit strings, GENESIS uses **semantic genetic algorithms** inspired by the **Artemis platform** (TurinTech AI, 2025).

**Key Innovation:** LLM-powered genetic operators that maintain semantic validity throughout evolution. Instead of randomly flipping bits, we use language models to intelligently mutate prompts, blend capabilities, and evaluate fitness.

### 1.2 Why Genetic Algorithms for Agents?

Based on Artemis research results:

| Agent System | Metric | Baseline | Optimized | Improvement |
|-------------|--------|----------|-----------|-------------|
| ALE Agent (Competitive Programming) | Acceptance Rate | 66.0% | 75.0% | **+13.6%** |
| Mini-SWE Agent (Code Optimization) | Performance Score | - | - | **+10.1%** (p<0.05) |
| CrewAI Agent (Math Reasoning) | Token Cost | 100% | 63.1% | **-36.9%** |
| MathTales Agent (Small Model) | Accuracy | Baseline | - | **+22%** |

**Key Advantage:** No architectural changes required — works as black-box optimization.

### 1.3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      GENETIC EVOLUTION ENGINE                                    │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  EVOLUTION CONTROLLER                                                   │   │
│   │  ├── Trigger: Every N tasks / Time-based / Manual                       │   │
│   │  ├── Population Manager: Size, diversity, elitism                       │   │
│   │  └── Generation Tracker: Lineage, statistics                            │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                            │
│         ┌───────────────────────────┼───────────────────────────┐                │
│         ▼                           ▼                           ▼                │
│   ┌──────────┐               ┌──────────┐               ┌──────────┐          │
│   │SELECTION │               │ MUTATION │               │ CROSSOVER│          │
│   │          │               │          │               │          │          │
│   │Tournament│               │LLM-based │               │Semantic  │          │
│   │+ Elitism │               │Semantic  │               │Blending  │          │
│   │          │               │          │               │          │          │
│   │ Input:   │               │ Input:   │               │ Input:   │          │
│   │ Population│              │ Agent DNA│               │ 2 Parent │          │
│   │          │               │          │               │ DNAs     │          │
│   │ Output:  │               │ Output:  │               │ Output:  │          │
│   │ Parents  │               │ Mutated  │               │ Child    │          │
│   │          │               │ DNA      │               │ DNA      │          │
│   └──────────┘               └──────────┘               └──────────┘          │
│         │                           │                           │                │
│         └───────────────────────────┼───────────────────────────┘                │
│                                     ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  FITNESS EVALUATION (Hierarchical)                                       │   │
│   │  Stage 1: LLM Scoring (cheap, fast) → Filter poor candidates            │   │
│   │  Stage 2: Simulation (medium) → Validate behavior                       │   │
│   │  Stage 3: Full Benchmark (expensive) → Final fitness                    │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                     │                                            │
│                                     ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  LIFECYCLE MANAGER                                                       │   │
│   │  ├── Sandbox Validation: Syntax, behavior, safety checks                │   │
│   │  ├── Gradual Deployment: 10% → 50% → 100% rollout                     │   │
│   │  └── Rollback: Automatic if fitness drops                               │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. AGENT DNA (GENOTYPE) SPECIFICATION

### 2.1 DNA Structure

The genotype is the complete encodable configuration of an agent. Every parameter that can be evolved is part of the DNA.

```python
# genesis/evolution/dna.py
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import hashlib
import json
import random

@dataclass
class PromptGenes:
    """Genes controlling agent behavior and personality"""
    system_prompt: str = "You are a helpful AI agent."
    reasoning_pattern: str = "chain-of-thought"  # chain-of-thought, tree-of-thought, react, plan-and-execute
    self_correction_enabled: bool = True
    self_correction_prompt: str = "Review your answer for errors. If found, correct them."
    verbosity: float = 0.5  # 0=concise, 1=detailed
    tone: str = "professional"  # professional, casual, technical, friendly
    language_style: str = "clear"  # clear, academic, simple, creative
    
    # Task-specific prompt extensions
    task_prefixes: Dict[str, str] = field(default_factory=dict)
    task_suffixes: Dict[str, str] = field(default_factory=dict)

@dataclass
class ParameterGenes:
    """Genes controlling LLM parameters"""
    temperature: float = 0.3
    max_tokens: int = 2048
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    reasoning_effort: str = "medium"  # low, medium, high
    
    # Dynamic parameter adjustment
    adaptive_temperature: bool = True  # Adjust based on task complexity
    temperature_range: tuple = (0.1, 0.8)  # Min/max adaptive range

@dataclass
class ToolGenes:
    """Genes controlling tool selection and usage"""
    available_tools: List[str] = field(default_factory=list)
    tool_selection_strategy: str = "relevance-based"  # relevance-based, all, round-robin
    max_tools_per_task: int = 5
    tool_timeout_seconds: int = 30
    tool_retry_count: int = 2
    parallel_tool_execution: bool = False
    
    # Tool preference weights (higher = preferred)
    tool_weights: Dict[str, float] = field(default_factory=dict)

@dataclass
class MemoryGenes:
    """Genes controlling memory behavior"""
    working_memory_size: int = 10  # Number of items in working memory
    episodic_retrieval_k: int = 5  # Number of episodic memories to retrieve
    semantic_depth: int = 3  # Graph traversal depth
    consolidation_frequency: int = 100  # Episodes between consolidation
    importance_threshold: float = 0.6  # Minimum importance to store
    recency_weight: float = 0.3
    relevance_weight: float = 0.5
    importance_weight: float = 0.2

@dataclass
class EvolutionGenes:
    """Meta-genes controlling how this agent evolves"""
    mutation_rate: float = 0.1
    crossover_fitness_threshold: float = 0.6  # Minimum fitness to be selected for crossover
    elitism_preference: bool = True
    exploration_vs_exploitation: float = 0.5  # 0=exploit, 1=explore
    
    # Fitness function weights
    fitness_weights: Dict[str, float] = field(default_factory=lambda: {
        "accuracy": 0.4,
        "efficiency": 0.3,
        "adaptability": 0.2,
        "diversity": 0.1
    })

@dataclass
class AgentDNA:
    """
    Complete genetic encoding of an agent.
    
    This is the genotype that gets:
    - Mutated during evolution
    - Crossed over with other agents
    - Evaluated for fitness
    - Stored for lineage tracking
    """
    
    # Metadata
    dna_version: str = "1.0"
    agent_type: str = "research"
    generation: int = 1
    lineage: List[str] = field(default_factory=list)  # Ancestor IDs
    
    # Core gene groups
    prompt_genes: PromptGenes = field(default_factory=PromptGenes)
    parameter_genes: ParameterGenes = field(default_factory=ParameterGenes)
    tool_genes: ToolGenes = field(default_factory=ToolGenes)
    memory_genes: MemoryGenes = field(default_factory=MemoryGenes)
    evolution_genes: EvolutionGenes = field(default_factory=EvolutionGenes)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def hash(self) -> str:
        """Unique hash of this DNA configuration"""
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True).encode()
        ).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AgentDNA":
        """Create from dictionary"""
        return cls(
            dna_version=data.get("dna_version", "1.0"),
            agent_type=data.get("agent_type", "research"),
            generation=data.get("generation", 1),
            lineage=data.get("lineage", []),
            prompt_genes=PromptGenes(**data.get("prompt_genes", {})),
            parameter_genes=ParameterGenes(**data.get("parameter_genes", {})),
            tool_genes=ToolGenes(**data.get("tool_genes", {})),
            memory_genes=MemoryGenes(**data.get("memory_genes", {})),
            evolution_genes=EvolutionGenes(**data.get("evolution_genes", {}))
        )
    
    def mutate_gene(self, gene_path: str, new_value: Any) -> "AgentDNA":
        """
        Create a new DNA with a specific gene mutated.
        
        gene_path format: "prompt_genes.system_prompt"
        """
        new_dna = self.from_dict(self.to_dict())
        
        parts = gene_path.split(".")
        target = new_dna
        for part in parts[:-1]:
            target = getattr(target, part)
        setattr(target, parts[-1], new_value)
        
        return new_dna
```

### 2.2 DNA Encoding Visualization

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          AGENT DNA ENCODING                                      │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ METADATA GENES                                                           │   │
│  │ dna_version:      "1.0"                                                  │   │
│  │ agent_type:       "research" | "code" | "analysis" | "creative"           │   │
│  │ generation:       5                                                      │   │
│  │ lineage:          ["uuid-g1", "uuid-g3", "uuid-g4"]                      │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ PROMPT GENES                                                             │   │
│  │ system_prompt:    "You are an expert research agent..."                  │   │
│  │ reasoning:        "chain-of-thought" | "tree-of-thought" | "react"       │   │
│  │ self_correction:  true | false                                           │   │
│  │ verbosity:        0.0 ──────────────────────────────► 1.0               │   │
│  │                   concise                           detailed             │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ PARAMETER GENES                                                          │   │
│  │ temperature:      0.1 ─────┬───── 0.5 ─────┬───── 0.9                  │   │
│  │                   focused   │    balanced   │    creative                │   │
│  │ max_tokens:       256 ─────┼───── 2048 ────┼───── 8192                  │   │
│  │ reasoning_effort: "low"    │    "medium"   │    "high"                   │   │
│  │ adaptive_temp:    true | false                                           │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ TOOL GENES                                                               │   │
│  │ available_tools:  ["web_search", "pdf_reader", "data_extractor"]         │   │
│  │ selection:        "relevance" | "all" | "round-robin"                    │   │
│  │ max_per_task:     1 ───── 3 ───── 5 ───── 10                             │   │
│  │ parallel:         true | false                                           │   │
│  │ tool_weights:     {"web_search": 1.5, "pdf_reader": 1.0}                 │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ MEMORY GENES                                                             │   │
│  │ working_size:     5 ───── 10 ───── 20                                    │   │
│  │ episodic_k:       3 ───── 5 ───── 10                                     │   │
│  │ semantic_depth:   1 ───── 3 ───── 5                                      │   │
│  │ importance_threshold: 0.3 ─── 0.6 ─── 0.9                                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ EVOLUTION GENES (Meta)                                                   │   │
│  │ mutation_rate:    0.05 ─── 0.1 ─── 0.3                                  │   │
│  │                   conservative  balanced  aggressive                      │   │
│  │ fitness_weights:  {"accuracy": 0.4, "efficiency": 0.3,                   │   │
│  │                    "adaptability": 0.2, "diversity": 0.1}                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. SELECTION OPERATORS

### 3.1 Tournament Selection with Elitism

The primary selection method, combining competitive selection with preservation of top performers.

```python
# genesis/evolution/selection.py
from dataclasses import dataclass
from typing import List, Optional, Callable
import random
import numpy as np

@dataclass
class SelectionConfig:
    """Configuration for selection operators"""
    tournament_size: int = 3
    elitism_count: int = 2
    selection_pressure: float = 0.7  # 0=random, 1=always pick best
    diversity_weight: float = 0.2  # Weight for diversity in selection

class TournamentSelection:
    """
    Tournament selection with elitism.
    
    Process:
    1. Preserve top N elites unchanged
    2. Run tournaments to select remaining parents
    3. Optionally consider genetic diversity
    """
    
    def __init__(self, config: SelectionConfig = None):
        self.config = config or SelectionConfig()
    
    def select(
        self,
        population: List["Agent"],
        num_parents: int
    ) -> List["Agent"]:
        """
        Select parents for reproduction.
        
        Returns:
            List of selected agents (may include duplicates for fit agents)
        """
        if len(population) < self.config.tournament_size:
            return population
        
        # Sort by fitness
        sorted_pop = sorted(population, key=lambda a: a.fitness_score, reverse=True)
        
        parents = []
        
        # Step 1: Elitism - preserve top performers
        elites = sorted_pop[:self.config.elitism_count]
        parents.extend(elites)
        
        # Step 2: Tournament selection for remaining
        remaining = num_parents - len(elites)
        
        for _ in range(remaining):
            # Select tournament participants
            tournament = random.sample(population, self.config.tournament_size)
            
            # Select winner with probability based on fitness
            winner = self._select_winner(tournament)
            parents.append(winner)
        
        return parents
    
    def _select_winner(self, tournament: List["Agent"]) -> "Agent":
        """
        Select winner from tournament.
        
        With selection_pressure=0.7:
        - 70% chance: pick the best
        - 30% chance: pick randomly (exploration)
        """
        if random.random() < self.config.selection_pressure:
            # Select best
            return max(tournament, key=lambda a: a.fitness_score)
        else:
            # Select randomly (exploration)
            return random.choice(tournament)
    
    def select_diverse(
        self,
        population: List["Agent"],
        num_parents: int
    ) -> List["Agent"]:
        """
        Selection that explicitly maintains diversity.
        
        Uses genetic distance (hamming distance on DNA hash)
        to avoid premature convergence.
        """
        sorted_pop = sorted(population, key=lambda a: a.fitness_score, reverse=True)
        
        parents = []
        elites = sorted_pop[:self.config.elitism_count]
        parents.extend(elites)
        
        remaining = num_parents - len(elites)
        
        for _ in range(remaining):
            tournament = random.sample(population, self.config.tournament_size)
            
            # Score = fitness + diversity_bonus
            def diversity_score(agent):
                # Calculate average DNA distance to already selected parents
                if not parents:
                    return agent.fitness_score
                
                distances = [self._dna_distance(agent, p) for p in parents]
                avg_distance = sum(distances) / len(distances)
                
                # Normalize distance to 0-1
                normalized_distance = min(avg_distance / 10, 1.0)
                
                return (
                    agent.fitness_score * (1 - self.config.diversity_weight) +
                    normalized_distance * self.config.diversity_weight
                )
            
            winner = max(tournament, key=diversity_score)
            parents.append(winner)
        
        return parents
    
    def _dna_distance(self, agent1: "Agent", agent2: "Agent") -> float:
        """
        Calculate genetic distance between two agents.
        
        Uses number of differing gene values.
        """
        dna1 = agent1.dna.to_dict()
        dna2 = agent2.dna.to_dict()
        
        differences = 0
        total_genes = 0
        
        def compare(obj1, obj2, path=""):
            nonlocal differences, total_genes
            
            if isinstance(obj1, dict) and isinstance(obj2, dict):
                all_keys = set(obj1.keys()) | set(obj2.keys())
                for key in all_keys:
                    compare(
                        obj1.get(key),
                        obj2.get(key),
                        f"{path}.{key}"
                    )
            elif isinstance(obj1, (int, float, str, bool)):
                total_genes += 1
                if obj1 != obj2:
                    differences += 1
        
        compare(dna1, dna2)
        return differences / max(total_genes, 1)
```

### 3.2 Fitness-Proportionate Selection (Alternative)

```python
class FitnessProportionateSelection:
    """
    Roulette wheel selection.
    Probability of selection proportional to fitness.
    """
    
    def select(self, population: List["Agent"], num_parents: int) -> List["Agent"]:
        """Select parents with probability proportional to fitness"""
        
        # Calculate selection probabilities
        fitnesses = [a.fitness_score for a in population]
        min_fitness = min(fitnesses)
        
        # Shift to positive (in case of negative fitness)
        adjusted = [f - min_fitness + 0.01 for f in fitnesses]
        total = sum(adjusted)
        probabilities = [a / total for a in adjusted]
        
        # Select
        selected_indices = np.random.choice(
            len(population),
            size=num_parents,
            p=probabilities,
            replace=True
        )
        
        return [population[i] for i in selected_indices]
```

---

## 4. MUTATION OPERATORS

### 4.1 LLM-Powered Semantic Mutation

The crown jewel of the GENESIS evolution engine. Unlike traditional GAs that flip bits, we use LLMs to intelligently mutate prompts while preserving semantic validity.

```python
# genesis/evolution/mutation.py
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import random
import json

@dataclass
class MutationConfig:
    """Configuration for mutation operators"""
    prompt_mutation_model: str = "gpt-5.4-mini"  # Fast model for mutations
    max_mutation_strength: float = 0.5
    gene_mutation_probabilities: Dict[str, float] = None
    
    def __post_init__(self):
        if self.gene_mutation_probabilities is None:
            self.gene_mutation_probabilities = {
                "prompt_genes.system_prompt": 0.3,
                "prompt_genes.reasoning_pattern": 0.1,
                "prompt_genes.self_correction_enabled": 0.05,
                "prompt_genes.verbosity": 0.15,
                "parameter_genes.temperature": 0.2,
                "parameter_genes.max_tokens": 0.1,
                "parameter_genes.reasoning_effort": 0.1,
                "tool_genes.available_tools": 0.1,
                "tool_genes.max_tools_per_task": 0.1,
                "memory_genes.working_memory_size": 0.1,
                "memory_genes.episodic_retrieval_k": 0.1,
                "evolution_genes.mutation_rate": 0.05,
            }

class SemanticMutator:
    """
    LLM-powered semantic mutation.
    
    Inspired by Artemis platform's semantic genetic algorithms.
    Key insight: LLMs can mutate natural language while preserving meaning.
    """
    
    # Mutation prompts for different strengths
    MILD_MUTATION_PROMPT = """
    Make MINOR improvements to the following system prompt.
    
    Guidelines:
    - Keep the core approach unchanged
    - Add 1-2 specific examples or clarifications
    - Improve wording for clarity
    - Do NOT change the fundamental strategy
    
    Original prompt:
    {prompt}
    
    Return ONLY the improved prompt, no explanations.
    """
    
    MEDIUM_MUTATION_PROMPT = """
    Create a MODERATE variation of the following system prompt.
    
    Guidelines:
    - Restructure the instructions
    - Add new constraints or requirements
    - Change the approach slightly (e.g., add verification step)
    - Keep the same overall goal
    
    Original prompt:
    {prompt}
    
    Return ONLY the new prompt, no explanations.
    """
    
    STRONG_MUTATION_PROMPT = """
    Create a SIGNIFICANTLY DIFFERENT version of the following system prompt.
    
    Guidelines:
    - Take a different approach to the same problem
    - Add entirely new strategies or techniques
    - Change the tone or style
    - The goal remains the same, but the method changes
    
    Original prompt:
    {prompt}
    
    Return ONLY the new prompt, no explanations.
    """
    
    def __init__(self, config: MutationConfig = None):
        self.config = config or MutationConfig()
    
    async def mutate(self, agent: "Agent") -> "Agent":
        """
        Apply semantic mutation to an agent's DNA.
        
        Process:
        1. Decide which genes to mutate based on probabilities
        2. Apply appropriate mutation to each selected gene
        3. Return new agent with mutated DNA
        """
        from genesis.llm import get_llm
        
        dna = agent.dna
        mutation_log = []
        
        # Determine effective mutation rate
        effective_rate = dna.evolution_genes.mutation_rate
        
        # Apply mutations gene by gene
        for gene_path, probability in self.config.gene_mutation_probabilities.items():
            if random.random() < probability * effective_rate * 10:  # Scale to effective rate
                try:
                    old_value = self._get_gene_value(dna, gene_path)
                    new_value = await self._mutate_gene(gene_path, old_value)
                    
                    if new_value != old_value:
                        dna = dna.mutate_gene(gene_path, new_value)
                        mutation_log.append({
                            "gene": gene_path,
                            "old": str(old_value)[:100],
                            "new": str(new_value)[:100]
                        })
                except Exception as e:
                    # Skip failed mutations
                    continue
        
        # Create new agent
        from genesis.agents import Agent
        new_agent = Agent.from_dna(dna, generation=agent.generation + 1)
        new_agent.parent_ids = [agent.id]
        new_agent.mutation_history = mutation_log
        
        return new_agent
    
    async def _mutate_gene(self, gene_path: str, current_value: Any) -> Any:
        """
        Apply appropriate mutation based on gene type.
        """
        from genesis.llm import get_llm
        
        # Determine mutation strength
        strength = random.uniform(0, self.config.max_mutation_strength)
        
        if gene_path.endswith("system_prompt"):
            return await self._mutate_prompt(current_value, strength)
        
        elif gene_path.endswith("reasoning_pattern"):
            return self._mutate_enum(
                current_value,
                ["chain-of-thought", "tree-of-thought", "react", "plan-and-execute"]
            )
        
        elif gene_path.endswith("temperature"):
            return self._mutate_float(current_value, strength, 0.0, 2.0)
        
        elif gene_path.endswith("max_tokens"):
            return self._mutate_int(current_value, strength, 256, 8192)
        
        elif gene_path.endswith("verbosity"):
            return self._mutate_float(current_value, strength, 0.0, 1.0)
        
        elif gene_path.endswith("reasoning_effort"):
            return self._mutate_enum(current_value, ["low", "medium", "high"])
        
        elif gene_path.endswith("available_tools"):
            return self._mutate_tool_list(current_value, strength)
        
        elif gene_path.endswith("self_correction_enabled"):
            return not current_value  # Toggle
        
        elif isinstance(current_value, bool):
            return random.random() < 0.5
        
        elif isinstance(current_value, int):
            return self._mutate_int(current_value, strength, current_value // 2, current_value * 2)
        
        elif isinstance(current_value, float):
            return self._mutate_float(current_value, strength, 0.0, 1.0)
        
        return current_value
    
    async def _mutate_prompt(self, prompt: str, strength: float) -> str:
        """Use LLM to mutate a prompt semantically"""
        from genesis.llm import get_llm
        
        llm = get_llm(model=self.config.prompt_mutation_model)
        
        # Select mutation prompt based on strength
        if strength < 0.3:
            mutation_prompt = self.MILD_MUTATION_PROMPT
        elif strength < 0.6:
            mutation_prompt = self.MEDIUM_MUTATION_PROMPT
        else:
            mutation_prompt = self.STRONG_MUTATION_PROMPT
        
        response = await llm.complete(
            mutation_prompt.format(prompt=prompt),
            temperature=min(strength + 0.3, 0.9),
            max_tokens=len(prompt) + 500
        )
        
        return response.content.strip()
    
    def _mutate_float(self, value: float, strength: float, min_val: float, max_val: float) -> float:
        """Apply Gaussian noise to float value"""
        import numpy as np
        
        noise = np.random.normal(0, strength * (max_val - min_val))
        new_value = value + noise
        return max(min_val, min(max_val, new_value))
    
    def _mutate_int(self, value: int, strength: float, min_val: int, max_val: int) -> int:
        """Apply Gaussian noise to int value"""
        import numpy as np
        
        noise = int(np.random.normal(0, strength * value))
        new_value = value + noise
        return max(min_val, min(max_val, new_value))
    
    def _mutate_enum(self, current: str, options: List[str]) -> str:
        """Select different enum value"""
        other_options = [o for o in options if o != current]
        return random.choice(other_options) if other_options else current
    
    def _mutate_tool_list(self, tools: List[str], strength: float) -> List[str]:
        """Add, remove, or swap tools"""
        available_tools = ["web_search", "pdf_reader", "data_extractor", 
                          "code_executor", "file_manager", "api_client",
                          "database_query", "image_analyzer", "chart_generator"]
        
        tools = list(tools)  # Copy
        
        action = random.random()
        if action < 0.33 and tools:
            # Remove random tool
            tools.remove(random.choice(tools))
        elif action < 0.66:
            # Add random tool
            new_tool = random.choice([t for t in available_tools if t not in tools])
            tools.append(new_tool)
        else:
            # Swap tool
            if tools:
                tools.remove(random.choice(tools))
                new_tool = random.choice([t for t in available_tools if t not in tools])
                tools.append(new_tool)
        
        return tools
    
    def _get_gene_value(self, dna: "AgentDNA", gene_path: str) -> Any:
        """Get gene value by path (e.g., 'prompt_genes.system_prompt')"""
        parts = gene_path.split(".")
        obj = dna
        for part in parts:
            obj = getattr(obj, part)
        return obj
```

### 4.2 Mutation Examples

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MUTATION EXAMPLES                                         │
│                                                                                  │
│  SYSTEM PROMPT MUTATION (Strength: 0.2 - Mild)                                  │
│  ─────────────────────────────────────────────                                  │
│  BEFORE:                                                                        │
│  "You are a research agent. Find relevant information on the given topic."      │
│                                                                                  │
│  AFTER:                                                                         │
│  "You are an expert research agent. Find relevant, authoritative information    │
│   on the given topic. Prioritize peer-reviewed sources and recent publications. │
│   Always cite your sources."                                                    │
│                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  PARAMETER MUTATION (Temperature: 0.3 → 0.45)                                   │
│  ─────────────────────────────────────────────                                  │
│  Impact: Agent becomes slightly more creative in responses                      │
│                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  TOOL MUTATION (Add "chart_generator")                                          │
│  ─────────────────────────────────────────────                                  │
│  BEFORE: ["web_search", "pdf_reader"]                                           │
│  AFTER:  ["web_search", "pdf_reader", "chart_generator"]                        │
│  Impact: Agent can now create visualizations                                    │
│                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────  │
│                                                                                  │
│  MEMORY GENE MUTATION (episodic_retrieval_k: 5 → 8)                             │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  Impact: Agent recalls more historical context per task                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. CROSSOVER OPERATORS

### 5.1 Semantic Blending

```python
# genesis/evolution/crossover.py
from dataclasses import dataclass
from typing import List, Dict, Tuple
import random

@dataclass
class CrossoverConfig:
    """Configuration for crossover operators"""
    blend_prompts: bool = True
    interpolate_parameters: bool = True
    merge_toolsets: bool = True
    blend_memory_genes: bool = True
    blend_evolution_genes: bool = True

class SemanticCrossover:
    """
    Semantic blending of two parent agents.
    
    Unlike bit-string crossover, we use LLMs to intelligently
    combine the best elements of both parents' prompts.
    """
    
    PROMPT_BLEND_PROMPT = """
    Create a new system prompt by combining the best elements of these two prompts.
    
    PROMPT A (Fitness: {fitness_a}):
    {prompt_a}
    
    PROMPT B (Fitness: {fitness_b}):
    {prompt_b}
    
    Instructions:
    1. Identify the strengths of each prompt
    2. Create a new prompt that combines these strengths
    3. Include the most effective techniques from both
    4. Remove weaknesses or redundancies
    5. The result should be coherent and executable
    6. Return ONLY the new prompt, no explanations
    """
    
    def __init__(self, config: CrossoverConfig = None):
        self.config = config or CrossoverConfig()
    
    async def crossover(
        self,
        parent1: "Agent",
        parent2: "Agent"
    ) -> "Agent":
        """
        Create child agent by blending two parents.
        
        Process:
        1. Blend system prompts using LLM
        2. Interpolate parameters (weighted by fitness)
        3. Merge toolsets
        4. Blend memory genes
        5. Create new DNA and agent
        """
        dna1 = parent1.dna
        dna2 = parent2.dna
        
        # Blend prompts
        child_prompt = await self._blend_prompts(
            dna1.prompt_genes.system_prompt,
            dna2.prompt_genes.system_prompt,
            parent1.fitness_score,
            parent2.fitness_score
        )
        
        # Create child DNA
        child_dna = AgentDNA(
            agent_type=dna1.agent_type,  # Same type as parents
            generation=max(parent1.generation, parent2.generation) + 1,
            lineage=[parent1.id, parent2.id],
            prompt_genes=PromptGenes(
                system_prompt=child_prompt,
                reasoning_pattern=self._select_gene(
                    dna1.prompt_genes.reasoning_pattern,
                    dna2.prompt_genes.reasoning_pattern,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                self_correction_enabled=self._select_boolean(
                    dna1.prompt_genes.self_correction_enabled,
                    dna2.prompt_genes.self_correction_enabled,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                verbosity=self._interpolate(
                    dna1.prompt_genes.verbosity,
                    dna2.prompt_genes.verbosity,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                tone=self._select_gene(
                    dna1.prompt_genes.tone,
                    dna2.prompt_genes.tone,
                    parent1.fitness_score,
                    parent2.fitness_score
                )
            ),
            parameter_genes=ParameterGenes(
                temperature=self._interpolate(
                    dna1.parameter_genes.temperature,
                    dna2.parameter_genes.temperature,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                max_tokens=self._interpolate_int(
                    dna1.parameter_genes.max_tokens,
                    dna2.parameter_genes.max_tokens,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                reasoning_effort=self._select_gene(
                    dna1.parameter_genes.reasoning_effort,
                    dna2.parameter_genes.reasoning_effort,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                adaptive_temperature=self._select_boolean(
                    dna1.parameter_genes.adaptive_temperature,
                    dna2.parameter_genes.adaptive_temperature,
                    parent1.fitness_score,
                    parent2.fitness_score
                )
            ),
            tool_genes=ToolGenes(
                available_tools=self._merge_toolsets(
                    dna1.tool_genes.available_tools,
                    dna2.tool_genes.available_tools
                ),
                max_tools_per_task=self._interpolate_int(
                    dna1.tool_genes.max_tools_per_task,
                    dna2.tool_genes.max_tools_per_task,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                tool_selection_strategy=self._select_gene(
                    dna1.tool_genes.tool_selection_strategy,
                    dna2.tool_genes.tool_selection_strategy,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                parallel_tool_execution=self._select_boolean(
                    dna1.tool_genes.parallel_tool_execution,
                    dna2.tool_genes.parallel_tool_execution,
                    parent1.fitness_score,
                    parent2.fitness_score
                )
            ),
            memory_genes=MemoryGenes(
                working_memory_size=self._interpolate_int(
                    dna1.memory_genes.working_memory_size,
                    dna2.memory_genes.working_memory_size,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                episodic_retrieval_k=self._interpolate_int(
                    dna1.memory_genes.episodic_retrieval_k,
                    dna2.memory_genes.episodic_retrieval_k,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                semantic_depth=self._interpolate_int(
                    dna1.memory_genes.semantic_depth,
                    dna2.memory_genes.semantic_depth,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                importance_threshold=self._interpolate(
                    dna1.memory_genes.importance_threshold,
                    dna2.memory_genes.importance_threshold,
                    parent1.fitness_score,
                    parent2.fitness_score
                )
            ),
            evolution_genes=EvolutionGenes(
                mutation_rate=self._interpolate(
                    dna1.evolution_genes.mutation_rate,
                    dna2.evolution_genes.mutation_rate,
                    parent1.fitness_score,
                    parent2.fitness_score
                ),
                fitness_weights=dna1.evolution_genes.fitness_weights  # Inherit from fitter parent
            )
        )
        
        # Create child agent
        from genesis.agents import Agent
        child = Agent.from_dna(child_dna)
        child.parent_ids = [parent1.id, parent2.id]
        
        return child
    
    async def _blend_prompts(
        self,
        prompt_a: str,
        prompt_b: str,
        fitness_a: float,
        fitness_b: float
    ) -> str:
        """Use LLM to blend two prompts"""
        from genesis.llm import get_llm
        
        blend_prompt = self.PROMPT_BLEND_PROMPT.format(
            prompt_a=prompt_a,
            prompt_b=prompt_b,
            fitness_a=f"{fitness_a:.2f}",
            fitness_b=f"{fitness_b:.2f}"
        )
        
        llm = get_llm(model="gpt-5.4-mini")
        response = await llm.complete(blend_prompt, temperature=0.5)
        
        return response.content.strip()
    
    def _interpolate(
        self,
        val_a: float,
        val_b: float,
        fitness_a: float,
        fitness_b: float
    ) -> float:
        """Interpolate between two values weighted by fitness"""
        total_fitness = fitness_a + fitness_b
        if total_fitness == 0:
            return (val_a + val_b) / 2
        
        weight_a = fitness_a / total_fitness
        return val_a * weight_a + val_b * (1 - weight_a)
    
    def _interpolate_int(
        self,
        val_a: int,
        val_b: int,
        fitness_a: float,
        fitness_b: float
    ) -> int:
        """Interpolate between two ints weighted by fitness"""
        return int(round(self._interpolate(val_a, val_b, fitness_a, fitness_b)))
    
    def _select_gene(
        self,
        gene_a,
        gene_b,
        fitness_a: float,
        fitness_b: float
    ):
        """Select one gene value weighted by fitness"""
        if fitness_a + fitness_b == 0:
            return random.choice([gene_a, gene_b])
        
        prob_a = fitness_a / (fitness_a + fitness_b)
        return gene_a if random.random() < prob_a else gene_b
    
    def _select_boolean(
        self,
        val_a: bool,
        val_b: bool,
        fitness_a: float,
        fitness_b: float
    ) -> bool:
        """Select boolean weighted by fitness"""
        if val_a == val_b:
            return val_a
        return self._select_gene(val_a, val_b, fitness_a, fitness_b)
    
    def _merge_toolsets(
        self,
        tools_a: List[str],
        tools_b: List[str]
    ) -> List[str]:
        """Merge two toolsets, removing duplicates"""
        merged = list(set(tools_a) | set(tools_b))
        # Limit to reasonable number
        if len(merged) > 10:
            # Keep tools that appear in both parents (consensus)
            consensus = list(set(tools_a) & set(tools_b))
            # Fill with random selection from union
            remaining = [t for t in merged if t not in consensus]
            needed = 10 - len(consensus)
            merged = consensus + random.sample(remaining, min(needed, len(remaining)))
        return merged
```

---

## 6. FITNESS EVALUATION

### 6.1 Hierarchical Fitness Evaluation

Inspired by the Artemis platform's multi-stage evaluation:

```python
# genesis/evolution/fitness.py
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from datetime import datetime
import asyncio

@dataclass
class FitnessConfig:
    """Configuration for fitness evaluation"""
    # Stage thresholds
    llm_score_threshold: float = 0.5  # Minimum to proceed to Stage 2
    simulation_threshold: float = 0.6  # Minimum to proceed to Stage 3
    
    # Weights for composite fitness
    accuracy_weight: float = 0.4
    efficiency_weight: float = 0.3
    adaptability_weight: float = 0.2
    diversity_weight: float = 0.1
    
    # Benchmark settings
    benchmark_sample_size: int = 20
    simulation_timeout: int = 30

@dataclass
class FitnessResult:
    """Result of fitness evaluation"""
    overall_fitness: float
    accuracy_score: float
    efficiency_score: float
    adaptability_score: float
    diversity_score: float
    stages_completed: int
    evaluation_cost: float  # Estimated $ cost
    evaluation_time_seconds: float
    details: Dict

class HierarchicalFitnessEvaluator:
    """
    Multi-stage fitness evaluation.
    
    Key principle: Cheap evaluators first to filter out poor candidates,
    expensive evaluators only for promising ones.
    
    Stage 1: LLM Scoring ($0.001, ~1s)
    Stage 2: Simulation ($0.01, ~10s)
    Stage 3: Full Benchmark ($1-10, ~1min)
    """
    
    def __init__(self, config: FitnessConfig = None):
        self.config = config or FitnessConfig()
    
    async def evaluate(self, agent: "Agent", benchmark: "Benchmark") -> FitnessResult:
        """
        Evaluate agent fitness hierarchically.
        
        Returns:
            FitnessResult with composite score and components
        """
        start_time = datetime.now()
        total_cost = 0
        stages = 0
        
        # Stage 1: LLM Scoring (cheap filter)
        llm_score = await self._llm_score(agent, benchmark)
        total_cost += 0.001
        stages = 1
        
        if llm_score < self.config.llm_score_threshold:
            # Early termination
            return FitnessResult(
                overall_fitness=llm_score * 0.3,  # Penalize for failing early
                accuracy_score=llm_score,
                efficiency_score=0,
                adaptability_score=0,
                diversity_score=0,
                stages_completed=stages,
                evaluation_cost=total_cost,
                evaluation_time_seconds=(datetime.now() - start_time).total_seconds(),
                details={"stage1_llm_score": llm_score, "terminated": "stage1"}
            )
        
        # Stage 2: Simulation (behavioral validation)
        sim_score = await self._simulate(agent, benchmark)
        total_cost += 0.01
        stages = 2
        
        if sim_score < self.config.simulation_threshold:
            return FitnessResult(
                overall_fitness=sim_score * 0.6,
                accuracy_score=llm_score,
                efficiency_score=sim_score,
                adaptability_score=0,
                diversity_score=0,
                stages_completed=stages,
                evaluation_cost=total_cost,
                evaluation_time_seconds=(datetime.now() - start_time).total_seconds(),
                details={"stage1_llm_score": llm_score, "stage2_sim_score": sim_score, "terminated": "stage2"}
            )
        
        # Stage 3: Full benchmark (expensive but accurate)
        full_score = await self._full_benchmark(agent, benchmark)
        total_cost += 1.0
        stages = 3
        
        # Calculate component scores
        accuracy = full_score
        efficiency = await self._measure_efficiency(agent, benchmark)
        adaptability = await self._measure_adaptability(agent, benchmark)
        diversity = self._measure_diversity(agent)
        
        # Composite fitness
        composite = (
            accuracy * self.config.accuracy_weight +
            efficiency * self.config.efficiency_weight +
            adaptability * self.config.adaptability_weight +
            diversity * self.config.diversity_weight
        )
        
        return FitnessResult(
            overall_fitness=composite,
            accuracy_score=accuracy,
            efficiency_score=efficiency,
            adaptability_score=adaptability,
            diversity_score=diversity,
            stages_completed=stages,
            evaluation_cost=total_cost,
            evaluation_time_seconds=(datetime.now() - start_time).total_seconds(),
            details={
                "stage1_llm_score": llm_score,
                "stage2_sim_score": sim_score,
                "stage3_full_score": full_score
            }
        )
    
    async def _llm_score(self, agent: "Agent", benchmark: "Benchmark") -> float:
        """
        Stage 1: Quick LLM-based scoring without actual execution.
        
        Ask an LLM to predict how well the agent would perform
        based on its DNA and sample tasks.
        """
        from genesis.llm import get_fast_model
        
        llm = get_fast_model()
        
        # Get sample tasks
        sample_tasks = benchmark.get_samples(5)
        
        scores = []
        for task in sample_tasks:
            prompt = f"""
            Evaluate how well the following agent configuration would perform on this task.
            
            Agent DNA:
            - Type: {agent.dna.agent_type}
            - Prompt: {agent.dna.prompt_genes.system_prompt[:200]}...
            - Reasoning: {agent.dna.prompt_genes.reasoning_pattern}
            - Temperature: {agent.dna.parameter_genes.temperature}
            - Tools: {', '.join(agent.dna.tool_genes.available_tools)}
            
            Task: {task.description}
            
            Rate from 0.0 to 1.0 based on:
            - Prompt relevance to task
            - Tool appropriateness
            - Parameter suitability
            
            Return ONLY a number between 0.0 and 1.0.
            """
            
            response = await llm.complete(prompt, temperature=0)
            
            try:
                score = float(response.content.strip())
                scores.append(max(0, min(1, score)))
            except ValueError:
                scores.append(0.5)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    async def _simulate(self, agent: "Agent", benchmark: "Benchmark") -> float:
        """
        Stage 2: Simulated execution in sandbox.
        
        Actually run the agent on a subset of tasks with limited resources.
        """
        from genesis.execution import SandboxExecutor
        
        executor = SandboxExecutor(timeout=self.config.simulation_timeout)
        
        sample_tasks = benchmark.get_samples(10)
        results = []
        
        for task in sample_tasks:
            result = await executor.run(agent, task)
            results.append(1.0 if result.success else 0.0)
        
        return sum(results) / len(results) if results else 0
    
    async def _full_benchmark(self, agent: "Agent", benchmark: "Benchmark") -> float:
        """
        Stage 3: Full benchmark evaluation.
        
        Run complete benchmark suite. This is expensive but accurate.
        """
        results = await benchmark.run(agent)
        return results.accuracy
    
    async def _measure_efficiency(self, agent: "Agent", benchmark: "Benchmark") -> float:
        """Measure token efficiency and latency"""
        # Normalize: lower tokens and latency = higher score
        avg_tokens = benchmark.get_avg_tokens(agent)
        avg_latency = benchmark.get_avg_latency(agent)
        
        # Score relative to baseline
        token_score = max(0, 1 - (avg_tokens / 10000))  # Normalize to 10K tokens
        latency_score = max(0, 1 - (avg_latency / 30000))  # Normalize to 30s
        
        return (token_score + latency_score) / 2
    
    async def _measure_adaptability(self, agent: "Agent", benchmark: "Benchmark") -> float:
        """Measure performance across diverse task types"""
        task_types = benchmark.get_task_types()
        
        scores = []
        for task_type in task_types:
            type_benchmark = benchmark.filter_by_type(task_type)
            result = await self._simulate(agent, type_benchmark)
            scores.append(result)
        
        # High adaptability = consistent performance across types
        # Penalize high variance
        mean_score = sum(scores) / len(scores) if scores else 0
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores) if scores else 1
        
        return mean_score * (1 - variance)
    
    def _measure_diversity(self, agent: "Agent") -> float:
        """
        Measure genetic diversity (unique DNA characteristics).
        
        Higher diversity score for agents with unique gene combinations.
        """
        # Simple measure: hash uniqueness
        dna_hash = agent.dna.hash
        
        # In a real implementation, compare against population
        # For now, return a neutral score
        return 0.5
```

---

## 7. EVOLUTION CONTROLLER

### 7.1 The Evolution Loop

```python
# genesis/evolution/controller.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import structlog

logger = structlog.get_logger()

@dataclass
class EvolutionCycleConfig:
    """Configuration for evolution cycles"""
    # Trigger conditions
    trigger_on_task_count: int = 100
    trigger_on_time_hours: int = 24
    manual_override: bool = True
    
    # Population settings
    min_population_size: int = 5
    max_population_size: int = 20
    target_population_size: int = 10
    
    # Evolution parameters
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elitism_count: int = 2
    
    # Safety
    sandbox_validation: bool = True
    gradual_deployment: bool = True
    rollback_on_regression: bool = True
    
    # Termination
    max_generations_without_improvement: int = 5
    fitness_improvement_threshold: float = 0.01

class EvolutionController:
    """
    Central controller for the genetic evolution process.
    
    Manages:
    - Evolution cycle triggering
    - Population management
    - Generation tracking
    - Safety (sandbox, rollback)
    """
    
    def __init__(
        self,
        config: EvolutionCycleConfig = None,
        selection: "SelectionOperator" = None,
        mutation: "SemanticMutator" = None,
        crossover: "SemanticCrossover" = None,
        fitness_evaluator: "HierarchicalFitnessEvaluator" = None
    ):
        self.config = config or EvolutionCycleConfig()
        self.selection = selection or TournamentSelection()
        self.mutation = mutation or SemanticMutator()
        self.crossover = crossover or SemanticCrossover()
        self.fitness = fitness_evaluator or HierarchicalFitnessEvaluator()
        
        self.task_counter = 0
        self.last_evolution_time = datetime.now()
        self.generations_without_improvement = 0
        self.best_fitness_ever = 0
    
    async def on_task_completed(self):
        """Called after each task completion. May trigger evolution."""
        self.task_counter += 1
        
        should_evolve = (
            self.task_counter >= self.config.trigger_on_task_count or
            (datetime.now() - self.last_evolution_time).total_seconds() / 3600 >= self.config.trigger_on_time_hours
        )
        
        if should_evolve:
            self.task_counter = 0
            await self.run_evolution_cycle()
    
    async def run_evolution_cycle(self, agent_type: Optional[str] = None):
        """
        Run a complete evolution cycle.
        
        Process:
        1. Get current population
        2. Evaluate fitness
        3. Select parents
        4. Apply crossover and mutation
        5. Validate offspring
        6. Deploy successful offspring
        7. Update population
        """
        logger.info("Starting evolution cycle", agent_type=agent_type)
        start_time = datetime.now()
        
        # Step 1: Get population
        population = await self._get_population(agent_type)
        
        if len(population) < self.config.min_population_size:
            logger.warning("Population too small, skipping evolution",
                          current_size=len(population),
                          min_required=self.config.min_population_size)
            return
        
        # Step 2: Evaluate fitness (for agents without recent scores)
        for agent in population:
            if agent.fitness_score is None or agent.needs_re_evaluation:
                fitness_result = await self.fitness.evaluate(agent, self._get_benchmark(agent))
                agent.fitness_score = fitness_result.overall_fitness
                agent.fitness_details = fitness_result.details
        
        # Check for improvement
        max_fitness = max(a.fitness_score for a in population)
        if max_fitness > self.best_fitness_ever + self.config.fitness_improvement_threshold:
            self.best_fitness_ever = max_fitness
            self.generations_without_improvement = 0
        else:
            self.generations_without_improvement += 1
        
        # Check termination condition
        if self.generations_without_improvement >= self.config.max_generations_without_improvement:
            logger.info("Evolution converged, stopping",
                       generations_without_improvement=self.generations_without_improvement)
            return
        
        # Step 3: Selection
        num_parents = min(len(population), self.config.target_population_size)
        parents = self.selection.select(population, num_parents)
        
        logger.info("Selected parents",
                   count=len(parents),
                   avg_fitness=sum(p.fitness_score for p in parents) / len(parents))
        
        # Step 4: Reproduction
        offspring = []
        
        # Elitism: keep top performers
        sorted_pop = sorted(population, key=lambda a: a.fitness_score, reverse=True)
        elites = sorted_pop[:self.config.elitism_count]
        offspring.extend(elites)
        
        # Crossover
        num_crossover = int((self.config.target_population_size - len(elites)) * self.config.crossover_rate)
        for _ in range(num_crossover // 2):
            parent1, parent2 = random.sample(parents, 2)
            try:
                child = await self.crossover.crossover(parent1, parent2)
                offspring.append(child)
            except Exception as e:
                logger.error("Crossover failed", error=str(e))
        
        # Mutation
        num_mutation = self.config.target_population_size - len(offspring)
        mutation_candidates = random.sample(parents, min(num_mutation, len(parents)))
        for parent in mutation_candidates:
            try:
                child = await self.mutation.mutate(parent)
                offspring.append(child)
            except Exception as e:
                logger.error("Mutation failed", error=str(e))
        
        # Step 5: Validation
        if self.config.sandbox_validation:
            valid_offspring = []
            for child in offspring:
                is_valid = await self._validate_in_sandbox(child)
                if is_valid:
                    valid_offspring.append(child)
                else:
                    logger.warning("Offspring failed validation",
                                  agent_id=child.id,
                                  generation=child.generation)
            offspring = valid_offspring
        
        # Step 6: Gradual deployment
        if self.config.gradual_deployment and len(offspring) > 0:
            await self._gradual_deploy(offspring)
        else:
            await self._deploy_all(offspring)
        
        # Step 7: Update population
        await self._update_population(population, offspring)
        
        # Record generation
        await self._record_generation(population, offspring)
        
        self.last_evolution_time = datetime.now()
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info("Evolution cycle complete",
                   duration_seconds=duration,
                   population_size=len(offsspring),
                   max_fitness=max_fitness)
    
    async def _validate_in_sandbox(self, agent: "Agent") -> bool:
        """Validate agent in sandbox before deployment"""
        from genesis.execution import SandboxExecutor
        
        executor = SandboxExecutor(timeout=30)
        
        # Basic validation
        if not agent.dna.prompt_genes.system_prompt:
            return False
        
        if len(agent.dna.prompt_genes.system_prompt) < 10:
            return False
        
        # Behavioral validation
        test_task = {"description": "Simple validation test", "type": "test"}
        try:
            result = await executor.run(agent, test_task)
            return result.success
        except Exception:
            return False
    
    async def _gradual_deploy(self, offspring: List["Agent"]):
        """Deploy with gradual rollout: 10% → 50% → 100%"""
        
        # Phase 1: 10% traffic
        for agent in offspring:
            agent.traffic_percentage = 10
        await self._deploy(offspring)
        await asyncio.sleep(60)  # Wait 1 minute
        
        # Check metrics
        if await self._check_metricshealthy(offspring):
            # Phase 2: 50% traffic
            for agent in offspring:
                agent.traffic_percentage = 50
            await self._deploy(offspring)
            await asyncio.sleep(120)  # Wait 2 minutes
            
            if await self._check_metrics_healthy(offspring):
                # Phase 3: 100% traffic
                for agent in offspring:
                    agent.traffic_percentage = 100
                await self._deploy(offspring)
            else:
                await self._rollback(offspring)
        else:
            await self._rollback(offspring)
    
    async def _check_metrics_healthy(self, agents: List["Agent"]) -> bool:
        """Check if deployed agents are performing well"""
        for agent in agents:
            if agent.fitness_score < 0.3:  # Minimum acceptable
                return False
        return True
    
    async def _rollback(self, agents: List["Agent"]):
        """Rollback to previous generation"""
        logger.warning("Rolling back agents due to health check failure")
        for agent in agents:
            agent.status = "rollback"
            # Revert to parent configuration
            if agent.parent_ids:
                parent = await self._get_agent(agent.parent_ids[0])
                if parent:
                    agent.dna = parent.dna
                    agent.fitness_score = parent.fitness_score
