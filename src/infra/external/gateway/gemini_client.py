from __future__ import annotations

import os
from functools import lru_cache

import google.genai as genai
from dotenv import load_dotenv


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not defined.")
    return genai.Client(api_key=api_key)
