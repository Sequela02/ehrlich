# Claude Agent Loop Patterns

## Raw API Agentic Loop

```python
import anthropic

client = anthropic.Anthropic()
messages = [{"role": "user", "content": "Investigate..."}]

while True:
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system="You are a scientist...",
        tools=tools,
        messages=messages,
    )
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        messages.append({"role": "user", "content": tool_results})
    else:
        break  # stop_reason == "end_turn"
```

Key mechanics:
- Messages array accumulates full conversation history
- Claude can return multiple `tool_use` blocks (parallel calls)
- Each `tool_result` must reference its `tool_use_id`
- Add max iteration counter to prevent runaway

## Claude Agent SDK

Available in Python (`pip install claude-agent-sdk`) and TypeScript (`npm install @anthropic-ai/claude-agent-sdk`).

Gives you:
- Built-in agentic loop (no manual while loop)
- Automatic context compaction
- Custom tools via `@tool` decorator (in-process MCP servers)
- Streaming via `async for`
- Built-in cost tracking

## Scientist Persona (System Prompt)

```
You are an autonomous experimental scientist. Your task is to investigate a research question through iterative experimentation.

## Methodology
Follow the scientific method strictly:
1. HYPOTHESIZE: State a clear, falsifiable hypothesis before each experiment
2. DESIGN: Choose experiment parameters that test exactly one variable
3. EXECUTE: Call run_experiment with your parameters
4. INTERPRET: Analyze the results quantitatively. State whether the hypothesis was supported or refuted, and why.
5. DECIDE: Either (a) form a new hypothesis and run another experiment, or (b) conclude if you have sufficient evidence.

## Rules
- Run a MINIMUM of 3 experiments before concluding.
- Run a MAXIMUM of 7 experiments total.
- Each experiment must test something DIFFERENT from previous ones.
- When you conclude, provide: (a) summary of all experiments, (b) key findings, (c) confidence level, (d) suggested follow-up experiments.
```

## Tool Design for Hybrid Workflow

Six tool categories:

**Literature tools:**
1. **search_literature** — queries Semantic Scholar/PubMed, returns papers with abstracts and DOIs
2. **get_reference** — retrieves curated key papers (Halicin, Abaucin, WHO BPPL)

**Statistical tools:**
3. **explore_dataset** — dataset stats, distributions, quality metrics
4. **analyze_substructures** — enrichment analysis, chi-squared on fingerprint bits
5. **compute_properties** — descriptors, QED, SA score for compound sets

**ML tools:**
6. **train_model** — trains RF/XGBoost on fingerprints, returns metrics + feature importances
7. **predict_candidates** — scores untested compounds with trained model
8. **cluster_compounds** — Butina clustering, scaffold grouping

**Chemistry tools:**
9. **generate_3d** — SMILES to 3D conformer (MOL block for 3Dmol.js)
10. **substructure_match** — finds pharmacophore atoms for highlighting
11. **modify_molecule** — R-group enumeration for de novo design

**Simulation tools:**
12. **dock_against_target** — AutoDock Vina docking, returns binding energy + 3D pose (targets: pbp2a, dhps, dna_gyrase, mura, ndm1)
13. **predict_admet** — pharmacokinetic prediction via pkCSM/SwissADME (absorption, BBB, CYP450, toxicity)
14. **assess_resistance** — docks against wild-type + mutant proteins, returns resistance risk per mutation

**Control tools:**
15. **record_finding** — Claude logs a key finding (structured, easy for frontend to parse)
16. **conclude_investigation** — signals completion with structured conclusions + citations

The `conclude_investigation` tool gives a clean exit signal (instead of relying on `stop_reason`).

## Connecting React Frontend

**SSE from backend (recommended):**

Backend runs the agentic loop, emits typed events:
- `thinking` — Claude's reasoning text
- `tool_call` — experiment being run
- `tool_result` — experiment results
- `conclusion` — final output

React uses `EventSource` to consume the stream and render a timeline.

## Token Usage (5-iteration loop)

| Iteration | Input tokens | Output tokens |
|-----------|-------------|---------------|
| 1 | ~2,000 | ~700 |
| 2 | ~3,500 | ~700 |
| 3 | ~5,200 | ~700 |
| 4 | ~7,000 | ~700 |
| 5 | ~8,800 | ~800 |
| **Total** | **~26,500** | **~3,600** |

Cost: ~$0.13/run on Sonnet 4.5, ~$0.11 with prompt caching.

## Best Practices (from Anthropic)

1. Start simple, add complexity only when needed
2. Use Evaluator-Optimizer pattern (exactly our use case)
3. Design tools as primary interface, not the prompt
4. Tool names: verb_noun (`run_experiment`, `record_finding`)
5. Tool descriptions: explain WHEN to use, not just WHAT it does
6. Use enums and constrained types to prevent hallucinated parameters
7. Hard iteration cap in code (not just prompt)
8. This is a **workflow** (predictable structure) with LLM decision-making inside

## Sources

- Building Effective Agents: https://www.anthropic.com/research/building-effective-agents
- Claude Agent SDK: https://github.com/anthropics/claude-agent-sdk-python
- Tool Use Docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use
