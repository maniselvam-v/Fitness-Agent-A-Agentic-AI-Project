"""
Main planning agent for generating workout and nutrition plans
"""
from typing import Dict, List
import json
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from utils.tdee import calculate_tdee
from langchain_core.messages import HumanMessage, AIMessage
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class FitnessPlanner:
    def __init__(self, google_api_key):
        self.llm = ChatGoogleGenerativeAI(google_api_key=google_api_key, model="gemini-2.0-flash", temperature=0.7)
        
        self.workout_prompt_template = PromptTemplate(
            input_variables=["age", "gender", "weight", "height", "activity_level", "goal", "preferences", "tdee"],
            template="""
            Generate a personalized workout plan based on the following user details. Do not include any introductory or conversational text. Provide only the plan content.
            User Details:
            - Age: {age}
            - Gender: {gender}
            - Weight: {weight} kg
            - Height: {height} cm
            - Activity Level: {activity_level}
            - Fitness Goal: {goal}
            - Preferences: {preferences}
            - Estimated Daily Calorie Needs (TDEE): {tdee} calories

            Workout Plan Guidelines:
            - Create a 3-day per week workout plan (e.g., Monday, Wednesday, Friday).
            - For each workout day, include 5-7 exercises.
            - Specify sets and repetitions for each exercise (e.g., 3 sets of 10-12 reps).
            - Include a warm-up and cool-down section for each day.
            - Consider the user's preferences (e.g., "No Gym Access" means bodyweight exercises or home equipment).
            - Output the workout plan in a structured, readable format. Do not use markdown tables.
            """
        )

        self.nutrition_prompt_template = PromptTemplate(
            input_variables=["age", "gender", "weight", "height", "activity_level", "goal", "preferences", "tdee"],
            template="""
            Generate a personalized nutrition plan based on the following user details. Do not include any introductory or conversational text. Provide only the plan content.
            User Details:
            - Age: {age}
            - Gender: {gender}
            - Weight: {weight} kg
            - Height: {height} cm
            - Activity Level: {activity_level}
            - Fitness Goal: {goal}
            - Preferences: {preferences}
            - Estimated Daily Calorie Needs (TDEE): {tdee} calories

            Nutrition Plan Guidelines:
            - Create a daily meal plan including Breakfast, Lunch, Dinner, and 1-2 Snacks.
            - Provide estimated calorie and macronutrient (protein, carbs, fat) breakdown for each meal.
            - Consider the user's preferences (e.g., "Vegetarian", "Vegan").
            - Suggest simple, easy-to-prepare meals.
            - Output the nutrition plan in a structured, readable format. Do not use markdown tables.
            """
        )

        self.plan_adjustment_prompt_template = PromptTemplate(
            input_variables=["user_request", "workout_plan", "nutrition_plan", "weekly_schedule"],
            template="""
            You are FitMate, an AI fitness coach. Your primary task is to interpret a user's request for a plan modification and **ABSOLUTELY MUST** output a JSON object describing the change.
            **CRITICAL: YOUR ENTIRE RESPONSE MUST BE A SINGLE JSON OBJECT INSIDE A MARKDOWN CODE BLOCK (```json...```). DO NOT INCLUDE ANY OTHER TEXT WHATSOEVER (NO GREETINGS, NO EXPLANATIONS, NO APOLOGIES, NO CONVERSATIONAL FILLERS).**
            For `suggest_alternative` changes, you **ARE REQUIRED** to use your general knowledge about common food or exercise substitutions to provide a suitable alternative. You are not limited to items explicitly mentioned in the provided plans.
            If you genuinely cannot fulfill a request (e.g., if it's illogical or impossible), you must still output the JSON with `change_type: "cannot_fulfill"` and provide a brief, direct reason in `details`.

            Here are the current plans:
            Workout Plan: {workout_plan}
            Nutrition Plan: {nutrition_plan}
            Weekly Schedule: {weekly_schedule}

            User's Request: {user_request}

            Output the modification as a JSON object inside a markdown code block. The JSON should have the following structure:
            '''json
            {{
              "action": "modify_plan",
              "plan_type": "workout" | "nutrition" | "schedule",
              "modifications": [
                {{
                  "target": "day" | "meal" | "exercise" | "general",
                  "value": "[Specific item/day to be changed/removed/replaced, e.g., 'Oatmeal', 'Monday']",
                  "change_type": "remove" | "add" | "replace" | "adjust_duration" | "adjust_sets_reps" | "suggest_alternative" | "cannot_fulfill",
                  "details": "[Specific details of the change, e.g., 'reduce to 20 minutes', 'Scrambled eggs with spinach and whole-wheat toast', 'Reason for not fulfilling']"
                }}
              ]
            }}
            '''

            Example 1 (Workout adjustment - reduce duration for Tuesday): 
            '''json
            {{
              "action": "modify_plan",
              "plan_type": "workout",
              "modifications": [
                {{
                  "target": "day",
                  "value": "Tuesday",
                  "change_type": "adjust_duration",
                  "details": "Reduce workout duration to 30 minutes"
                }}
              ]
            }}
            '''

            Example 2 (Nutrition adjustment - suggest alternative for Breakfast):
            '''json
            {{
              "action": "modify_plan",
              "plan_type": "nutrition",
              "modifications": [
                {{
                  "target": "meal",
                  "value": "Breakfast",
                  "change_type": "suggest_alternative",
                  "details": "Greek yogurt with berries and granola."
                }}
              ]
            }}
            '''
            Example 3 (Weekly Schedule - general adjustment):
            '''json
            {{
              "action": "modify_plan",
              "plan_type": "schedule",
              "modifications": [
                {{
                  "target": "general",
                  "value": "",
                  "change_type": "adjust",
                  "details": "Move Monday's workout to Tuesday due to a conflict."
                }}
              ]
            }}
            '''
            Example 4 (Cannot fulfill request):
            '''json
            {{
              "action": "modify_plan",
              "plan_type": "nutrition",
              "modifications": [
                {{
                  "target": "meal",
                  "value": "Unicorn Tears",
                  "change_type": "cannot_fulfill",
                  "details": "Cannot suggest an alternative for 'Unicorn Tears' as it is not a recognized food item."
                }}
              ]
            }}
            '''
            """
        )

        self.workout_chain = LLMChain(llm=self.llm, prompt=self.workout_prompt_template)
        self.nutrition_chain = LLMChain(llm=self.llm, prompt=self.nutrition_prompt_template)

    def generate_plan(self, age, gender, weight, height, activity_level, goal, preferences):
        try:
            tdee = calculate_tdee(age, gender, weight, height, activity_level)

            workout_plan = self.workout_chain.run(
                age=age, gender=gender, weight=weight, height=height,
                activity_level=activity_level, goal=goal, preferences=preferences, tdee=round(tdee)
            )
            
            nutrition_plan = self.nutrition_chain.run(
                age=age, gender=gender, weight=weight, height=height,
                activity_level=activity_level, goal=goal, preferences=preferences, tdee=round(tdee)
            )

            return workout_plan, nutrition_plan
        except Exception as e:
            logging.error(f"Error generating fitness plans: {e}")
            return "Error generating workout plan.", "Error generating nutrition plan."

    def generate_weekly_schedule(self, workout_plan, nutrition_plan):
        try:
            # This is a simplified example. A more advanced implementation might parse
            # the workout and nutrition plans to create a structured schedule.
            schedule_prompt_template = PromptTemplate(
                input_variables=["workout_plan", "nutrition_plan"],
                template="""
                Generate a structured weekly schedule combining the following workout and nutrition plans. Do not include any introductory or conversational text. Provide only the schedule content.

                Workout Plan:
                {workout_plan}

                Nutrition Plan:
                {nutrition_plan}

                Weekly Schedule Guidelines:
                - Create a schedule for 7 days (Monday to Sunday).
                - Integrate workout days and rest days clearly.
                - For each day, include main meals (Breakfast, Lunch, Dinner) and snacks, referencing the nutrition plan.
                - Provide a concise overview for each day.
                - Output the weekly schedule in a structured, readable format. Do not use markdown tables.
                """
            )
            schedule_chain = LLMChain(llm=self.llm, prompt=schedule_prompt_template)
            weekly_schedule = schedule_chain.run(
                workout_plan=workout_plan,
                nutrition_plan=nutrition_plan
            )
            return weekly_schedule
        except Exception as e:
            logging.error(f"Error generating weekly schedule: {e}")
            return "Error generating weekly schedule."

    def chat_response(self, user_message, chat_history, context):
        try:
            # Check if the user's message is a request for plan modification
            modification_keywords = ["modify", "change", "adjust", "update", "suggest alternative for", "remove", "add", "replace"]
            is_modification_request = any(keyword in user_message.lower() for keyword in modification_keywords)

            if is_modification_request:
                logging.info(f"User requested plan modification: {user_message}")
                # Use the dedicated prompt for plan adjustments
                adjustment_chain = LLMChain(llm=self.llm, prompt=self.plan_adjustment_prompt_template)
                json_response = adjustment_chain.run(
                    user_request=user_message,
                    workout_plan=context.get('workout_plan', 'Not available.'),
                    nutrition_plan=context.get('nutrition_plan', 'Not available.'),
                    weekly_schedule=context.get('weekly_schedule', 'Not available.')
                )
                return json_response
            else:
                messages = []
                # Add a system message or initial prompt for the AI to understand its role
                system_message_content = (
                    "You are FitMate, an AI fitness coach. Your primary goal is to assist users with their fitness journey."
                    "You have access to the user's currently generated Workout Plan, Nutrition Plan, and Weekly Schedule."
                    "**Always refer to these plans directly when answering questions about workouts, nutrition, or scheduling.**"
                    "Keep your responses concise, helpful, and directly relevant to the provided plans or general fitness knowledge."
                    "If a user asks about a specific day, exercise, or meal, extract the information from the relevant plan."
                    "Do not make up information that is not in the plans."
                    f"\n\nGenerated Workout Plan: {context['workout_plan']}"
                    f"\n\nGenerated Nutrition Plan: {context['nutrition_plan']}"
                    f"\n\nGenerated Weekly Schedule: {context['weekly_schedule']}"
                )
                messages.append(HumanMessage(content=system_message_content))

                for msg in chat_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
                
                messages.append(HumanMessage(content=user_message))

                response = self.llm.invoke(messages)
                return response.content
        except Exception as e:
            logging.error(f"Error in chat response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."

class PlannerAgent:
    def __init__(self):
        self.workout_templates = self._load_workout_templates()
        self.nutrition_templates = self._load_nutrition_templates()
    
    def _load_workout_templates(self) -> Dict:
        """Load workout templates from JSON file"""
        # TODO: Implement actual template loading
        return {
            "beginner": {
                "full_body": [
                    {"exercise": "Push-ups", "sets": 3, "reps": "10-12"},
                    {"exercise": "Squats", "sets": 3, "reps": "12-15"},
                    {"exercise": "Plank", "sets": 3, "reps": "30s"},
                ],
                "upper_body": [
                    {"exercise": "Push-ups", "sets": 3, "reps": "10-12"},
                    {"exercise": "Dumbbell Rows", "sets": 3, "reps": "12-15"},
                    {"exercise": "Shoulder Press", "sets": 3, "reps": "10-12"},
                ],
                "lower_body": [
                    {"exercise": "Squats", "sets": 3, "reps": "12-15"},
                    {"exercise": "Lunges", "sets": 3, "reps": "10-12 each"},
                    {"exercise": "Glute Bridges", "sets": 3, "reps": "12-15"},
                ]
            }
        }
    
    def _load_nutrition_templates(self) -> Dict:
        """Load nutrition templates from JSON file"""
        # TODO: Implement actual template loading
        return {
            "vegetarian": {
                "breakfast": [
                    "Greek yogurt with berries and granola",
                    "Oatmeal with banana and nuts",
                    "Avocado toast with eggs"
                ],
                "lunch": [
                    "Quinoa bowl with roasted vegetables",
                    "Lentil soup with whole grain bread",
                    "Mediterranean salad with chickpeas"
                ],
                "dinner": [
                    "Tofu stir-fry with brown rice",
                    "Vegetable curry with quinoa",
                    "Stuffed bell peppers with rice and beans"
                ]
            }
        }
    
    def generate_workout_plan(self, 
                            goal: str,
                            preferences: List[str],
                            experience_level: str = "beginner") -> Dict:
        """
        Generate a weekly workout plan based on user's goal and preferences
        """
        plan = {
            "monday": self._get_workout("full_body", experience_level),
            "wednesday": self._get_workout("upper_body", experience_level),
            "friday": self._get_workout("lower_body", experience_level)
        }
        
        # Add rest days
        plan["tuesday"] = {"type": "rest", "notes": "Active recovery - light walking or stretching"}
        plan["thursday"] = {"type": "rest", "notes": "Active recovery - light walking or stretching"}
        plan["saturday"] = {"type": "rest", "notes": "Complete rest day"}
        plan["sunday"] = {"type": "rest", "notes": "Complete rest day"}
        
        return plan
    
    def _get_workout(self, workout_type: str, experience_level: str) -> Dict:
        """Get a specific workout template"""
        return {
            "type": workout_type,
            "exercises": self.workout_templates[experience_level][workout_type]
        }
    
    def generate_nutrition_plan(self,
                              macros: Dict,
                              preferences: List[str]) -> Dict:
        """
        Generate a daily nutrition plan based on macros and preferences
        """
        diet_type = "vegetarian" if "Vegetarian" in preferences else "standard"
        
        return {
            "breakfast": self._get_meal("breakfast", diet_type),
            "lunch": self._get_meal("lunch", diet_type),
            "dinner": self._get_meal("dinner", diet_type),
            "snacks": [
                "Greek yogurt with berries",
                "Handful of nuts",
                "Protein shake"
            ],
            "macros": macros
        }
    
    def _get_meal(self, meal_type: str, diet_type: str) -> str:
        """Get a specific meal template"""
        return self.nutrition_templates[diet_type][meal_type][0]  