"""
Configuration settings for FitMate
"""

# API Keys
OPENAI_API_KEY = "abc"  # API key

# Application Settings
APP_NAME = "FitMate AI Coach"
APP_VERSION = "0.1.0"

# File Paths
DATA_DIR = "data"
WORKOUT_TEMPLATES_PATH = f"{DATA_DIR}/workouts/templates.json"
NUTRITION_TEMPLATES_PATH = f"{DATA_DIR}/nutrition/templates.json"

# Default Settings
DEFAULT_EXPERIENCE_LEVEL = "beginner"
DEFAULT_WORKOUT_DAYS = ["monday", "wednesday", "friday"]
DEFAULT_REST_DAYS = ["tuesday", "thursday", "saturday", "sunday"]

# Workout Settings
WORKOUT_TYPES = {
    "beginner": ["full_body", "upper_body", "lower_body"],
    "intermediate": ["push", "pull", "legs"],
    "advanced": ["chest", "back", "shoulders", "arms", "legs"]
}

# Nutrition Settings
DIET_TYPES = ["standard", "vegetarian", "vegan"]
MEAL_TYPES = ["breakfast", "lunch", "dinner", "snacks"]

# Activity Level Multipliers
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "lightly active": 1.375,
    "moderately active": 1.55,
    "very active": 1.725,
    "extra active": 1.9
} 
