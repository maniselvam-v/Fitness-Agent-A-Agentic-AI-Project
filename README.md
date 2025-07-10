# FitMate: AI Fitness Coach

An intelligent fitness coaching system that creates personalized workout and nutrition plans using AI agents.

## Features

- Personalized workout and nutrition planning
- Goal-based program generation
- Daily check-ins and progress tracking
- Adaptive planning based on user feedback

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## Project Structure

```
fitmate/
├── app.py                 # Main Streamlit application
├── agents/               # AI agent implementations
│   ├── planner.py        # Main planning agent
│   └── tools.py          # Agent tools and utilities
├── data/                 # Data storage and templates
│   ├── workouts/         # Workout templates
│   └── nutrition/        # Nutrition guidelines
├── utils/               # Utility functions
│   ├── tdee.py          # TDEE calculator
│   └── formatters.py    # Output formatting utilities
└── config.py            # Configuration settings
```

## MVP Features

- Basic workout plan generation
- Simple nutrition guidelines
- TDEE calculation
- Goal-based planning

## Future Enhancements

- Multi-agent system
- Real-time form feedback
- Advanced progress tracking
- Integration with fitness APIs 