# Import Base first
from app.database import Base

# Import all your models
from auth.models import User, APIKey
from prompts.models import Prompt, PromptVersion, Project
