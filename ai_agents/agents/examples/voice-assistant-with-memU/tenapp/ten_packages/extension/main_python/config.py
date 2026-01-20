from pydantic import BaseModel


class MainControlConfig(BaseModel):
    greeting: str = "Hello, I am your AI assistant."
    # Memory configuration (Zep)
    agent_id: str = "agent001"
    agent_name: str = "Voice Assistant with Memory"
    user_id: str = "user001"
    user_name: str = "Tim Smith"
    zep_api_key: str = ""  # Zep API key, can also be set via ZEP_API_KEY environment variable
    enable_memorization: bool = True
