---
name: model-info
description: Show 
argument-hint: [model-id]
allowed-tools: [Bash]
agent: general-purpose
---

# Model Info

Display information about the models available.

## Arguments

The user invoked this with: $ARGUMENTS

## Instructions

When this skill is invoked, run `bash ./scripts/model_info.sh` relative to this skill's directory.

## Example Output
Model(context_length=131072, id='DeepSeek-V3.1-Terminus', max_completion_tokens=7168)
Model(context_length=8192, id='DeepSeek-V3.2', max_completion_tokens=7168)
Model(context_length=163840, id='MiniMax-M2.5', max_completion_tokens=16384)
Model(context_length=65536, id='Qwen3-235B', max_completion_tokens=4096)
Model(context_length=131072, id='gpt-oss-120b', max_completion_tokens=131072)
