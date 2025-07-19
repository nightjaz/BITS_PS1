import streamlit as st
import spacy
import requests
import json
import random

# --- Configuration for APIs (Replace with your actual keys if you use real ones) ---
# For a real project, store these securely (e.g., environment variables)
# If you don't use real keys, the app will use hardcoded/simulated data.
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY" # Get from https://openweathermap.org/api
GOOGLE_PLACES_API_KEY = "YOUR_GOOGLE_PLACES_API_KEY" # Get from Google Cloud Console (Places API)


class TravelPlannerAgent:
    def __init__(self):
        # Load spaCy NLP model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            # print("SpaCy model loaded successfully.") # Suppress this print in Streamlit
        except OSError:
            # st.warning("SpaCy 'en_core_web_sm' model not found. Please run: python -m spacy download en_core_web_sm")
            # st.warning("Proceeding without advanced NLP capabilities.")
            self.nlp = None

        # Hardcoded data for fallback/example (used if APIs are not configured or simulated)
        self.hardcoded_attractions = {
            "paris": {
                "culture": ["Louvre Museum", "Eiffel Tower (Culture/Iconic)", "Notre Dame Cathedral"],
                "food": ["Experience a Parisian bistro", "Try French crepes", "Visit a local patisserie"],
                "history": ["Palace of Versailles (day trip)", "Les Invalides (Napoleon's Tomb)", "Latin Quarter"],
                "shopping": ["Champs-Élysées", "Galleries Lafayette"],
                "default": ["Walk along the Seine", "Explore Montmartre", "Visit a local market"]
            },
            "tokyo": {
                "culture": ["Senso-ji Temple", "Meiji Jingu Shrine", "Ghibli Museum (advance booking needed)"],
                "food": ["Shinjuku Golden Gai (food & drink)", "Tsukiji Outer Market", "Authentic Ramen experience"],
                "history": ["Imperial Palace East Garden", "Edo-Tokyo Museum"],
                "shopping": ["Shibuya Crossing & Hachiko Statue", "Ginza Shopping Street"],
                "default": ["Explore Akihabara (electronics/anime)", "Visit a themed cafe"]
            },
            "rome": {
                "culture": ["Colosseum & Roman Forum", "Vatican City (St. Peter's Basilica)", "Borghese Gallery"],
                "food": ["Traditional Roman Pizza", "Authentic Italian Gelato", "Pasta making class"],
                "history": ["Pantheon", "Trevi Fountain", "Catacombs of Rome"],
                "shopping": ["Via del Corso"],
                "default": ["Wander through Trastevere", "Visit the Spanish Steps"]
            },
            # --- NEW CITIES ADDED BELOW ---
            "barcelona": {
                "culture": ["Sagrada Familia", "Park Güell", "Gothic Quarter", "Picasso Museum"],
                "food": ["La Boqueria Market", "Try Tapas in El Born", "Seafood Paella by the beach"],
                "history": ["Gothic Quarter", "Sagrada Familia (history/architecture)", "Casa Batlló", "Montjuïc Castle"],
                "shopping": ["Passeig de Gràcia", "El Born boutiques", "Mercat de Sant Antoni"],
                "nature": ["Parc de la Ciutadella", "Montjuïc Hill", "Barceloneta Beach"],
                "default": ["Stroll La Rambla", "Explore Gràcia neighborhood"]
            },
            "delhi": {
                "culture": ["India Gate", "Lotus Temple", "Akshardham Temple", "National Museum"],
                "food": ["Chandni Chowk street food", "Try Chole Bhature", "Kebabs from Old Delhi"],
                "history": ["Red Fort", "Humayun's Tomb", "Qutub Minar", "India Gate"],
                "shopping": ["Sarojini Nagar Market", "Janpath Market", "Dilli Haat", "Connaught Place"],
                "nature": ["Lodhi Garden", "Garden of Five Senses", "Sunder Nursery"],
                "default": ["Explore Old Delhi", "Visit Connaught Place"]
            }
        }
        # Update supported cities to include the new ones
        self.supported_cities = list(self.hardcoded_attractions.keys())

    def understand_request(self, user_input):
        """
        Agent for advanced parsing using SpaCy NLP.
        Extracts destination, approximate dates, and interests.
        """
        destination = None
        dates = "your specified dates" # Still a placeholder for simplicity unless robust date parsing is added
        interests = []
        travel_style = []

        if self.nlp:
            doc = self.nlp(user_input)

            # Try to find a destination using NER (Named Entity Recognition for GPE - Geopolitical Entity)
            for ent in doc.ents:
                # Check for direct match with city names, also handling "Delhi" vs "दिल्ली"
                if ent.label_ == "GPE" and (ent.text.lower() in self.supported_cities or ent.text.lower() == "delhi"):
                    destination = ent.text.lower()
                    # Standardize "दिल्ली" to "delhi" key if it was detected by GPE for user-friendliness
                    if destination == "दिल्ली":
                        destination = "delhi"
                    break # Assuming one destination per request for simplicity
            
            # Fallback for destination if NER doesn't catch it but it's in supported_cities
            if not destination:
                user_input_lower = user_input.lower()
                for city_key in self.supported_cities:
                    if city_key in user_input_lower:
                        destination = city_key
                        break


            # More granular keyword matching or custom entity recognition for interests
            keywords_to_interests = {
                "culture": ["culture", "museums", "art", "gallery", "iconic", "architecture", "spiritual"],
                "food": ["food", "eat", "restaurant", "cuisine", "taste", "street food", "local dishes"],
                "history": ["history", "ancient", "historical", "ruins", "old", "monuments", "tombs", "forts"],
                "shopping": ["shop", "shopping", "boutiques", "markets", "crafts", "souvenirs"],
                "nature": ["nature", "parks", "gardens", "beach", "hill", "outdoor"], # Added for Barcelona/Delhi
                "adventure": ["adventure", "hike", "thrill", "explore"], # Example for future expansion
                "relaxation": ["relax", "beach", "spa", "chill"] # Example for future expansion
            }

            user_input_lower = user_input.lower()
            for interest_type, keywords in keywords_to_interests.items():
                if any(keyword in user_input_lower for keyword in keywords):
                    interests.append(interest_type)

            # Default interest if none are found
            if not interests:
                interests.append("default")

        else: # Fallback to basic string matching if SpaCy failed to load
            # print("Using basic string matching for request understanding.") # Suppress print
            user_input_lower = user_input.lower()
            for city in self.supported_cities:
                if city in user_input_lower:
                    destination = city
                    break

            if "culture" in user_input_lower or "art" in user_input_lower: interests.append("culture")
            if "food" in user_input_lower or "eat" in user_input_lower: interests.append("food")
            if "history" in user_input_lower or "ancient" in user_input_lower: interests.append("history")
            if "shop" in user_input_lower: interests.append("shopping")
            if "nature" in user_input_lower or "park" in user_input_lower or "garden" in user_input_lower or "beach" in user_input_lower: interests.append("nature")
            if not interests: interests.append("default")


        return {
            "destination": destination,
            "dates": dates,
            "budget": "your specified budget",
            "interests": interests
        }

    def get_weather_data(self, city):
        """
        Simulates fetching weather data using OpenWeatherMap API.
        Requires an API key.
        """
        if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":
            # print("OpenWeatherMap API key not configured. Simulating weather data.") # Suppress print
            simulated_weather = {
                "paris": "Mild and cloudy, around 18°C.",
                "tokyo": "Warm and humid, occasional rain, around 25°C.",
                "rome": "Sunny and hot, around 30°C.",
                "barcelona": "Pleasant and sunny, around 22°C.", # Simulated
                "delhi": "Hot and dry, around 38°C." # Simulated
            }
            return simulated_weather.get(city.lower(), "Weather information not available.")

        base_url = "http://api.openweathermap.org/data/2.5/weather?"
        complete_url = f"{base_url}q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        try:
            response = requests.get(complete_url, timeout=5) # Add timeout
            response.raise_for_status() # Raise an exception for HTTP errors
            data = response.json()
            if data["cod"] == 200:
                main_data = data["main"]
                weather_data = data["weather"][0]
                temp = main_data["temp"]
                description = weather_data["description"]
                return f"Current weather: {description.capitalize()}, {temp}°C."
            else:
                return f"Could not retrieve weather for {city}. Error: {data.get('message', 'Unknown error')}"
        except requests.exceptions.RequestException as e:
            # print(f"Error fetching weather for {city}: {e}") # Suppress print
            return f"Weather data currently unavailable for {city}."
        except json.JSONDecodeError:
            # print(f"Error decoding JSON for weather data for {city}.") # Suppress print
            return f"Weather data currently unavailable for {city}."


    def get_places_of_interest(self, destination, interests):
        """
        Simulates fetching points of interest using a Places API (e.g., Google Places).
        Requires an API key and more complex setup for real use.
        """
        # Ensure destination is lowercase to match dictionary keys
        destination = destination.lower() 

        if not GOOGLE_PLACES_API_KEY or GOOGLE_PLACES_API_KEY == "YOUR_GOOGLE_PLACES_API_KEY":
            # print("Google Places API key not configured. Using hardcoded attractions.") # Suppress print
            # Fallback to hardcoded attractions if API key is not set
            selected_attractions = []
            if destination in self.hardcoded_attractions:
                for interest in interests:
                    if interest in self.hardcoded_attractions[destination]:
                        selected_attractions.extend(self.hardcoded_attractions[destination][interest])
                    elif "default" in self.hardcoded_attractions[destination]:
                        selected_attractions.extend(self.hardcoded_attractions[destination]["default"])
                return list(set(selected_attractions)) # Return unique items
            else:
                return [] # No hardcoded data for this destination

        # --- Conceptual API call for Google Places (simplified) ---
        # A real Places API call would be more complex, needing coordinates, radius, types, etc.
        # This is purely illustrative of where an API call would go.
        # print(f"Attempting to fetch places for {destination} with interests {interests} via Places API (conceptual)...") # Suppress print
        # Example API endpoint (this is not a working URL for demo purposes)
        # base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        # query = f"{' '.join(interests)} attractions in {destination}"
        # params = {
        #      "query": query,
        #      "key": GOOGLE_PLACES_API_KEY
        # }
        #
        # try:
        #      response = requests.get(base_url, params=params, timeout=10)
        #      response.raise_for_status()
        #      data = response.json()
        #      if data.get("status") == "OK" and data.get("results"):
        #          return [place["name"] for place in data["results"][:5]] # Get top 5
        #      else:
        #          print(f"No places found via API for {destination} or API error: {data.get('status')}")
        #          return self.hardcoded_attractions[destination].get(interests[0], []) # Fallback
        # except requests.exceptions.RequestException as e:
        #      print(f"Error fetching places for {destination}: {e}")
        #      return self.hardcoded_attractions[destination].get(interests[0], []) # Fallback


        # Since we're not actually making the Google Places API call live for a demo,
        # we'll always fall back to the hardcoded data even if a key is provided,
        # to ensure the demo runs without needing live credentials.
        selected_attractions = []
        if destination in self.hardcoded_attractions:
            for interest in interests:
                if interest in self.hardcoded_attractions[destination]:
                    selected_attractions.extend(self.hardcoded_attractions[destination][interest])
                elif "default" in self.hardcoded_attractions[destination]:
                    selected_attractions.extend(self.hardcoded_attractions[destination]["default"])
        return list(set(selected_attractions)) # Return unique items

    def generate_itinerary(self, params, attractions):
        """
        Agent to create a 3-day itinerary from fetched attractions.
        """
        destination = params.get("destination")
        itinerary_days = []

        if not attractions:
            return "No attractions found for this destination or your specified interests."

        # Shuffle attractions to provide variety in itinerary generation
        random.shuffle(attractions)

        # Distribute attractions over 3 days (approx. 2-3 per day)
        num_days = 3
        activities_per_day = 2 # Or 3 if enough activities
        total_activities = len(attractions)
        
        # Ensure we don't try to assign more activities than available
        if total_activities < num_days * activities_per_day:
            activities_per_day = max(1, total_activities // num_days)

        current_activity_index = 0
        for day in range(1, num_days + 1):
            day_activities = []
            for _ in range(activities_per_day):
                if current_activity_index < total_activities:
                    day_activities.append(attractions[current_activity_index])
                    current_activity_index += 1
                else:
                    break # No more activities

            if not day_activities and current_activity_index >= total_activities:
                day_activities.append("Relax and explore on your own.")
            elif not day_activities: # Should not happen if activities_per_day is calculated correctly or activities_pool is not empty
                    day_activities.append("Further exploration based on your interests.")

            itinerary_days.append(f"Day {day}: {', '.join(day_activities)}")

        return "\n".join(itinerary_days)

    def get_flight_info(self, destination, dates):
        """
        Simulates getting flight information (conceptual API call).
        A real implementation would involve specific flight APIs (e.g., Skyscanner, Kayak APIs).
        """
        # print(f"Simulating flight search for {destination} on {dates}...") # Suppress print
        # In a real scenario, this would involve a complex API call to a flight aggregator
        # and parsing live flight data.
        mock_flights = {
            "paris": "Flights typically range from $600-$1200 USD round trip, depending on origin and booking time.",
            "tokyo": "Flights often range from $800-$1500 USD round trip, but can vary greatly.",
            "rome": "Flights usually range from $500-$1000 USD round trip.",
            "barcelona": "Flights typically range from $550-$1100 USD round trip.", # Simulated
            "delhi": "Flights often range from $700-$1400 USD round trip." # Simulated
        }
        return mock_flights.get(destination.lower(), "Flight information conceptual (check major airlines or aggregators).")

    def get_accommodation_info(self, destination, budget):
        """
        Simulates getting accommodation information (conceptual API call).
        A real implementation would involve hotel booking APIs (e.g., Booking.com, Expedia APIs).
        """
        # print(f"Simulating accommodation search for {destination} within {budget}...") # Suppress print
        # In a real scenario, this would involve a complex API call to a hotel booking site
        # and parsing live hotel availability and prices.
        mock_accommodation = {
            "paris": "Consider charming boutique hotels in Le Marais or Saint-Germain-des-Prés, or more budget-friendly options near public transport hubs.",
            "tokyo": "Look for modern hotels in Shinjuku, Shibuya, or traditional ryokans for a unique experience.",
            "rome": "Stay near the historical center for easy access to sights, or explore lively Trastevere for nightlife.",
            "barcelona": "Explore hotels in Gothic Quarter for history, or near Barceloneta for beach access.", # Simulated
            "delhi": "Consider hotels in Connaught Place for central access, or boutique stays in Hauz Khas Village." # Simulated
        }
        return mock_accommodation.get(destination.lower(), "Accommodation information conceptual (check hotel booking sites).")


    def plan_trip(self, user_input):
        """
        Orchestrates the agents and API calls to plan a trip.
        """
        # print(f"\n--- Processing your request: '{user_input}' ---") # Suppress print
        
        # Agent 1: Understand Request (NLP/Parsing)
        request_params = self.understand_request(user_input)

        destination = request_params["destination"]
        if not destination:
            return "I couldn't identify a valid destination in your request. Please specify Paris, Tokyo, Rome, Barcelona, or Delhi."
            
        # print(f"Understood request for: {destination.capitalize()}, Interests: {', '.join(request_params['interests'])}") # Suppress print

        # Agent 2: Fetch External Data (API Calls)
        weather = self.get_weather_data(destination)
        attractions = self.get_places_of_interest(destination, request_params["interests"])
        flights = self.get_flight_info(destination, request_params["dates"])
        accommodation = self.get_accommodation_info(destination, request_params["budget"])

        # Agent 3: Generate Itinerary (using fetched data)
        itinerary = self.generate_itinerary(request_params, attractions)

        # Compile the full plan
        full_plan = f"**--- Your Personalized Trip Plan to {destination.capitalize()} ---**\n"
        full_plan += f"**Dates:** {request_params['dates']}\n"
        full_plan += f"**Budget:** {request_params['budget']}\n"
        full_plan += f"**Weather in {destination.capitalize()}:** {weather}\n\n"
        full_plan += "**Proposed Itinerary:**\n"
        full_plan += itinerary
        full_plan += "\n\n**Recommendations:**\n"
        full_plan += f"**Flights:** {flights}\n"
        full_plan += f"**Accommodation:** {accommodation}\n"
        full_plan += "\n\nEnjoy your planning and your trip!"

        return full_plan

# --- Streamlit UI ---

st.set_page_config(page_title="Agentic Travel Planner", layout="wide")

st.title("✈️ Agentic Travel Planner")
st.markdown("Plan your next adventure to **Paris, Tokyo, Rome, Barcelona, or Delhi** with the help of intelligent agents!")

# Initialize the TravelPlannerAgent
if 'planner' not in st.session_state:
    st.session_state.planner = TravelPlannerAgent()
    if st.session_state.planner.nlp is None:
        st.warning("SpaCy 'en_core_web_sm' model not found. Please run `python -m spacy download en_core_web_sm` in your terminal for better NLP capabilities.")
        st.warning("Proceeding with basic keyword matching.")


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hello! I can help you plan a 3-day trip. Tell me where you'd like to go and what your interests are."})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Tell me your travel plans (e.g., 'Plan a trip to Barcelona for culture and food')"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.planner.plan_trip(prompt)
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

st.sidebar.header("How to Use:")
st.sidebar.markdown(
    """
    1. **Type your request** in the chat input at the bottom.
    2. **Specify a city** from the supported list: Paris, Tokyo, Rome, Barcelona, Delhi.
    3. **Mention your interests** (e.g., culture, food, history, shopping, nature).
    4. The agent will generate a 3-day itinerary and provide recommendations.
    """
)
st.sidebar.subheader("Example Queries:")
st.sidebar.markdown("- `Plan a trip to Tokyo for food and culture.`")
st.sidebar.markdown("- `I want to go to Rome, focusing on history and ancient ruins.`")
st.sidebar.markdown("- `Suggest an adventure trip to Barcelona, maybe some nature.`")
st.sidebar.markdown("- `What are some shopping and historical places in Delhi?`")

st.sidebar.subheader("Notes:")
st.sidebar.info("This is a demo. API keys for real-time weather and places are not configured, so simulated data is used.")