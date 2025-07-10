from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import re

def create_fitness_plan_pdf(workout_plan, nutrition_plan, weekly_schedule):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    flowables = []

    # Title
    flowables.append(Paragraph("FitMate AI Fitness Plan", styles['h1']))
    flowables.append(Spacer(1, 0.2 * 100)) # Add vertical space

    # Workout Plan
    flowables.append(Paragraph("Workout Plan", styles['h2']))
    workout_plan_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', workout_plan)
    workout_plan_html = workout_plan_html.replace('\n', '<br/>')
    flowables.append(Paragraph(workout_plan_html, styles['Normal']))
    flowables.append(Spacer(1, 0.2 * 100))

    # Nutrition Plan
    flowables.append(Paragraph("Nutrition Plan", styles['h2']))
    nutrition_plan_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', nutrition_plan)
    nutrition_plan_html = nutrition_plan_html.replace('\n', '<br/>')
    flowables.append(Paragraph(nutrition_plan_html, styles['Normal']))
    flowables.append(Spacer(1, 0.2 * 100))

    # Weekly Schedule
    flowables.append(Paragraph("Weekly Schedule", styles['h2']))
    weekly_schedule_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', weekly_schedule)
    weekly_schedule_html = weekly_schedule_html.replace('\n', '<br/>')
    flowables.append(Paragraph(weekly_schedule_html, styles['Normal']))
    flowables.append(Spacer(1, 0.2 * 100))

    doc.build(flowables)
    buffer.seek(0)
    return buffer.getvalue() 