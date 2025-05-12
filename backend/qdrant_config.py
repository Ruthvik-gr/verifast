import os

# Set this to "memory" to use in-memory Qdrant
# Set this to "server" to use Qdrant server
os.environ["QDRANT_MODE"] = "memory"
