"""
LLM Service - Handles LLM interactions with Hugging Face models.
"""

import logging
from typing import Any, Dict, List, Optional
import os

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with local Hugging Face LLM models.
    
    Supports:
    - ChatGPT OSS 20B from Hugging Face
    - Other Hugging Face models
    - Local model loading and inference
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

        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.pipeline: Optional[Any] = None
        self._initialized = False

    def _determine_device(self, device: str) -> str:
        """Determine the device to use."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"  # Apple Silicon
            else:
                return "cpu"
        return device

    def initialize(self) -> None:
        """Initialize the model and tokenizer."""
        if self._initialized:
            return

        logger.info(f"Loading model: {self.model_name} on device: {self.device}")

        try:
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
            logger.info("Model loaded successfully")

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

