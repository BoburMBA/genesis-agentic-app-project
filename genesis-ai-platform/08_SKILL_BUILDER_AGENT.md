# GENESIS AI PLATFORM — Skill Builder Agent Specification
## Deep Technical Design for Autonomous Skill Generation

**Version:** 1.0  
**Date:** April 2026  
**Classification:** Meta-Agent Specification  
**Related Documents:** 01_MASTER_PROJECT_PLAN.md, 07_AGENT_SKILLS_CATALOG.md

---

## 1. SKILL BUILDER AGENT OVERVIEW

### 1.1 The Meta-Cognitive Layer

The **Skill Builder Agent** is the most unique component of GENESIS — the only agent with the authority to **create, modify, and evolve skills** for the entire agent ecosystem. It's the mechanism through which the system achieves **open-ended capability growth**.

**Key Innovation:** While traditional agent systems have fixed capabilities, GENESIS can autonomously extend its own skill catalog based on observed task patterns and failures.

### 1.2 Why a Dedicated Skill Builder?

Research from the Artemis platform (2025) and self-improving agent studies (2026) demonstrates:

- **80% of agent improvements** come from better prompts and tools, not model changes
- **Manual skill creation** takes 2-4 hours per skill
- **Automated skill generation** can produce valid skills in 5-15 minutes
- **Genetic optimization** improves skill quality by 10-37% over manual creation

### 1.3 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      SKILL BUILDER AGENT                                         │
│                    "The Architect of Capabilities"                               │
│                                                                                  │
│  OBSERVE                    DESIGN                   VALIDATE                   │
│  ───────                    ──────                   ────────                   │
│  ┌──────────┐              ┌──────────┐              ┌──────────┐              │
│  │ Pattern  │              │ Skill    │              │ Sandbox  │              │
│  │ Detector │─────────────▶│ Designer │─────────────▶│ Executor │              │
│  └──────────┘              └──────────┘              └──────────┘              │
│       │                         │                         │                      │
│       │                         │                         │                      │
│       ▼                         ▼                         ▼                      │
│  ┌──────────┐              ┌──────────┐              ┌──────────┐              │
│  │ Failure  │              │ Code     │              │ Fitness  │              │
│  │ Analyzer │              │ Generator│              │ Evaluator│              │
│  └──────────┘              └──────────┘              └──────────┘              │
│       │                         │                         │                      │
│       └─────────────────────────┴─────────────────────────┘                      │
│                                     │                                              │
│                                     ▼                                              │
│                              ┌──────────┐                                        │
│                              │ DEPLOY   │                                        │
│                              │ Registry │                                        │
│                              └──────────┘                                        │
│                                                                                  │
│  TRIGGER CONDITIONS:                                                             │
│  1. Task fails due to missing skill                                              │
│  2. Agent repeatedly uses workaround for missing capability                      │
│  3. Admin manually requests new skill                                            │
│  4. Evolution cycle identifies skill gap                                         │
│  5. Pattern detector identifies recurring task type                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. SKILL DEFINITION SCHEMA

### 2.1 Skill DNA (Machine-Readable)

Every skill in GENESIS has a genetic encoding that enables evolution:

```python
# genesis/skills/schema.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import json

class SkillComplexity(Enum):
    SIMPLE = "simple"       # Single-step, deterministic
    MEDIUM = "medium"       # Multi-step, some conditionals
    COMPLEX = "complex"     # Multi-step, error handling, state management

class ExecutionPattern(Enum):
    SEQUENTIAL = "sequential"       # Step A → Step B → Step C
    PARALLEL = "parallel"           # Step A + Step B + Step C
    CONDITIONAL = "conditional"     # If X then A else B
    ITERATIVE = "iterative"         # Repeat until condition
    ADAPTIVE = "adaptive"           # Dynamic based on intermediate results

@dataclass
class InputSchema:
    """Defines expected input for the skill"""
    fields: Dict[str, Dict[str, Any]]  # name: {type, description, required, default}
    
    def validate(self, inputs: Dict) -> (bool, List[str]):
        """Validate input against schema"""
        errors = []
        for field_name, field_spec in self.fields.items():
            if field_spec.get("required", True) and field_name not in inputs:
                errors.append(f"Missing required field: {field_name}")
            if field_name in inputs:
                expected_type = field_spec.get("type", "string")
                actual_type = type(inputs[field_name]).__name__
                if not self._type_matches(expected_type, actual_type):
                    errors.append(f"Field {field_name}: expected {expected_type}, got {actual_type}")
        return len(errors) == 0, errors
    
    def _type_matches(self, expected: str, actual: str) -> bool:
        type_map = {
            "string": ["str"],
            "integer": ["int"],
            "number": ["int", "float"],
            "boolean": ["bool"],
            "array": ["list"],
            "object": ["dict"]
        }
        return actual in type_map.get(expected, [expected])

@dataclass
class OutputSchema:
    """Defines expected output from the skill"""
    fields: Dict[str, Dict[str, Any]]  # name: {type, description}
    
    def validate(self, output: Dict) -> (bool, List[str]):
        """Validate output against schema"""
        errors = []
        for field_name, field_spec in self.fields.items():
            if field_name not in output:
                errors.append(f"Missing output field: {field_name}")
        return len(errors) == 0, errors

@dataclass
class ValidationRule:
    """A rule for validating skill execution"""
    name: str
    description: str
    condition: str  # Python expression or LLM prompt
    rule_type: str  # "python", "llm", "regex"
    severity: str = "error"  # "error", "warning"

@dataclass
class SkillDNA:
    """
    Genetic encoding of a skill.
    
    This is the complete machine-readable definition of a skill
    that can be:
    - Generated automatically by the Skill Builder
    - Mutated by the evolution engine
    - Executed by any agent
    - Versioned and tracked
    """
    
    # Identity
    skill_id: str
    name: str
    version: int = 1
    description: str = ""
    
    # Classification
    agent_types: List[str] = field(default_factory=list)  # Which agent types can use this
    tags: List[str] = field(default_factory=list)
    complexity: SkillComplexity = SkillComplexity.MEDIUM
    
    # Core definition
    prompt_template: str = ""  # The primary instruction template
    execution_pattern: ExecutionPattern = ExecutionPattern.SEQUENTIAL
    
    # Input/Output contracts
    input_schema: InputSchema = field(default_factory=lambda: InputSchema(fields={}))
    output_schema: OutputSchema = field(default_factory=lambda: OutputSchema(fields={}))
    
    # Tool requirements
    required_tools: List[str] = field(default_factory=list)
    optional_tools: List[str] = field(default_factory=list)
    
    # Execution parameters
    parameters: Dict[str, Any] = field(default_factory=lambda: {
        "temperature": 0.3,
        "max_tokens": 2048,
        "timeout_seconds": 30,
        "max_retries": 2
    })
    
    # Validation
    validation_rules: List[ValidationRule] = field(default_factory=list)
    
    # Error handling
    error_handling: Dict[str, str] = field(default_factory=lambda: {
        "on_timeout": "retry",
        "on_failure": "fallback",
        "fallback_skill": ""
    })
    
    # Examples for few-shot learning
    examples: List[Dict] = field(default_factory=list)
    
    # Metadata
    created_by: str = ""  # Agent ID that created this skill
    lineage: List[str] = field(default_factory=list)  # Parent skill IDs
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Runtime metrics (populated after execution)
    fitness_score: float = 0.5
    usage_count: int = 0
    success_count: int = 0
    avg_execution_time_ms: float = 0
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps({
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "agent_types": self.agent_types,
            "tags": self.tags,
            "complexity": self.complexity.value,
            "prompt_template": self.prompt_template,
            "execution_pattern": self.execution_pattern.value,
            "input_schema": self.input_schema.fields,
            "output_schema": self.output_schema.fields,
            "required_tools": self.required_tools,
            "optional_tools": self.optional_tools,
            "parameters": self.parameters,
            "validation_rules": [
                {"name": r.name, "description": r.description, "condition": r.condition,
                 "rule_type": r.rule_type, "severity": r.severity}
                for r in self.validation_rules
            ],
            "error_handling": self.error_handling,
            "examples": self.examples,
            "created_by": self.created_by,
            "lineage": self.lineage,
            "created_at": self.created_at
        }, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SkillDNA":
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            version=data.get("version", 1),
            description=data.get("description", ""),
            agent_types=data.get("agent_types", []),
            tags=data.get("tags", []),
            complexity=SkillComplexity(data.get("complexity", "medium")),
            prompt_template=data.get("prompt_template", ""),
            execution_pattern=ExecutionPattern(data.get("execution_pattern", "sequential")),
            input_schema=InputSchema(fields=data.get("input_schema", {})),
            output_schema=OutputSchema(fields=data.get("output_schema", {})),
            required_tools=data.get("required_tools", []),
            optional_tools=data.get("optional_tools", []),
            parameters=data.get("parameters", {}),
            validation_rules=[
                ValidationRule(**r) for r in data.get("validation_rules", [])
            ],
            error_handling=data.get("error_handling", {}),
            examples=data.get("examples", []),
            created_by=data.get("created_by", ""),
            lineage=data.get("lineage", []),
            created_at=data.get("created_at", datetime.now().isoformat())
        )
```

### 2.2 Skill Definition Example

```json
{
  "skill_id": "skill-web-research-synthesis-v1",
  "name": "Web Research Synthesis",
  "version": 1,
  "description": "Search the web for information on a topic and synthesize findings into a structured report with citations",
  "agent_types": ["research", "analysis"],
  "tags": ["research", "web", "synthesis", "auto-generated"],
  "complexity": "medium",
  "prompt_template": "Research the following topic using web search: {{topic}}\n\nRequirements:\n- Find at least {{min_sources}} authoritative sources\n- Extract key facts and data points\n- Synthesize findings into a coherent summary\n- Include source citations with confidence scores\n- Structure output as: Executive Summary, Key Findings, Sources\n\nOutput format:\n{{output_schema}}",
  "execution_pattern": "sequential",
  "input_schema": {
    "topic": {
      "type": "string",
      "description": "Research topic or question",
      "required": true
    },
    "min_sources": {
      "type": "integer",
      "description": "Minimum number of sources to find",
      "required": false,
      "default": 5
    },
    "depth": {
      "type": "string",
      "description": "Research depth",
      "required": false,
      "default": "medium",
      "enum": ["shallow", "medium", "deep"]
    }
  },
  "output_schema": {
    "executive_summary": {
      "type": "string",
      "description": "High-level summary of findings"
    },
    "key_findings": {
      "type": "array",
      "description": "List of key findings with evidence"
    },
    "sources": {
      "type": "array",
      "description": "List of sources with URLs and confidence"
    },
    "confidence_score": {
      "type": "number",
      "description": "Overall confidence in findings (0-1)"
    }
  },
  "required_tools": ["web_search", "web_scraper"],
  "optional_tools": ["citation_manager", "pdf_reader"],
  "parameters": {
    "temperature": 0.3,
    "max_tokens": 4096,
    "timeout_seconds": 60,
    "max_retries": 2
  },
  "validation_rules": [
    {
      "name": "minimum_sources",
      "description": "Must have at least min_sources",
      "condition": "len(output['sources']) >= inputs.get('min_sources', 5)",
      "rule_type": "python",
      "severity": "error"
    },
    {
      "name": "confidence_threshold",
      "description": "Confidence score must be above 0.5",
      "condition": "output['confidence_score'] > 0.5",
      "rule_type": "python",
      "severity": "warning"
    }
  ],
  "error_handling": {
    "on_timeout": "retry",
    "on_failure": "fallback",
    "fallback_skill": "skill-simple-web-search-v1"
  },
  "examples": [
    {
      "input": {
        "topic": "Latest developments in CRISPR gene editing 2025",
        "min_sources": 3,
        "depth": "medium"
      },
      "output": {
        "executive_summary": "CRISPR technology has advanced significantly...",
        "key_findings": ["Finding 1...", "Finding 2..."],
        "sources": [{"url": "...", "confidence": 0.9}],
        "confidence_score": 0.85
      }
    }
  ],
  "created_by": "skill-builder-agent-001",
  "lineage": [],
  "created_at": "2026-04-23T10:00:00Z"
}
```

---

## 3. SKILL GENERATION PIPELINE

### 3.1 The 5-Stage Pipeline

```python
# genesis/skills/generator.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

@dataclass
class SkillGenerationRequest:
    """Request to generate a new skill"""
    trigger_type: str  # "pattern_detected", "task_failed", "admin_request", "evolution_gap"
    description: str  # Natural language description of needed skill
    agent_type: str  # Target agent type
    examples: List[Dict] = None  # Example inputs/outputs
    existing_skills: List[str] = None  # Similar existing skills
    priority: str = "normal"  # "low", "normal", "high", "critical"

@dataclass
class SkillGenerationResult:
    """Result of skill generation"""
    skill: SkillDNA
    generation_time_seconds: float
    validation_passed: bool
    test_results: Dict
    estimated_fitness: float

class SkillGenerationPipeline:
    """
    5-stage pipeline for autonomous skill generation:
    
    1. Requirement Analysis
    2. Skill Design
    3. Code Generation
    4. Validation
    5. Registration
    """
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.skill_designer = SkillDesigner()
        self.code_generator = SkillCodeGenerator()
        self.validator = SkillValidator()
        self.registry = SkillRegistry()
    
    async def generate(self, request: SkillGenerationRequest) -> SkillGenerationResult:
        """
        Execute the full skill generation pipeline.
        """
        start_time = datetime.now()
        
        # Stage 1: Requirement Analysis
        requirements = await self._analyze_requirements(request)
        
        # Stage 2: Skill Design
        skill_design = await self._design_skill(requirements)
        
        # Stage 3: Code Generation
        skill_code = await self._generate_code(skill_design)
        
        # Stage 4: Validation
        validation_results = await self._validate(skill_code)
        
        # Stage 5: Registration (if validation passes)
        if validation_results["passed"]:
            registered_skill = await self._register(skill_code, validation_results)
        else:
            # Attempt auto-fix
            fixed_skill = await self._attempt_fix(skill_code, validation_results)
            revalidation = await self._validate(fixed_skill)
            if revalidation["passed"]:
                registered_skill = await self._register(fixed_skill, revalidation)
            else:
                registered_skill = skill_code  # Register anyway with warning flag
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return SkillGenerationResult(
            skill=registered_skill,
            generation_time_seconds=duration,
            validation_passed=validation_results["passed"],
            test_results=validation_results,
            estimated_fitness=validation_results.get("estimated_fitness", 0.5)
        )
    
    async def _analyze_requirements(self, request: SkillGenerationRequest) -> Dict:
        """
        Stage 1: Analyze the skill requirement.
        
        Extract:
        - What capability is needed
        - Input/output expectations
        - Tool requirements
        - Complexity level
        """
        from genesis.llm import get_powerful_model
        
        llm = get_powerful_model()
        
        analysis_prompt = f"""
        Analyze the following skill requirement and extract structured specifications.
        
        Request Type: {request.trigger_type}
        Description: {request.description}
        Target Agent: {request.agent_type}
        
        Existing Similar Skills: {request.existing_skills or "None"}
        
        Extract:
        1. Skill name (concise, descriptive)
        2. Core capability description
        3. Expected inputs with types
        4. Expected outputs with types
        5. Required tools
        6. Complexity level (simple/medium/complex)
        7. Similar skills to inherit from
        
        Return JSON.
        """
        
        response = await llm.complete(analysis_prompt, response_format={"type": "json_object"})
        return json.loads(response.content)
    
    async def _design_skill(self, requirements: Dict) -> SkillDNA:
        """
        Stage 2: Design the skill DNA.
        
        Create complete skill definition including:
        - Prompt template
        - Input/output schemas
        - Validation rules
        - Error handling
        """
        from genesis.llm import get_powerful_model
        
        llm = get_powerful_model()
        
        design_prompt = f"""
        Design a complete skill definition based on the following requirements.
        
        Requirements:
        {json.dumps(requirements, indent=2)}
        
        Create:
        1. A detailed prompt template with {{variable}} placeholders
        2. Input schema with types and validation
        3. Output schema with expected fields
        4. Validation rules
        5. Error handling strategy
        6. 2-3 example input/output pairs
        
        The skill should be self-contained, well-documented, and follow best practices.
        
        Return as JSON matching the SkillDNA schema.
        """
        
        response = await llm.complete(design_prompt, response_format={"type": "json_object"})
        design_data = json.loads(response.content)
        
        # Create SkillDNA from design
        skill_id = f"skill-{requirements['name'].lower().replace(' ', '-')}-v1"
        
        return SkillDNA(
            skill_id=skill_id,
            name=requirements["name"],
            description=requirements.get("description", ""),
            agent_types=[requirements.get("target_agent", "research")],
            tags=requirements.get("tags", ["auto-generated"]),
            complexity=SkillComplexity(requirements.get("complexity", "medium")),
            prompt_template=design_data.get("prompt_template", ""),
            input_schema=InputSchema(fields=design_data.get("input_schema", {})),
            output_schema=OutputSchema(fields=design_data.get("output_schema", {})),
            required_tools=requirements.get("required_tools", []),
            validation_rules=[
                ValidationRule(**r) for r in design_data.get("validation_rules", [])
            ],
            error_handling=design_data.get("error_handling", {}),
            examples=design_data.get("examples", []),
            created_by="skill-builder-agent"
        )
    
    async def _generate_code(self, skill_design: SkillDNA) -> SkillDNA:
        """
        Stage 3: Generate executable code for the skill.
        
        Creates:
        - Python execution function
        - Input validation
        - Error handling
        - Tool orchestration
        """
        from genesis.llm import get_powerful_model
        
        llm = get_powerful_model()
        
        code_prompt = f"""
        Generate Python code for the following skill.
        
        Skill: {skill_design.name}
        Description: {skill_design.description}
        Prompt Template: {skill_design.prompt_template[:500]}
        Input Schema: {json.dumps(skill_design.input_schema.fields)}
        Output Schema: {json.dumps(skill_design.output_schema.fields)}
        Required Tools: {skill_design.required_tools}
        
        Generate:
        1. An `execute(inputs: Dict) -> Dict` function
        2. Input validation using the schema
        3. Tool calls in the correct order
        4. Output formatting matching the schema
        5. Error handling with retries
        
        The code should be production-ready with type hints and docstrings.
        
        Return ONLY the Python code, no explanations.
        """
        
        response = await llm.complete(code_prompt, temperature=0.2)
        
        # Store generated code in skill metadata
        skill_design.parameters["generated_code"] = response.content
        skill_design.parameters["code_version"] = "1.0"
        
        return skill_design
    
    async def _validate(self, skill: SkillDNA) -> Dict:
        """
        Stage 4: Validate the generated skill.
        
        Tests:
        1. Schema validation (input/output)
        2. Syntax validation (generated code)
        3. Execution test (sandbox)
        4. Output format validation
        """
        results = {
            "passed": True,
            "tests": [],
            "estimated_fitness": 0.5
        }
        
        # Test 1: Input schema validation
        try:
            test_input = self._generate_test_input(skill.input_schema)
            valid, errors = skill.input_schema.validate(test_input)
            results["tests"].append({
                "name": "input_schema",
                "passed": valid,
                "errors": errors
            })
            if not valid:
                results["passed"] = False
        except Exception as e:
            results["tests"].append({
                "name": "input_schema",
                "passed": False,
                "errors": [str(e)]
            })
            results["passed"] = False
        
        # Test 2: Syntax validation
        if "generated_code" in skill.parameters:
            try:
                compile(skill.parameters["generated_code"], "<string>", "exec")
                results["tests"].append({
                    "name": "syntax",
                    "passed": True,
                    "errors": []
                })
            except SyntaxError as e:
                results["tests"].append({
                    "name": "syntax",
                    "passed": False,
                    "errors": [f"Line {e.lineno}: {e.msg}"]
                })
                results["passed"] = False
        
        # Test 3: Sandbox execution
        try:
            from genesis.execution import SandboxExecutor
            executor = SandboxExecutor(timeout=30)
            
            test_input = self._generate_test_input(skill.input_schema)
            execution_result = await executor.execute_skill(skill, test_input)
            
            results["tests"].append({
                "name": "execution",
                "passed": execution_result.success,
                "errors": [execution_result.error] if execution_result.error else [],
                "latency_ms": execution_result.latency_ms
            })
            
            if execution_result.success:
                # Test 4: Output validation
                valid, errors = skill.output_schema.validate(execution_result.output)
                results["tests"].append({
                    "name": "output_schema",
                    "passed": valid,
                    "errors": errors
                })
                
                if valid:
                    # Estimate fitness based on execution quality
                    results["estimated_fitness"] = min(0.8, 0.5 + (1 - execution_result.latency_ms / 30000) * 0.3)
            else:
                results["passed"] = False
                
        except Exception as e:
            results["tests"].append({
                "name": "execution",
                "passed": False,
                "errors": [str(e)]
            })
            results["passed"] = False
        
        return results
    
    async def _attempt_fix(self, skill: SkillDNA, validation_results: Dict) -> SkillDNA:
        """
        Auto-fix validation failures.
        
        Common fixes:
        - Fix syntax errors
        - Adjust output format
        - Add missing error handling
        """
        from genesis.llm import get_powerful_model
        
        llm = get_powerful_model()
        
        # Collect errors
        errors = []
        for test in validation_results.get("tests", []):
            if not test["passed"]:
                errors.extend(test.get("errors", []))
        
        fix_prompt = f"""
        Fix the following skill based on validation errors.
        
        Current Skill Code:
        {skill.parameters.get("generated_code", "")}
        
        Validation Errors:
        {chr(10).join(errors)}
        
        Fix the code to address these errors. Return ONLY the fixed code.
        """
        
        response = await llm.complete(fix_prompt, temperature=0.2)
        
        skill.parameters["generated_code"] = response.content
        skill.version += 1
        
        return skill
    
    async def _register(self, skill: SkillDNA, validation: Dict) -> SkillDNA:
        """
        Stage 5: Register the skill in the catalog.
        
        Actions:
        - Store in PostgreSQL
        - Index in Qdrant
        - Notify relevant agents
        - Start fitness tracking
        """
        # Register in database
        await self.registry.register(skill)
        
        # Index for semantic search
        await self.registry.index(skill)
        
        # Notify agents of new skill
        await self._notify_agents(skill)
        
        return skill
    
    def _generate_test_input(self, input_schema: InputSchema) -> Dict:
        """Generate test input based on schema"""
        test_input = {}
        for field_name, field_spec in input_schema.fields.items():
            field_type = field_spec.get("type", "string")
            default = field_spec.get("default")
            
            if default is not None:
                test_input[field_name] = default
            elif field_type == "string":
                test_input[field_name] = f"test_{field_name}"
            elif field_type == "integer":
                test_input[field_name] = 42
            elif field_type == "number":
                test_input[field_name] = 3.14
            elif field_type == "boolean":
                test_input[field_name] = True
            elif field_type == "array":
                test_input[field_name] = []
            elif field_type == "object":
                test_input[field_name] = {}
        
        return test_input
```

---

## 4. TRIGGER CONDITIONS

### 4.1 Automatic Triggers

| Trigger | Detection Method | Priority | Example |
|---------|-----------------|----------|---------|
| **Task Failure** | Router can't find suitable agent | High | "No agent can handle 'generate 3D model'" |
| **Workaround Pattern** | Agent uses multiple tools to simulate missing skill | Medium | Using web_search + manual parsing instead of structured_search |
| **Recurring Pattern** | PatternDetector identifies >3 similar tasks in 24h | High | "Summarize PDF" requested 5 times |
| **Evolution Gap** | Evolution cycle finds low fitness due to missing capability | Medium | Code agent failing on "write tests" repeatedly |
| **Performance Regression** | Agent fitness drops >20% | Critical | Research agent source quality declining |

### 4.2 Trigger Detection Code

```python
# genesis/skills/triggers.py
class PatternDetector:
    """
    Detects patterns that indicate a new skill is needed.
    
    Monitors:
    - Task execution logs
    - Agent failure patterns
    - Tool usage patterns
    """
    
    def __init__(self):
        self.failure_threshold = 3
        self.time_window_hours = 24
        self.similarity_threshold = 0.8
    
    async def detect_patterns(self) -> List[SkillGenerationRequest]:
        """
        Scan recent task history for skill gaps.
        
        Returns list of skill generation requests.
        """
        requests = []
        
        # Check 1: Failed tasks
        failed_requests = await self._detect_failed_task_patterns()
        requests.extend(failed_requests)
        
        # Check 2: Workaround patterns
        workaround_requests = await self._detect_workaround_patterns()
        requests.extend(workaround_requests)
        
        # Check 3: Recurring task types
        recurring_requests = await self._detect_recurring_patterns()
        requests.extend(recurring_requests)
        
        return requests
    
    async def _detect_failed_task_patterns(self) -> List[SkillGenerationRequest]:
        """Detect tasks that failed due to missing skills"""
        from genesis.db import get_db_pool
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Find tasks that failed because no agent could handle them
            rows = await conn.fetch("""
                SELECT task_description, COUNT(*) as fail_count,
                       array_agg(DISTINCT error_message) as errors
                FROM task_executions
                WHERE status = 'failed'
                  AND created_at > NOW() - INTERVAL '%s hours'
                  AND error_message ILIKE '%%no agent%%'
                GROUP BY task_description
                HAVING COUNT(*) >= $1
                ORDER BY fail_count DESC
            """, self.time_window_hours)
        
        requests = []
        for row in rows:
            requests.append(SkillGenerationRequest(
                trigger_type="task_failed",
                description=f"Multiple failures for: {row['task_description']}. Errors: {', '.join(row['errors'][:3])}",
                agent_type="unknown",
                priority="high"
            ))
        
        return requests
    
    async def _detect_workaround_patterns(self) -> List[SkillGenerationRequest]:
        """
        Detect agents using complex workarounds for missing capabilities.
        
        Pattern: Agent uses 5+ tools for a task that should need 1-2,
        indicating a missing higher-level skill.
        """
        from genesis.db import get_db_pool
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT agent_id, task_type, 
                       AVG(array_length(tools_used, 1)) as avg_tools,
                       COUNT(*) as task_count
                FROM task_executions
                WHERE created_at > NOW() - INTERVAL '%s hours'
                  AND status = 'completed'
                GROUP BY agent_id, task_type
                HAVING AVG(array_length(tools_used, 1)) > 5
                   AND COUNT(*) >= 3
            """, self.time_window_hours)
        
        requests = []
        for row in rows:
            requests.append(SkillGenerationRequest(
                trigger_type="workaround_pattern",
                description=f"Agent {row['agent_id']} uses {row['avg_tools']:.1f} tools on average for '{row['task_type']}'. "
                           f"Suggest creating a composite skill.",
                agent_type=row['task_type'],
                priority="medium"
            ))
        
        return requests
    
    async def _detect_recurring_patterns(self) -> List[SkillGenerationRequest]:
        """Detect frequently occurring task types without dedicated skills"""
        from genesis.db import get_db_pool
        from genesis.embeddings import get_embeddings
        from collections import defaultdict
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT task_description
                FROM task_executions
                WHERE created_at > NOW() - INTERVAL '%s hours'
                ORDER BY created_at DESC
                LIMIT 1000
            """, self.time_window_hours)
        
        # Cluster similar task descriptions
        descriptions = [r["task_description"] for r in rows]
        
        if len(descriptions) < 3:
            return []
        
        # Get embeddings
        embeddings = await get_embeddings(descriptions)
        
        # Simple clustering (in production, use proper clustering algorithm)
        clusters = defaultdict(list)
        for i, emb in enumerate(embeddings):
            # Find nearest cluster center
            assigned = False
            for cluster_id, cluster_embs in clusters.items():
                center = self._calculate_center(cluster_embs)
                similarity = self._cosine_similarity(emb, center)
                if similarity > self.similarity_threshold:
                    clusters[cluster_id].append(emb)
                    assigned = True
                    break
            
            if not assigned:
                clusters[len(clusters)].append(emb)
        
        # Find clusters with >3 members
        requests = []
        for cluster_id, cluster_embs in clusters.items():
            if len(cluster_embs) >= 3:
                requests.append(SkillGenerationRequest(
                    trigger_type="pattern_detected",
                    description=f"Detected {len(cluster_embs)} similar tasks in last {self.time_window_hours}h. "
                               f"Consider creating a dedicated skill.",
                    priority="high"
                ))
        
        return requests
    
    def _calculate_center(self, embeddings: List[List[float]]) -> List[float]:
        """Calculate centroid of embeddings"""
        import numpy as np
        return np.mean(embeddings, axis=0).tolist()
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        import numpy as np
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

---

## 5. SKILL EVOLUTION

### 5.1 Skill Genetic Operations

Skills themselves can evolve through the genetic engine:

```python
# genesis/skills/evolution.py
class SkillEvolution:
    """
    Evolution operations specialized for skills.
    
    Skills have their own genetic encoding (SkillDNA) that can:
    - Mutate: Prompt changes, parameter tuning
    - Crossover: Combine two skills into a composite
    - Evaluate: Fitness based on adoption and success rate
    """
    
    async def mutate_skill(self, skill: SkillDNA, strength: float = 0.2) -> SkillDNA:
        """
        Mutate a skill's DNA.
        
        Mutation types:
        1. Prompt improvement
        2. Parameter tuning
        3. Tool addition/removal
        4. Example addition
        """
        from genesis.llm import get_powerful_model
        
        llm = get_powerful_model()
        
        mutation_prompt = f"""
        Improve the following skill by making {'minor' if strength < 0.3 else 'moderate' if strength < 0.6 else 'significant'} changes.
        
        Current Skill:
        Name: {skill.name}
        Description: {skill.description}
        Prompt: {skill.prompt_template[:500]}
        
        Improvement focus (choose one):
        - Make instructions more specific and actionable
        - Add error handling considerations
        - Improve output format
        - Add more examples
        - Optimize for the target agent type
        
        Return ONLY the improved prompt_template and description.
        JSON format: {{"description": "...", "prompt_template": "..."}}
        """
        
        response = await llm.complete(mutation_prompt, response_format={"type": "json_object"})
        improvements = json.loads(response.content)
        
        # Create mutated skill
        mutated = SkillDNA.from_json(skill.to_json())
        mutated.description = improvements.get("description", skill.description)
        mutated.prompt_template = improvements.get("prompt_template", skill.prompt_template)
        mutated.version = skill.version + 1
        mutated.lineage = skill.lineage + [skill.skill_id]
        
        return mutated
    
    async def crossover_skills(self, skill_a: SkillDNA, skill_b: SkillDNA) -> SkillDNA:
        """
        Create composite skill from two parent skills.
        
        Example: Cross "web_search" + "data_extraction" = "structured_web_search"
        """
        from genesis.llm import get_powerful_model
        
        llm = get_powerful_model()
        
        crossover_prompt = f"""
        Create a new composite skill by combining these two skills.
        
        SKILL A: {skill_a.name}
        Description: {skill_a.description}
        Prompt: {skill_a.prompt_template[:300]}
        Tools: {skill_a.required_tools}
        
        SKILL B: {skill_b.name}
        Description: {skill_b.description}
        Prompt: {skill_b.prompt_template[:300]}
        Tools: {skill_b.required_tools}
        
        Create a new skill that combines the capabilities of both.
        The new skill should be more powerful than either parent alone.
        
        Return JSON with: name, description, prompt_template, required_tools
        """
        
        response = await llm.complete(crossover_prompt, response_format={"type": "json_object"})
        composite_data = json.loads(response.content)
        
        # Merge toolsets
        merged_tools = list(set(skill_a.required_tools + skill_b.required_tools))
        
        return SkillDNA(
            skill_id=f"skill-{composite_data['name'].lower().replace(' ', '-')}-v1",
            name=composite_data["name"],
            description=composite_data["description"],
            prompt_template=composite_data["prompt_template"],
            agent_types=list(set(skill_a.agent_types + skill_b.agent_types)),
            required_tools=merged_tools,
            complexity=SkillComplexity.COMPLEX,
            lineage=[skill_a.skill_id, skill_b.skill_id],
            created_by="skill-builder-agent-crossover"
        )
    
    def calculate_skill_fitness(self, skill: SkillDNA) -> float:
        """
        Calculate composite fitness of a skill.
        
        Factors:
        - Usage frequency (0.3)
        - Success rate (0.3)
        - User feedback (0.2)
        - Efficiency (0.2)
        """
        # Usage score (more usage = more useful)
        usage_score = min(skill.usage_count / 100, 1.0)
        
        # Success rate
        total = skill.success_count + (skill.usage_count - skill.success_count)
        success_rate = skill.success_count / total if total > 0 else 0.5
        
        # Efficiency score (faster = better)
        efficiency = max(0, 1 - (skill.avg_execution_time_ms / 60000))
        
        # Combine
        return (
            usage_score * 0.3 +
            success_rate * 0.3 +
            skill.fitness_score * 0.2 +  # User feedback proxy
            efficiency * 0.2
        )
```

---

## 6. SKILL REGISTRY

### 6.1 Registry Operations

```python
# genesis/skills/registry.py
class SkillRegistry:
    """
    Central registry for all skills in the GENESIS ecosystem.
    
    Features:
    - CRUD operations
    - Semantic search
    - Version management
    - Fitness tracking
    - Usage analytics
    """
    
    def __init__(
        self,
        db_url: str = "postgresql://localhost:5432/genesis",
        qdrant_url: str = "http://localhost:6333"
    ):
        self.db_url = db_url
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection = "procedural_memory"
    
    async def register(self, skill: SkillDNA) -> str:
        """Register a new skill"""
        import asyncpg
        
        conn = await asyncpg.connect(self.db_url)
        try:
            await conn.execute("""
                INSERT INTO skills (id, name, version, description, definition, dna,
                                  fitness_score, created_by, agent_type, tags, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    version = EXCLUDED.version,
                    definition = EXCLUDED.definition,
                    dna = EXCLUDED.dna,
                    updated_at = NOW()
            """,
                skill.skill_id,
                skill.name,
                skill.version,
                skill.description,
                skill.to_json(),
                skill.to_json(),
                skill.fitness_score,
                skill.created_by,
                skill.agent_types[0] if skill.agent_types else None,
                skill.tags,
                "active"
            )
        finally:
            await conn.close()
        
        return skill.skill_id
    
    async def find_skill(
        self,
        query: str,
        agent_type: Optional[str] = None,
        min_fitness: float = 0.3
    ) -> Optional[SkillDNA]:
        """
        Find best skill matching the query.
        
        Uses semantic search via Qdrant.
        """
        from genesis.embeddings import get_embedding
        
        query_embedding = await get_embedding(query)
        
        filter_conditions = []
        if agent_type:
            filter_conditions.append(
                FieldCondition(key="agent_types", match=MatchValue(value=agent_type))
            )
        
        results = self.qdrant.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
            limit=5
        )
        
        # Filter by fitness
        viable = [
            r for r in results
            if r.payload.get("fitness_score", 0) >= min_fitness
        ]
        
        if not viable:
            return None
        
        # Return best match
        best = max(viable, key=lambda r: r.score * r.payload.get("fitness_score", 0.5))
        
        # Load full skill
        return await self.get_skill(best.payload["skill_id"])
    
    async def get_skill_analytics(self, skill_id: str) -> Dict:
        """Get usage analytics for a skill"""
        import asyncpg
        
        conn = await asyncpg.connect(self.db_url)
        try:
            # Get execution stats
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_uses,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successes,
                    AVG(latency_ms) as avg_latency,
                    AVG(tokens_input + tokens_output) as avg_tokens
                FROM task_executions
                WHERE tools_used @> ARRAY[$1]
                  AND created_at > NOW() - INTERVAL '7 days'
            """, skill_id)
            
            # Get user feedback (stored in execution metadata)
            feedback = await conn.fetch("""
                SELECT metadata->'feedback' as feedback, COUNT(*) as count
                FROM task_executions
                WHERE tools_used @> ARRAY[$1]
                  AND metadata ? 'feedback'
                GROUP BY metadata->'feedback'
            """, skill_id)
            
            return {
                "skill_id": skill_id,
                "total_uses_7d": stats["total_uses"],
                "success_rate": stats["successes"] / stats["total_uses"] if stats["total_uses"] > 0 else 0,
                "avg_latency_ms": stats["avg_latency"],
                "avg_tokens": stats["avg_tokens"],
                "feedback_distribution": {r["feedback"]: r["count"] for r in feedback}
            }
        finally:
            await conn.close()
```

---

*Document Status: SKILL BUILDER SPECIFICATION COMPLETE*  
*Next Review: After Phase 4 Implementation*  
*Document Owner: Genesis AI Platform Meta-Agent Team*
