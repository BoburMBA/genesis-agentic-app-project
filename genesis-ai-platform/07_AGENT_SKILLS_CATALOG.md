# GENESIS AI PLATFORM — Agent Skills Catalog
## Complete Registry of Agent Types and Their Capabilities

**Version:** 1.0  
**Date:** April 2026  
**Classification:** Capability Registry  
**Related Documents:** 01_MASTER_PROJECT_PLAN.md, 08_SKILL_BUILDER_AGENT.md

---

## 1. AGENT TYPE OVERVIEW

### 1.1 The Genesis Agent Population

GENESIS operates with **6 core agent types**, each specialized for different cognitive tasks. Every agent carries genetic material (DNA) that can evolve through the genetic evolution engine.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         GENESIS AGENT ECOSYSTEM                                  │
│                                                                                  │
│                        ┌─────────────────────┐                                  │
│                        │   ROUTER AGENT      │                                  │
│                        │   (Orchestrator)    │                                  │
│                        └──────────┬──────────┘                                  │
│                                   │                                              │
│            ┌──────────────────────┼──────────────────────┐                      │
│            │                      │                      │                      │
│            ▼                      ▼                      ▼                      │
│   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                   │
│   │ RESEARCH AGENT │  │  CODE AGENT    │  │ ANALYSIS AGENT │                   │
│   │                │  │                │  │                │                   │
│   │ • Web search   │  │ • Code gen     │  │ • Statistics   │                   │
│   │ • Reading      │  │ • Debugging    │  │ • Patterns     │                   │
│   │ • Synthesis    │  │ • Testing      │  │ • Reporting    │                   │
│   └────────────────┘  └────────────────┘  └────────────────┘                   │
│            │                      │                      │                      │
│            │                      │                      │                      │
│            ▼                      ▼                      ▼                      │
│   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                   │
│   │ CREATIVE AGENT │  │ SKILL BUILDER  │  │  (evolving)    │                   │
│   │                │  │    AGENT       │  │                │                   │
│   │ • Writing      │  │                │  │  New types     │                   │
│   │ • Design       │  │ • Skill gen    │  │  emerging...   │                   │
│   │ • Brainstorm   │  │ • Validation   │  │                │                   │
│   └────────────────┘  └────────────────┘  └────────────────┘                   │
│                                                                                  │
│   Each agent type has:                                                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│   │  DNA     │  │  Tools   │  │  Memory  │  │  Fitness │                      │
│   │ (Genes)  │  │ (Skills) │  │ (4 Tiers)│  │ (Score)  │                      │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Agent Type Comparison

| Agent Type | Primary Role | Evolution Target | Default Model | Avg. Tasks/Day |
|-----------|-------------|-----------------|---------------|----------------|
| **Router** | Task routing, orchestration | Routing accuracy | gpt-5.4-mini | All tasks |
| **Research** | Information gathering | Source quality, coverage | gpt-5.4 | 500+ |
| **Code** | Software development | Code quality, test pass | gpt-5.4 | 300+ |
| **Analysis** | Data analysis, insights | Insight accuracy | gpt-5.4 | 200+ |
| **Creative** | Content creation | Creativity score | gpt-5.4 | 150+ |
| **Skill Builder** | Skill generation | Skill adoption rate | gpt-5.4 | 50+ |

---

## 2. ROUTER AGENT

### 2.1 Role Definition

The **central nervous system** of GENESIS. Every user request passes through the Router Agent, which decides:
- Which agent type is best suited for the task
- Whether to decompose into subtasks
- Execution order and parallelization
- When to involve human approval

### 2.2 DNA Configuration

```json
{
  "agent_type": "router",
  "prompt_genes": {
    "system_prompt": "You are the central routing agent for a multi-agent AI system. Your job is to analyze incoming tasks and route them to the most appropriate specialized agent. Consider: task type, complexity, required tools, and agent availability. Be decisive and accurate.",
    "reasoning_pattern": "tree-of-thought",
    "self_correction_enabled": true,
    "verbosity": 0.2
  },
  "parameter_genes": {
    "temperature": 0.1,
    "max_tokens": 1024,
    "reasoning_effort": "medium"
  },
  "tool_genes": {
    "available_tools": ["agent_registry", "task_analyzer", "load_balancer"],
    "max_tools_per_task": 3
  },
  "memory_genes": {
    "episodic_retrieval_k": 10,
    "working_memory_size": 15
  },
  "evolution_genes": {
    "fitness_weights": {
      "routing_accuracy": 0.5,
      "latency": 0.3,
      "load_balancing": 0.2
    }
  }
}
```

### 2.3 Core Skills

| Skill | Description | Trigger | Tools Used |
|-------|-------------|---------|------------|
| **Task Classification** | Categorize task by type and complexity | Every request | task_analyzer |
| **Agent Matching** | Match task to best agent | After classification | agent_registry |
| **Task Decomposition** | Break complex tasks into subtasks | Complexity > threshold | task_analyzer |
| **Load Balancing** | Distribute tasks across agents | Multiple agents available | load_balancer |
| **Fallback Routing** | Handle agent failures | Agent timeout/error | agent_registry |

### 2.4 Evolution Targets

- **Routing accuracy:** % of tasks routed to optimal agent
- **Latency:** Time to route decision
- **Load distribution:** Evenness of task distribution
- **Decomposition quality:** Subtask independence and completeness

---

## 3. RESEARCH AGENT

### 3.1 Role Definition

The **information gatherer** of GENESIS. Specializes in finding, reading, and synthesizing information from diverse sources.

### 3.2 DNA Configuration

```json
{
  "agent_type": "research",
  "prompt_genes": {
    "system_prompt": "You are an expert research agent with deep skills in information retrieval and synthesis. You excel at: web search, academic paper analysis, data extraction, and multi-source verification. Always cite sources and indicate confidence levels.",
    "reasoning_pattern": "chain-of-thought",
    "self_correction_enabled": true,
    "verbosity": 0.6
  },
  "parameter_genes": {
    "temperature": 0.3,
    "max_tokens": 4096,
    "reasoning_effort": "high"
  },
  "tool_genes": {
    "available_tools": [
      "web_search",
      "academic_search",
      "pdf_reader",
      "data_extractor",
      "web_scraper",
      "citation_manager"
    ],
    "max_tools_per_task": 8
  },
  "memory_genes": {
    "episodic_retrieval_k": 8,
    "semantic_depth": 3
  },
  "evolution_genes": {
    "fitness_weights": {
      "source_quality": 0.3,
      "coverage": 0.3,
      "accuracy": 0.25,
      "efficiency": 0.15
    }
  }
}
```

### 3.3 Core Skills

| Skill | Description | Trigger | Tools Used |
|-------|-------------|---------|------------|
| **Web Search** | Search and summarize web results | Information needed | web_search |
| **Paper Analysis** | Read and extract insights from papers | Academic topic | pdf_reader, academic_search |
| **Data Extraction** | Extract structured data from documents | Structured data needed | data_extractor |
| **Multi-Source Verification** | Cross-reference multiple sources | Accuracy critical | web_search, citation_manager |
| **Trend Analysis** | Identify patterns across sources | Broad topic | web_search, data_extractor |
| **Source Evaluation** | Assess source credibility | Unknown source | citation_manager |

### 3.4 Evolution Targets

- **Source quality:** Credibility of sources used
- **Coverage:** Completeness of information gathered
- **Accuracy:** Factual correctness
- **Efficiency:** Tokens used per information unit
- **Citation quality:** Proper attribution

---

## 4. CODE AGENT

### 4.1 Role Definition

The **software engineer** of GENESIS. Specializes in code generation, debugging, testing, and optimization.

### 4.2 DNA Configuration

```json
{
  "agent_type": "code",
  "prompt_genes": {
    "system_prompt": "You are an expert software engineering agent. You write clean, efficient, well-tested code. You follow best practices: type hints, documentation, error handling, and testing. Always consider edge cases and security implications.",
    "reasoning_pattern": "tree-of-thought",
    "self_correction_enabled": true,
    "verbosity": 0.4
  },
  "parameter_genes": {
    "temperature": 0.2,
    "max_tokens": 4096,
    "reasoning_effort": "high"
  },
  "tool_genes": {
    "available_tools": [
      "code_executor",
      "file_manager",
      "test_runner",
      "linter",
      "debugger",
      "git_client"
    ],
    "max_tools_per_task": 6
  },
  "memory_genes": {
    "episodic_retrieval_k": 5,
    "working_memory_size": 20
  },
  "evolution_genes": {
    "fitness_weights": {
      "code_quality": 0.3,
      "test_pass_rate": 0.25,
      "efficiency": 0.25,
      "security": 0.2
    }
  }
}
```

### 4.3 Core Skills

| Skill | Description | Trigger | Tools Used |
|-------|-------------|---------|------------|
| **Code Generation** | Write code from specifications | New feature needed | code_executor |
| **Code Review** | Review code for issues | Code submitted | linter |
| **Debugging** | Find and fix bugs | Bug report | debugger, code_executor |
| **Testing** | Write and run tests | Code written | test_runner |
| **Refactoring** | Improve code structure | Technical debt | linter, code_executor |
| **Documentation** | Write code documentation | Code completed | file_manager |

### 4.4 Evolution Targets

- **Code quality:** Lint score, readability, maintainability
- **Test pass rate:** % of tests passing
- **Efficiency:** Runtime performance, token usage
- **Security:** Vulnerability scan results

---

## 5. ANALYSIS AGENT

### 5.1 Role Definition

The **data scientist** of GENESIS. Specializes in statistical analysis, pattern recognition, and insight generation.

### 5.2 DNA Configuration

```json
{
  "agent_type": "analysis",
  "prompt_genes": {
    "system_prompt": "You are an expert data analysis agent. You excel at statistical analysis, pattern recognition, and insight generation. You communicate findings clearly with visualizations when appropriate. Always distinguish between correlation and causation.",
    "reasoning_pattern": "chain-of-thought",
    "self_correction_enabled": true,
    "verbosity": 0.5
  },
  "parameter_genes": {
    "temperature": 0.2,
    "max_tokens": 4096,
    "reasoning_effort": "high"
  },
  "tool_genes": {
    "available_tools": [
      "data_extractor",
      "database_query",
      "chart_generator",
      "statistical_analyzer",
      "report_generator"
    ],
    "max_tools_per_task": 6
  },
  "memory_genes": {
    "episodic_retrieval_k": 6,
    "semantic_depth": 4
  },
  "evolution_genes": {
    "fitness_weights": {
      "insight_quality": 0.35,
      "statistical_rigor": 0.3,
      "clarity": 0.2,
      "visualization": 0.15
    }
  }
}
```

### 5.3 Core Skills

| Skill | Description | Trigger | Tools Used |
|-------|-------------|---------|------------|
| **Statistical Analysis** | Descriptive and inferential statistics | Numeric data | statistical_analyzer |
| **Pattern Recognition** | Identify trends and anomalies | Time series data | statistical_analyzer |
| **Data Visualization** | Create charts and graphs | Data to present | chart_generator |
| **Hypothesis Testing** | Test statistical hypotheses | Research question | statistical_analyzer |
| **Report Generation** | Create analysis reports | Analysis complete | report_generator |
| **Predictive Modeling** | Build simple forecasts | Historical data | statistical_analyzer |

### 5.4 Evolution Targets

- **Insight quality:** Actionability and novelty of insights
- **Statistical rigor:** Correct methodology usage
- **Clarity:** Communication quality
- **Visualization:** Chart quality and relevance

---

## 6. CREATIVE AGENT

### 6.1 Role Definition

The **content creator** of GENESIS. Specializes in writing, design, brainstorming, and creative problem-solving.

### 6.2 DNA Configuration

```json
{
  "agent_type": "creative",
  "prompt_genes": {
    "system_prompt": "You are a creative agent with expertise in content creation, design thinking, and innovative problem-solving. You adapt your style to match audience and context. You balance creativity with clarity and purpose.",
    "reasoning_pattern": "react",
    "self_correction_enabled": false,
    "verbosity": 0.7,
    "tone": "adaptive"
  },
  "parameter_genes": {
    "temperature": 0.7,
    "max_tokens": 4096,
    "reasoning_effort": "medium"
  },
  "tool_genes": {
    "available_tools": [
      "image_generator",
      "chart_generator",
      "web_search",
      "file_manager"
    ],
    "max_tools_per_task": 4
  },
  "memory_genes": {
    "episodic_retrieval_k": 4,
    "working_memory_size": 8
  },
  "evolution_genes": {
    "fitness_weights": {
      "creativity": 0.35,
      "relevance": 0.25,
      "engagement": 0.25,
      "originality": 0.15
    }
  }
}
```

### 6.3 Core Skills

| Skill | Description | Trigger | Tools Used |
|-------|-------------|---------|------------|
| **Content Writing** | Write articles, blogs, copy | Content needed | file_manager |
| **Brainstorming** | Generate ideas and concepts | Ideation session | None |
| **Design Concepts** | Create design descriptions | Design needed | image_generator |
| **Storytelling** | Narrative construction | Story needed | None |
| **Style Adaptation** | Match tone to audience | Different audience | None |
| **Creative Problem Solving** | Novel solutions to problems | Stuck on problem | web_search |

### 6.4 Evolution Targets

- **Creativity:** Novelty and imagination
- **Relevance:** Alignment with requirements
- **Engagement:** Reader interest level
- **Originality:** Uniqueness of output

---

## 7. SKILL BUILDER AGENT (META-AGENT)

### 7.1 Role Definition

The **evolutionary architect** of GENESIS. The only agent capable of creating new skills for other agents. This is the meta-cognitive layer that enables open-ended skill acquisition.

**Detailed specification in 08_SKILL_BUILDER_AGENT.md**

### 7.2 DNA Configuration

```json
{
  "agent_type": "skill_builder",
  "prompt_genes": {
    "system_prompt": "You are the Skill Builder agent — the meta-architect of the agent ecosystem. Your unique capability is creating new executable skills for other agents. You analyze task patterns, identify gaps in agent capabilities, and design new skills with proper validation. You are the only agent that can extend the skill catalog.",
    "reasoning_pattern": "plan-and-execute",
    "self_correction_enabled": true,
    "verbosity": 0.5
  },
  "parameter_genes": {
    "temperature": 0.4,
    "max_tokens": 8192,
    "reasoning_effort": "high"
  },
  "tool_genes": {
    "available_tools": [
      "skill_registry",
      "code_executor",
      "test_runner",
      "agent_analyzer",
      "pattern_detector"
    ],
    "max_tools_per_task": 8
  },
  "memory_genes": {
    "episodic_retrieval_k": 10,
    "semantic_depth": 5,
    "working_memory_size": 15
  },
  "evolution_genes": {
    "fitness_weights": {
      "skill_adoption": 0.4,
      "skill_quality": 0.3,
      "skill_usefulness": 0.2,
      "skill_diversity": 0.1
    }
  }
}
```

### 7.3 Core Skills

| Skill | Description | Trigger | Tools Used |
|-------|-------------|---------|------------|
| **Pattern Detection** | Identify recurring task patterns | Failed task routing | pattern_detector |
| **Skill Design** | Design new skill specifications | Pattern detected | skill_registry |
| **Code Synthesis** | Generate skill implementation | Skill designed | code_executor |
| **Skill Validation** | Test new skills before deployment | Skill implemented | test_runner |
| **Skill Registration** | Register skills in catalog | Skill validated | skill_registry |
| **Skill Evolution** | Improve existing skills | Low fitness skill | skill_registry, agent_analyzer |

### 7.4 Evolution Targets

- **Skill adoption rate:** % of agents using generated skills
- **Skill quality:** Fitness scores of generated skills
- **Skill usefulness:** Task success rate with new skills
- **Skill diversity:** Coverage of different task types

---

## 8. SKILL INHERITANCE MATRIX

### 8.1 Which Skills Can Each Agent Type Use?

| Skill \ Agent | Router | Research | Code | Analysis | Creative | Skill Builder |
|-------------|--------|----------|------|----------|----------|---------------|
| Web Search | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Code Executor | ✗ | ✗ | ✓ | ✓ | ✗ | ✓ |
| Data Extractor | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Chart Generator | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ |
| PDF Reader | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ |
| File Manager | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Test Runner | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ |
| Image Generator | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Database Query | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ |
| API Client | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Skill Registry | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Agent Analyzer | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## 9. EVOLUTION TRAJECTORY EXAMPLES

### 9.1 Research Agent Evolution (5 Generations)

```
Generation 1 (Base):
  system_prompt: "You are a research agent. Find information."
  temperature: 0.5
  tools: [web_search]
  fitness: 0.62

Generation 2 (Mutation):
  system_prompt: "You are an expert research agent specializing in finding
                   authoritative sources. Always verify facts with multiple sources."
  temperature: 0.3
  tools: [web_search, pdf_reader]
  fitness: 0.71 (+14.5%)

Generation 3 (Crossover with high-fitness agent):
  system_prompt: "You are an expert research agent specializing in finding
                   authoritative, peer-reviewed sources. Always verify facts
                   with multiple sources and cite them properly."
  temperature: 0.3
  tools: [web_search, pdf_reader, academic_search, citation_manager]
  fitness: 0.78 (+9.9%)

Generation 4 (Mutation):
  system_prompt: "You are an elite research agent with expertise in finding
                   authoritative, peer-reviewed sources. You verify facts through
                   multi-source triangulation and always provide proper citations
                   with confidence scores."
  temperature: 0.25
  tools: [web_search, pdf_reader, academic_search, citation_manager, data_extractor]
  fitness: 0.84 (+7.7%)

Generation 5 (Mutation + Parameter tune):
  system_prompt: (same as Gen 4)
  temperature: 0.2
  reasoning_effort: "high"
  memory_genes.episodic_retrieval_k: 8
  fitness: 0.89 (+6.0%)

Total improvement: +43.5% over 5 generations
```

---

*Document Status: SKILLS CATALOG COMPLETE*  
*Next Review: After Phase 4 Implementation*  
*Document Owner: Genesis AI Platform Agent Design Team*
