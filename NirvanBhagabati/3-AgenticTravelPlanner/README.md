# Agentic Travel Planner

A Streamlit chatbot that helps you plan 3-day trips to popular cities using intelligent agents and simulated data.

---

## Features

- **Natural Language Understanding:** Uses spaCy for parsing travel requests and interests.
- **Trip Planning:** Generates 3-day itineraries based on your interests (culture, food, history, shopping, nature).
- **Simulated Data:** Uses hardcoded data for attractions, weather, flights, and accommodations.
- **API Ready:** Supports integration with OpenWeatherMap and Google Places APIs (simulated if not configured).
- **Chat Interface:** Interactive chat for easy trip planning.

---

## Installation

1. **Install requirements:** pip install streamlit spacy requests
2. **Download the spaCy language model:** python -m spacy download en_core_web_sm

---

## Usage

1. **Run the app:** streamlit run app.py
2. **Type your request:**  Plan a trip to Tokyo for food and culture.

---

## Project Structure

- `AgenticTravelPlanner.py` – Main application script
- `requirements.txt` – List of required packages

---

## Notes

- **Simulated Mode:** Weather and attractions use hardcoded data if API keys are not provided.
- **API Integration:** Add your own API keys for real-time data.
- **Chat Interface:** Designed for easy, interactive trip planning.
