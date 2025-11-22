"""
LLM Service - Handles LLM interactions with Hugging Face models and GGUF files.
"""

import logging
from typing import Any, Dict, List, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing transformers (for Hugging Face models)
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Try importing llama-cpp-python (for GGUF models)
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False


class LLMService:
    """
    Service for interacting with local LLM models.
    
    Supports:
    - GGUF models (via llama-cpp-python)
    - Hugging Face models (via transformers)
    - ChatGPT OSS 20B and similar models
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-7B-Instruct",
        model_path: Optional[str] = None,
        device: str = "auto",
        temperature: float = 0.1,
        max_tokens: int = 4000,
        trust_remote_code: bool = True,
    ):
        self.model_name = model_name
        self.model_path = model_path or model_name
        self.device = self._determine_device(device)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.trust_remote_code = trust_remote_code

        # Detect if model is GGUF format
        self.is_gguf = self._is_gguf_model()
        
        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.pipeline: Optional[Any] = None
        self.llama_model: Optional[Any] = None
        self._initialized = False

    def _is_gguf_model(self) -> bool:
        """Check if the model path points to a GGUF file."""
        if not self.model_path:
            return False
        model_path_obj = Path(self.model_path)
        if model_path_obj.exists() and model_path_obj.suffix.lower() == ".gguf":
            return True
        # Also check if it's a string ending in .gguf
        if isinstance(self.model_path, str) and self.model_path.lower().endswith(".gguf"):
            return True
        return False

    def _determine_device(self, device: str) -> str:
        """Determine the device to use."""
        if device == "auto":
            if TRANSFORMERS_AVAILABLE:
                if torch.cuda.is_available():
                    return "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    return "mps"  # Apple Silicon
            return "cpu"
        return device

    def initialize(self) -> None:
        """Initialize the model and tokenizer."""
        if self._initialized:
            return

        logger.info(f"Loading model: {self.model_path} (GGUF: {self.is_gguf}) on device: {self.device}")

        try:
            if self.is_gguf:
                # Load GGUF model using llama-cpp-python
                if not LLAMA_CPP_AVAILABLE:
                    raise ImportError("llama-cpp-python is required for GGUF models. Install it with: pip install llama-cpp-python")
                
                if not Path(self.model_path).exists():
                    raise FileNotFoundError(f"GGUF model file not found: {self.model_path}")
                
                logger.info(f"Loading GGUF model from: {self.model_path}")
                self.llama_model = Llama(
                    model_path=self.model_path,
                    n_ctx=self.max_tokens,  # Context window
                    n_threads=None,  # Auto-detect CPU threads
                    verbose=False,
                )
                self._initialized = True
                logger.info("GGUF model loaded successfully")
            else:
                # Load Hugging Face model
                if not TRANSFORMERS_AVAILABLE:
                    raise ImportError("transformers is required for Hugging Face models. Install it with: pip install transformers torch")
                
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_path,
                    trust_remote_code=self.trust_remote_code,
                )

                # Load model
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    trust_remote_code=self.trust_remote_code,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map=self.device if self.device != "cpu" else None,
                    low_cpu_mem_usage=True,
                )

                # Create pipeline for text generation
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if self.device == "cuda" else -1,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )

                self._initialized = True
                logger.info("Hugging Face model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def generate(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop_sequences: Sequences to stop generation at
            
        Returns:
            Generated text
        """
        if not self._initialized:
            self.initialize()

        max_new_tokens = max_new_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            if self.is_gguf and self.llama_model:
                # Generate using GGUF model
                response = self.llama_model(
                    prompt,
                    max_tokens=max_new_tokens,
                    temperature=temperature,
                    stop=stop_sequences if stop_sequences else [],
                )
                generated_text = response["choices"][0]["text"]
            else:
                # Generate using Hugging Face model
                # Format prompt for chat models
                if self.tokenizer and hasattr(self.tokenizer, "apply_chat_template"):
                    messages = [{"role": "user", "content": prompt}]
                    formatted_prompt = self.tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                else:
                    formatted_prompt = prompt

                # Generate
                outputs = self.pipeline(
                    formatted_prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    return_full_text=False,
                    pad_token_id=self.tokenizer.eos_token_id if self.tokenizer else None,
                )

                generated_text = outputs[0]["generated_text"]

            # Apply stop sequences if provided
            if stop_sequences:
                for stop_seq in stop_sequences:
                    if stop_seq in generated_text:
                        generated_text = generated_text.split(stop_seq)[0]

            return generated_text.strip()

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    def generate_batch(
        self,
        prompts: List[str],
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> List[str]:
        """Generate text for multiple prompts."""
        return [self.generate(p, max_new_tokens, temperature) for p in prompts]

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "device": self.device,
            "initialized": self._initialized,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

