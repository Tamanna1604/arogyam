import streamlit as st
from pathlib import Path
import openai
import os  # For environment variables
from googletrans import Translator
from geopy.geocoders import Nominatim
import requests
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import re  # For regular expression matching

# Configure OpenAI with API key (use environment variable for security)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("API Key not found! Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# Initialize the translator
translator = Translator()

# OpenAI System Prompt
system_prompt = """
As a highly skilled medical practitioner specializing in image analysis, you are tasked with examining medical images for a renowned hospital. Your expertise is crucial in identifying any anomalies, diseases, or health issues that may be present in the image.

Your Responsibility:

1. **Give the name of the disease as the heading in bold letters.**
2. **Detailed Analysis:** Thoroughly analyze each image, focusing on identifying any abnormal findings.
3. **Findings Report:** Document all observed anomalies or signs of disease. Clearly articulate these findings in a structured format.
4. **Recommendations and Next Steps:** Based on your analysis, suggest potential next steps, including further tests or treatments as applicable.
5. **Treatment Suggestions:** If appropriate, recommend possible treatment options or interventions.

Important Notes:

- Scope of Response: Only respond if the image pertains to human health issues.
- Clarity of Images: In cases where the image quality impedes clear analysis, note that certain aspects are 'Unable to be determined based on the provided image'.
- Disclaimer: Accompany your analysis with a disclaimer: "Consult with a doctor before making any decisions."
- Your insights are valuable in guiding clinical decisions. Please proceed with the analysis, adhering to the structured approach outlined above.

Please provide me an output response with these four headings: **Detailed Analysis**, **Findings Report**, **Recommendations and Next Steps**, **Treatment Suggestions**.
"""

# Function to get AI-generated response from OpenAI
def get_ai_analysis(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use "gpt-3.5-turbo" if GPT-4 is unavailable
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            api_key=api_key
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

# Function to fetch user's approximate location
def get_user_location():
    try:
        response = requests.get("https://ipinfo.io")
        data = response.json()
        return data.get("city", "Unknown")
    except Exception:
        return "Unknown"

# Map location to default language
def get_default_language(location):
    location_language_map = {
        "Delhi": "Hindi",
        "Mumbai": "Hindi",
        "Chennai": "Tamil",
        "Kolkata": "Bengali",
        "Hyderabad": "Telugu",
        "Bangalore": "Kannada",
        "Ahmedabad": "Gujarati",
        "Pune": "Marathi",
        "Thiruvananthapuram": "Malayalam",
        "Amritsar": "Punjabi",
    }
    return location_language_map.get(location, "English")  # Default to English

# Function to extract the disease name from AI response
def extract_disease_name(text):
    pattern = r"\*\*(.*?)\*\*"  # Regex to find bold text (disease name)
    match = re.search(pattern, text)
    return match.group(1) if match else "Unknown Disease"

# Function to convert text to speech
def speak(text):
    tts = gTTS(text=text, lang="en")
    tts.save("output.mp3")
    st.audio("output.mp3", format="audio/mp3")

# Function to fetch nearest hospital and area details
def get_nearest_hospital(location):
    geolocator = Nominatim(user_agent="myApp")
    location_obj = geolocator.geocode(location)

    if location_obj:
        lat, lon = location_obj.latitude, location_obj.longitude
        reverse = geolocator.reverse((lat, lon), language='en')
        area = reverse.raw.get('address', {}).get('suburb', 'Unknown Area')
        
        hospital_details = {
            "name": "City Medical Center",
            "area": area,
            "phone": "+1-234-567-8901"
        }
        return hospital_details
    return None

# Function to give speech dictation for analysis
def give_speech_dictation(disease_name, urgency, hospital_details):
    response = f"Disease: {disease_name}, Urgency of treatment: {urgency}. "
    speak(response)
    st.write(response)

# Page configuration
st.set_page_config(page_title="Aarogyam", page_icon=":robot:")

# Display logo (only if file exists)
if Path("health-logo.png").exists():
    st.image("health-logo.png", width=200)

st.title("Aarogyam")
st.subheader("An AI application that helps people understand diseases by analyzing medical images.")

# File uploader
uploaded_file = st.file_uploader("Upload the image for analysis", type=["png", "jpg", "jpeg"])

# Initialize session state
if "generated_text" not in st.session_state:
    st.session_state["generated_text"] = ""

# Get user location and language
user_location = get_user_location()
default_language = get_default_language(user_location)

if uploaded_file:
    st.image(uploaded_file, width=200, caption="Uploaded image")
    analyze_button = st.button("Analyze!")

    if analyze_button:
        image_data = uploaded_file.getvalue()
        prompt_parts = f"Analyze this medical image and provide findings: {system_prompt}"

        st.header("Analysis on the basis of the provided image:")
        response_text = get_ai_analysis(prompt_parts)
        st.session_state["generated_text"] = response_text
        st.write(st.session_state["generated_text"])

        # Extract disease name and urgency
        disease_name = extract_disease_name(st.session_state["generated_text"])
        urgency = "High"  # Could be dynamically extracted

        # Get nearest hospital details
        hospital_details = get_nearest_hospital(user_location)
        if hospital_details:
            give_speech_dictation(disease_name, urgency, hospital_details)
        else:
            st.write("Unable to find nearby hospitals.")

# Translation options
if st.session_state["generated_text"]:
    st.header("Translate the Analysis:")
    languages = {
        "English": "en",
        "Hindi": "hi",
        "Bengali": "bn",
        "Tamil": "ta",
        "Telugu": "te",
        "Marathi": "mr",
        "Gujarati": "gu",
        "Kannada": "kn",
        "Malayalam": "ml",
        "Punjabi": "pa",
    }

    st.write(f"Detected Location: **{user_location}**")

    selected_language = st.selectbox(
        "Select a language to translate", list(languages.keys()), index=list(languages.keys()).index(default_language)
    )

    translate_button = st.button("Translate")

    if translate_button:
        translated_text = translator.translate(
            st.session_state["generated_text"], src="en", dest=languages[selected_language]
        ).text
        st.write(f"Translated Text in {selected_language}:")
        st.write(translated_text)
