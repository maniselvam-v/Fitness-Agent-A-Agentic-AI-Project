"""
TDEE (Total Daily Energy Expenditure) Calculator
"""

def calculate_bmr(weight, height, age, gender):
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation
    weight in kg, height in cm, age in years
    """
    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return bmr

def get_activity_multiplier(activity_level):
    """
    Get activity multiplier based on activity level
    """
    multipliers = {
        "sedentary": 1.2,  # Little or no exercise
        "lightly active": 1.375,  # Light exercise 1-3 days/week
        "moderately active": 1.55,  # Moderate exercise 3-5 days/week
        "very active": 1.725,  # Hard exercise 6-7 days/week
        "extra active": 1.9,  # Very hard exercise & physical job
    }
    return multipliers.get(activity_level.lower(), 1.2)

def calculate_tdee(age, gender, weight_kg, height_cm, activity_level):
    # Mifflin-St Jeor Equation for BMR
    if gender == "Male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:  # Female
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    # Activity Multipliers
    # Sedentary: little or no exercise
    # Lightly Active: light exercise/sports 1-3 days/week
    # Moderately Active: moderate exercise/sports 3-5 days/week
    # Very Active: hard exercise/sports 6-7 days/week
    # Extra Active: very hard exercise/physical job
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Extra Active": 1.9,
    }

    tdee = bmr * activity_multipliers.get(activity_level, 1.2) # Default to sedentary
    return tdee

def calculate_macros(tdee, goal, weight):
    """
    Calculate macronutrient targets based on TDEE and goal
    Returns: protein (g), carbs (g), fat (g)
    """
    if goal.lower() == "lose weight":
        calories = tdee - 500  # 500 calorie deficit
        protein = weight * 2.2  # 2.2g per kg of bodyweight
        fat = (calories * 0.25) / 9  # 25% of calories from fat
        carbs = (calories - (protein * 4) - (fat * 9)) / 4  # Remaining calories from carbs
    
    elif goal.lower() == "build muscle":
        calories = tdee + 300  # 300 calorie surplus
        protein = weight * 2.2  # 2.2g per kg of bodyweight
        fat = (calories * 0.25) / 9  # 25% of calories from fat
        carbs = (calories - (protein * 4) - (fat * 9)) / 4  # Remaining calories from carbs
    
    else:  # maintain weight
        calories = tdee
        protein = weight * 1.8  # 1.8g per kg of bodyweight
        fat = (calories * 0.25) / 9  # 25% of calories from fat
        carbs = (calories - (protein * 4) - (fat * 9)) / 4  # Remaining calories from carbs
    
    return {
        "calories": round(calories),
        "protein": round(protein),
        "carbs": round(carbs),
        "fat": round(fat)
    } 