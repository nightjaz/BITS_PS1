# Agentic Travel Planner

A Streamlit chatbot designed to help users plan personalized 3-day trips, leveraging an agent-based architecture, various external data sources (conceptual APIs), and Google Gemini models for intelligent recommendations and itinerary generation. Also implemented memory management feature so as to account for users previous interests. 

---

## Features

-   **Personalized Itineraries:** Generates 3-day travel plans based on user preferences and interests.
-   **Intelligent Agents:** Utilizes an agentic approach for understanding requests, fetching data, and generating itineraries.
-   **Context Management:** Employs Neo4j for a topic graph and ChromaDB for a vector store to manage conversation context and long-term memory.
-   **NLP Capabilities:** Integrates SpaCy for advanced natural language processing to extract key information from user inputs.
-   **External Data Integration:** Conceptual integrations for weather data (OpenWeatherMap) and points of interest (Google Places), with fallback to simulated data if API keys are not configured.
-   **LLM Integration:** Powered by Google Gemini 1.5 Flash and Gemini 2.5 Flash for conversational intelligence and response generation.
-   **Streamlit UI:** Provides an interactive and user-friendly web interface for planning trips.

---

1.  **Install requirements:**
    Ensure you have Python 3.8+ installed. It's recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    (You will need to create a `requirements.txt` file. See the "Dependencies" section below for common packages.)

2.  **Download SpaCy NLP model:**
    ```bash
    python -m spacy download en_core_web_sm
    ```

3.  **Set Environment Variables for API Keys and Credentials:**
    For secure operation, it is **crucial** to set the following environment variables. If these are not set, the application will use simulated data for weather and places of interest.

    * `OPENWEATHER_API_KEY`: Get from [OpenWeatherMap API](https://openweathermap.org/api)
    * `GOOGLE_PLACES_API_KEY`: Get from [Google Cloud Console (Places API)](https://console.cloud.google.com/apis/library/places-api.googleapis.com)
    * `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
    * `NEO4J_URL`: Your Neo4j database URL (e.g., `bolt://localhost:7687` or a cloud instance URL)
    * `NEO4J_USERNAME`: Your Neo4j username (e.g., `neo4j`)
    * `NEO4J_PASSWORD`: Your Neo4j database password

    **Example (for temporary session on Linux/macOS):**
    ```bash
    export OPENWEATHER_API_KEY="your_openweather_key"
    export GOOGLE_PLACES_API_KEY="your_google_places_key"
    export GEMINI_API_KEY="your_gemini_key"
    export NEO4J_URL="bolt://your_neo4j_url:7687"
    export NEO4J_USERNAME="neo4j"
    export NEO4J_PASSWORD="your_neo4j_password"
    ```
    For permanent setup or deployment, refer to your operating system's documentation or platform-specific instructions (e.g., GitHub Secrets, Streamlit Community Cloud Secrets).

---

## Dependencies (for `requirements.txt`)

Based on `PLM_final.py`, your `requirements.txt` should include: