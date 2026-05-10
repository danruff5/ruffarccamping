#Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Force Ollama to use NVIDIA GPU (GPU 0 in Task Manager)
$env:CUDA_VISIBLE_DEVICES = "0"

python -m uvicorn backend.main:app