#!/usr/bin/env bash
set -euo pipefail

# Starts an OpenAI-compatible vLLM server for ClipContext's AMD-hosted
# inference stages (content generation and/or discriminator ranking — see
# src/ai/providers/amd_vllm.py). Run this from a terminal inside the AMD
# AI Notebook (ROCm 7.2 + vLLM 0.16.0 + PyTorch 2.9), not on your laptop —
# it needs the notebook's GPU and preinstalled ROCm/vLLM/PyTorch stack.
#
# Required:
#   AMD_VLLM_MODEL              Hugging Face model id (or local path) to
#                                serve. Chosen after real GPU diagnostics —
#                                see amd/verify_rocm.py and amd/README.md.
#
# Optional (defaults shown):
#   AMD_VLLM_HOST                0.0.0.0
#   AMD_VLLM_PORT                8000
#   AMD_VLLM_API_KEY             unset -> server accepts unauthenticated
#                                          requests. Set this before
#                                          exposing the port beyond
#                                          localhost / an authenticated
#                                          tunnel.
#   GPU_MEMORY_UTILIZATION       0.90
#   MAX_MODEL_LEN                unset -> vLLM's model-default context
#   HF_TOKEN                     unset -> only needed for a gated model

: "${AMD_VLLM_MODEL:?Set AMD_VLLM_MODEL to the Hugging Face model id (or local path) to serve.}"

HOST="${AMD_VLLM_HOST:-0.0.0.0}"
PORT="${AMD_VLLM_PORT:-8000}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"

ARGS=(
  --model "${AMD_VLLM_MODEL}"
  --served-model-name "${AMD_VLLM_MODEL}"
  --host "${HOST}"
  --port "${PORT}"
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}"
)

if [[ -n "${MAX_MODEL_LEN:-}" ]]; then
  ARGS+=(--max-model-len "${MAX_MODEL_LEN}")
fi

if [[ -n "${AMD_VLLM_API_KEY:-}" ]]; then
  ARGS+=(--api-key "${AMD_VLLM_API_KEY}")
else
  echo "WARNING: AMD_VLLM_API_KEY is not set." >&2
  echo "The server will accept unauthenticated requests on ${HOST}:${PORT}." >&2
  echo "That is fine while it's only reachable from localhost inside the notebook." >&2
  echo "Set AMD_VLLM_API_KEY before exposing this port beyond localhost / an authenticated tunnel." >&2
fi

echo "Starting vLLM OpenAI-compatible server: model=${AMD_VLLM_MODEL} host=${HOST} port=${PORT}"
echo "Command: python -m vllm.entrypoints.openai.api_server ${ARGS[*]}"

exec python -m vllm.entrypoints.openai.api_server "${ARGS[@]}"
