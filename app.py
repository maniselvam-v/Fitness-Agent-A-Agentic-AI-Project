import streamlit as st
from dotenv import load_dotenv
import os
from agents.planner import FitnessPlanner
from utils.pdf_generator import create_fitness_plan_pdf
import json
import re
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

planner = FitnessPlanner(google_api_key=GOOGLE_API_KEY)

def apply_plan_modifications(plan_type, modifications, current_workout_plan, current_nutrition_plan, current_weekly_schedule):
    updated_workout_plan = current_workout_plan
    updated_nutrition_plan = current_nutrition_plan
    updated_weekly_schedule = current_weekly_schedule
    feedback_message = []

    for mod in modifications:
        target = mod.get("target", "")
        value = mod.get("value", "")
        change_type = mod.get("change_type", "")
        details = mod.get("details", "")

        if plan_type == "workout":
            if change_type == "adjust_duration":

                if value in updated_workout_plan:
                    updated_workout_plan = updated_workout_plan.replace(
                        value, f"{value} ({details})"
                    )
                    feedback_message.append(f"Workout plan for {value} adjusted: {details}.")
                else:
                    feedback_message.append(f"Could not find '{value}' in workout plan to adjust.")
            elif change_type == "suggest_alternative":
                if value in updated_workout_plan:
                    updated_workout_plan = updated_workout_plan.replace(
                        value, details
                    )
                    feedback_message.append(f"Workout plan alternative for {value} suggested: {details}.")
                else:
                    feedback_message.append(f"Could not find '{value}' in workout plan to suggest alternative.")

        elif plan_type == "nutrition":
            if change_type == "suggest_alternative" or change_type == "remove" or change_type == "replace":

                if value in updated_nutrition_plan:

                    lines = updated_nutrition_plan.split('\n')
                    for i, line in enumerate(lines):
                        if value in line:
                            if change_type == "remove":
                                lines[i] = "" 
                                feedback_message.append(f"Nutrition meal '{value}' removed.")
                            elif change_type == "suggest_alternative" or change_type == "replace":
                                lines[i] = f"{details}" 
                                feedback_message.append(f"Nutrition meal '{value}' replaced with '{details}'.")
                            break
                    updated_nutrition_plan = '\n'.join([line for line in lines if line]) 
                else:
                    feedback_message.append(f"Could not find '{value}' in nutrition plan to suggest alternative/remove.")

        elif plan_type == "schedule":
            if change_type == "adjust":

                updated_weekly_schedule += f"\n\nNote: {details}"
                feedback_message.append(f"Weekly schedule adjusted: {details}.")

    return updated_workout_plan, updated_nutrition_plan, updated_weekly_schedule, "; ".join(feedback_message)

st.set_page_config(
    page_title="FitMate AI Coach",
    page_icon="💪",
    layout="wide"
)

st.title("FitMate AI Fitness Coach")
st.markdown("""
Your personal AI-powered fitness coach that creates customized workout and nutrition plans
based on your goals and preferences.
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Your Profile")
    
    age = st.number_input("Age", min_value=16, max_value=100, value=30)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
    height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
    
    activity_level = st.selectbox(
        "Activity Level",
        ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"]
    )
    
    st.subheader("Your Goals")
    goal = st.selectbox(
        "Primary Goal",
        ["Lose Weight", "Build Muscle", "Improve Fitness", "Maintain Weight"]
    )
    
    preferences = st.multiselect(
        "Preferences",
        ["Vegetarian", "Vegan", "No Gym Access", "Home Workouts Only", "Time Constrained"]
    )
    
    generate_plan = st.button("Generate My Plan", type="primary")

if generate_plan:
    if not GOOGLE_API_KEY:
        st.error("GOOGLE_API_KEY not found. Please set it in your .env file.")
    else:
        with st.spinner("Generating your personalized plan..."):
            workout_plan, nutrition_plan = planner.generate_plan(
                age, gender, weight, height, activity_level, goal, preferences
            )
            if "Error" in workout_plan or "Error" in nutrition_plan:
                st.error("An error occurred while generating your plans. Please check the logs for details.")
                st.session_state.workout_plan = None
                st.session_state.nutrition_plan = None
                st.session_state.weekly_schedule = None
            else:
                st.session_state.workout_plan = workout_plan
                st.session_state.nutrition_plan = nutrition_plan
                weekly_schedule = planner.generate_weekly_schedule(workout_plan, nutrition_plan)
                if "Error" in weekly_schedule:
                    st.error("An error occurred while generating your weekly schedule. Please check the logs for details.")
                    st.session_state.weekly_schedule = None
                else:
                    st.session_state.weekly_schedule = weekly_schedule
        st.success("Plan Generated!")

if "workout_plan" in st.session_state and st.session_state.workout_plan:
    st.header("Your Personalized Plan")
    
    tab1, tab2, tab3 = st.tabs(["Workout Plan", "Nutrition Plan", "Weekly Schedule"])
    
    with tab1:
        st.subheader("Workout Plan")
        st.markdown(st.session_state.workout_plan)
        
    with tab2:
        st.subheader("Nutrition Plan")
        st.markdown(st.session_state.nutrition_plan)
        
    with tab3:
        st.subheader("Weekly Schedule")
        st.markdown(st.session_state.weekly_schedule)

    # PDF Download Button (remains outside tabs but within the plan display block)
    pdf_buffer = create_fitness_plan_pdf(
        st.session_state.workout_plan,
        st.session_state.nutrition_plan,
        st.session_state.weekly_schedule
    )
    st.download_button(
        label="Download Plan as PDF",
        data=pdf_buffer,
        file_name="FitMate_Personalized_Plan.pdf",
        mime="application/pdf"
    )

else:
    st.info("👈 Fill in your details in the sidebar and click 'Generate My Plan' to get started!")

st.divider()

st.header("Chat with FitMate")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask FitMate a question..."):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("FitMate is thinking..."):
        # Prepare context for the chat agent
        context = {
            "workout_plan": st.session_state.get("workout_plan", "Not yet generated."),
            "nutrition_plan": st.session_state.get("nutrition_plan", "Not yet generated."),
            "weekly_schedule": st.session_state.get("weekly_schedule", "Not yet generated."),
        }

        response = planner.chat_response(prompt, st.session_state.messages, context)

    # Attempt to parse response as direct JSON first (if AI doesn't wrap in markdown)
    modification_applied = False
    try:
        modification_data = json.loads(response) # Try parsing the whole response as JSON
        logging.info("Attempting to parse response as direct JSON.")

        action = modification_data.get("action")
        plan_type = modification_data.get("plan_type")
        modifications = modification_data.get("modifications", [])

        if action == "modify_plan" and plan_type and modifications:
            logging.info(f"Direct JSON modification request detected for {plan_type} plan.")
            (updated_workout, updated_nutrition, updated_schedule, feedback_msg) = \
                apply_plan_modifications(
                    plan_type, modifications,
                    st.session_state.get("workout_plan", ""),
                    st.session_state.get("nutrition_plan", ""),
                    st.session_state.get("weekly_schedule", "")
                )
            
            st.session_state.workout_plan = updated_workout
            st.session_state.nutrition_plan = updated_nutrition
            st.session_state.weekly_schedule = updated_schedule

            with st.chat_message("assistant"):
                st.success(f"Plan Updated! {feedback_msg}")
            st.session_state.messages.append({"role": "assistant", "content": f"Plan Updated! {feedback_msg}"})
            st.experimental_rerun() # Rerun to update the displayed plans immediately
            modification_applied = True
        else:
            logging.info("Direct JSON parsed but not a recognized modification action.")
            pass # If it's JSON but not a recognized modification, just treat as regular chat for now.
    except json.JSONDecodeError:
        logging.info("Response is not direct JSON. Checking for markdown JSON block.")
        pass # Not direct JSON, proceed to check for markdown JSON block
    except Exception as e:
        logging.error(f"Error processing direct JSON response: {e}")
        with st.chat_message("assistant"):
            st.markdown("An error occurred while processing a potential plan adjustment. Please check logs for details.")
        st.session_state.messages.append({"role": "assistant", "content": "An error occurred while processing a potential plan adjustment. Please check logs for details."})
        modification_applied = True # Prevent further processing if an error occurred during direct JSON handling

    if not modification_applied: # Only proceed if no modification was applied by direct JSON parsing
        # Check if the response contains a JSON modification request wrapped in markdown
        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL) # Corrected regex
        if json_match:
            try:
                json_content = json_match.group(1)
                logging.info(f"Markdown JSON block detected. Content: {json_content[:200]}...") # Log snippet
                modification_data = json.loads(json_content)
                action = modification_data.get("action")
                plan_type = modification_data.get("plan_type")
                modifications = modification_data.get("modifications", [])

                if action == "modify_plan" and plan_type and modifications:
                    logging.info(f"Markdown JSON modification request detected for {plan_type} plan.")
                    (updated_workout, updated_nutrition, updated_schedule, feedback_msg) = \
                        apply_plan_modifications(
                            plan_type, modifications,
                            st.session_state.get("workout_plan", ""),
                            st.session_state.get("nutrition_plan", ""),
                            st.session_state.get("weekly_schedule", "")
                        )
                    
                    st.session_state.workout_plan = updated_workout
                    st.session_state.nutrition_plan = updated_nutrition
                    st.session_state.weekly_schedule = updated_schedule

                    with st.chat_message("assistant"):
                        st.success(f"Plan Updated! {feedback_msg}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Plan Updated! {feedback_msg}"})
                    
                    st.experimental_rerun() # Rerun to update the displayed plans immediately
                else:
                    logging.info("Markdown JSON parsed but not a recognized modification action.")
                    with st.chat_message("assistant"):
                        st.markdown("I understood your request for a plan modification, but the structure was not recognized. Please try rephrasing.")
                    st.session_state.messages.append({"role": "assistant", "content": "I understood your request for a plan modification, but the structure was not recognized. Please try rephrasing."})
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON from AI response wrapped in markdown: {e}")
                with st.chat_message("assistant"):
                    st.markdown("I received a malformed response (JSON in markdown) when trying to adjust your plan. Please try again or rephrase your request.")
                st.session_state.messages.append({"role": "assistant", "content": "I received a malformed response (JSON in markdown) when trying to adjust your plan. Please try again or rephrase your request."})
            except Exception as e:
                logging.error(f"Error applying plan modifications from markdown JSON: {e}")
                with st.chat_message("assistant"):
                    st.markdown("An unexpected error occurred while trying to apply plan adjustments from markdown JSON. Please check the logs for details.")
                st.session_state.messages.append({"role": "assistant", "content": "An unexpected error occurred while trying to apply plan adjustments from markdown JSON. Please check the logs for details."})
        else:
            logging.info("Response is not a recognized JSON modification; treating as regular chat.")
            # Display assistant response in chat message container for regular chat
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response}) 