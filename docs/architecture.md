# WANDR Architecture

```text
reference/wandr_tasks/* (source tasks)
  -> adapters/wandr (deterministic packaging)
    -> datasets/wandr/* (self-contained Harbor tasks)
      -> Harbor run + Relay agent
        -> task-local verifier (wandr_core)
          -> rewards + diagnostics + reports + replay pack
```

Key boundaries:
- **Source-of-truth tasks:** `reference/wandr_tasks/`
- **Generator/adapter:** `adapters/wandr/`
- **Runnable benchmark packages:** `datasets/wandr/`
- **Execution adapter:** `agents/relay/`
- **Evaluator runtime:** `tests/wandr_core` inside generated tasks
