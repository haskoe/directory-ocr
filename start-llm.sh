#!/bin/bash

llama-server \
  -m ~/models/Qwen3VL-8B-Instruct-Q8_0.gguf \
  --mmproj ~/models/mmproj-Qwen3VL-8B-Instruct-F16.gguf \
  --ctx-size 8192 \
  --batch-size 256 \
  --ubatch-size 256 \
  --gpu-layers 99 \
#  -fa on
# -ctk q4_0 -ctv q4_0
  --host 0.0.0.0 --port 8080 &  

llama-server \
  -m ~/models/gemma-2-2b-it-q8_0.gguf \
  --port 8081 \
  --ctx-size 4096 \
  --gpu-layers 99 \
  --no-mmap \
  -fa on \
  --host 0.0.0.0
