import streamlit as st
import spacy
import requests
import json
import random
from collections import deque
from langchain.memory import ConversationEntityMemory
from langchain.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_community.graphs import Neo4jGraph
import os
from langchain_core.messages import HumanMessage, SystemMessage

# --- Configuration for APIs (Replace with your actual keys if you use real ones) ---
# For a real project, store these securely (e.g., environment variables)
# If you don't use real keys, the app will use hardcoded/simulated data.
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY" # Get from https://openweathermap.org/api
GOOGLE_PLACES_API_KEY = "YOUR_GOOGLE_PLACES_API_KEY" # Get from Google Cloud Console (Places API)

class TravelPlannerAgent:

    def periodic_refresh(self):
        if len(self.context_buffer) >= self.context_buffer.maxlen:
            summary = self._summarize_buffer()
            self.vector_store.add_texts([summary])
            self.context_buffer.clear()
    # Optionally update entities or clean vector store

    def _summarize_buffer(self) -> str:
        """Summarize the context buffer for long-term storage"""
        buffer_text = " ".join(self.context_buffer)
        if len(buffer_text) > 100:
            return "Conversation summary: " + buffer_text[:100] + "..."
        return "Conversation summary: " + buffer_text
    
    def __init__(self):

        self.topic_graph = Neo4jGraph(
            url=os.getenv("NEO4J_URL"),
            username="neo4j",
            password=os.getenv("NEO4J_PASSWORD")
        )
        self._init_topic_graph()

        self.vector_store = Chroma(
            collection_name="travel_facts",  # Use fixed name
            embedding_function=GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=os.getenv("GEMINI_API_KEY"))
        )

        self.context_buffer = deque(maxlen=5)
        
        self.entity_memory = ConversationEntityMemory(
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=os.getenv("GEMINI_API_KEY"))
        )

        # Add LLM instance
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )

        # Load spaCy NLP model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            # print("SpaCy model loaded successfully.") # Suppress this print in Streamlit
        except OSError:
            # st.warning("SpaCy 'en_core_web_sm' model not found. Please run: python -m spacy download en_core_web_sm")
            # st.warning("Proceeding without advanced NLP capabilities.")
            self.nlp = None

    def _init_topic_graph(self):
        # Create lightweight topic schema
        self.topic_graph.query("""
        CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE
        """)

    def _is_memorizable(self, text: str) -> bool:
        """Determine if text contains important facts"""
        keywords = [
            "prefer", "like", "dislike", "always", "never",
            "allergy", "diet", "require", "need", "must"
        ]
        return any(kw in text.lower() for kw in keywords)

    def _update_topic_graph(self, text: str):
        """
        Extracts simple topics from user input and updates the Neo4j topic graph.
        This is a lightweight, rule-based implementation.
        """
        # Define a set of topics to look for (expand as needed)
        topics = {"culture", "food", "history", "shopping", "nature", "adventure", "relaxation"}
        found_topics = [t for t in topics if t in text.lower()]

        for topic in found_topics:
            # For now, use a single user node 'default'
            self.topic_graph.query(
                "MERGE (t:Topic {name: $topic}) "
                "MERGE (u:User {id: 'default'}) "
                "MERGE (u)-[:INTERESTED_IN]->(t)",
                {"topic": topic}
            )

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
                if ent.label_ == "GPE":
                    destination = ent.text.lower()
                    # Standardize "दिल्ली" to "delhi" key if it was detected by GPE for user-friendliness
                    if destination == "दिल्ली":
                        destination = "delhi"
                    break # Assuming one destination per request for simplicity
            
            # Fallback for destination if NER doesn't catch it but it's in supported_cities
            if not destination:
                user_input_lower = user_input.lower()

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

    def recall_context(self):
        return "\n".join(self.context_buffer)

    def recall_topics(self):
        result = self.topic_graph.query(
            "MATCH (u:User {id: 'default'})-[:INTERESTED_IN]->(t:Topic) RETURN t.name AS topic"
        )
        return [record['topic'] for record in result]

    def plan_trip(self, user_input):
        """
        Orchestrates the agents and API calls to plan a trip.
        """
        # print(f"\n--- Processing your request: '{user_input}' ---") # Suppress print
        
        # Agent 1: Understand Request (NLP/Parsing)
        request_params = self.understand_request(user_input)

        destination = request_params["destination"]
        if not destination:
            prompt = f"Extract only the city name from this travel request: '{user_input}'. Return only the city name."
            response = self.llm.invoke([HumanMessage(content=prompt)])
            destination = response.content.strip().lower()
        
            # Update request_params with Gemini-extracted destination
            request_params["destination"] = destination
            
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

        # Update context buffer with the latest conversation turn
        self.context_buffer.append(f"User: {user_input}")
        self.context_buffer.append(f"Agent: {full_plan}")
        
        self._update_topic_graph(user_input)

        # Add memorizable inputs to vector store
        if self._is_memorizable(user_input):
            self.vector_store.add_texts([user_input])
        
        # Update entity memory
        self.entity_memory.save_context(
            {"input": user_input},
            {"output": full_plan}
        )

        # Maintenance
        if random.random() < 0.2:
            self.periodic_refresh()
        
        entities = self.entity_memory.load_memory_variables({"input": user_input})['history']
        # Retrieve relevant facts using vector search
        facts = self.vector_store.similarity_search(user_input, k=3)

        # Retrieve topics from the topic graph
        topics = self.recall_topics()
        # Extract mobility restrictions safely
        mobility_restrictions = (
            entities.get("mobility") 
            if isinstance(entities, dict) 
            else "None specified"
        )
        dates = request_params['dates']
        budget = request_params['budget']

        # Add to prompt construction
        personalization = ""
        if isinstance(entities, dict) and "food" in entities.get("interests", []):
            personalization += "- Include 2 food experiences per day\n"
        if isinstance(entities, dict) and "history" in entities.get("interests", []):
            personalization += "- Prioritize historical sites\n"
        
        constraints = f"""
        Constraints:
        - Dates: {dates}
        - Budget: {budget}
        - Mobility: {mobility_restrictions}
        """
        
        # Construct LLM prompt with memory context
        prompt = f"""
        **Travel Planning Task**
        Destination: {destination}
        Dates: {dates}
        Budget: {budget}
        Weather: {weather}

        **User Profile**
        Stated Interests: {user_input}
        Historical Preferences: {entities}
        Relevant Facts: {facts}
        Related Topics: {topics}

        **Personalization Requirements**
        {personalization}

        **Constraints**
        {constraints}

        **Output Format**
        1. 3-day hourly itinerary
        2. For each activity: 
           - Why it matches user's profile
           - Estimated cost
        """
    
        # Generate response with LLM
        messages = [
            SystemMessage(content="You're a travel expert specialized in personalized itineraries"),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        full_plan = response.content
        
        return full_plan

# --- Streamlit UI ---

st.set_page_config(page_title="Agentic Travel Planner", layout="wide")

st.title("✈️ Agentic Travel Planner")
st.markdown("Plan your next adventure to **your desired city** with the help of intelligent agents!")

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
    2. **Specify a city**.
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