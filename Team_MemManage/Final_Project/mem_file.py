import os
import json
import datetime
from collections import deque
from typing import Optional, Dict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.memory import ConversationEntityMemory
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.graphs import Neo4jGraph
import re # Ensure 're' is imported for regex operations (used for JSON parsing now)

class MemoryManager:
    """
    Manages various types of memory for a conversational AI, designed to be general-purpose.

    Components:
    - Context Buffer (deque): Short-term memory for recent conversation turns.
    - Vector Store (Chroma): Long-term semantic memory for important facts/summaries.
    - Conversation Entity Memory (LangChain): Tracks entities and their history.
    - Neo4j Graph Database: Structured memory for user-defined topics/relationships.
    - Global User Profile (shared): For information persistent across all sessions in a run.
    """

    def __init__(self,
                 llm_for_entity_extraction: ChatOpenAI,
                 chroma_collection_name: str = "general_chatbot_facts",
                 graph_user_node_label: str = "User",
                 graph_user_node_id_property: str = "id",
                 graph_user_node_id_value: str = "default_user",
                 graph_topic_node_label: str = "Topic",
                 graph_topic_name_property: str = "name",
                 graph_relationship_type: str = "DISCUSSED",
                 domain_topics: Optional[set] = None,
                 memorizable_keywords: Optional[list] = None,
                 global_user_profile_ref: Optional[Dict] = None
                 ):
        self.llm_for_entity_extraction = llm_for_entity_extraction
        self.max_context_buffer_size = 5
        self.context_buffer = deque(maxlen=self.max_context_buffer_size)
        self.chroma_collection_name = chroma_collection_name
        self.persist_directory = "./chroma_db"
        self.embedding_model_name = "all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        try:
            self.vector_store = Chroma(
                collection_name=self.chroma_collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"ChromaDB initialized with collection: {self.chroma_collection_name}")
        except Exception as e:
            self.vector_store = None
            print(f"Warning: Could not initialize ChromaDB for collection '{self.chroma_collection_name}': {e}. Facts will not be persistently stored.")

        self.entity_memory = ConversationEntityMemory(llm=self.llm_for_entity_extraction)
        self.neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.graph_user_node_label = graph_user_node_label
        self.graph_user_node_id_property = graph_user_node_id_property
        self.graph_user_node_id_value = graph_user_node_id_value
        self.graph_topic_node_label = graph_topic_node_label
        self.graph_topic_name_property = graph_topic_name_property
        self.graph_relationship_type = graph_relationship_type
        self.domain_topics = domain_topics if domain_topics is not None else set()
        self.memorizable_keywords = memorizable_keywords if memorizable_keywords is not None else []
        self.neo4j_initialized = False
        self.topic_graph = None
        try:
            self.topic_graph = Neo4jGraph(
                url=self.neo4j_url,
                username=self.neo4j_username,
                password=self.neo4j_password
            )
            self.topic_graph.query(
                f"MERGE (u:{self.graph_user_node_label} "
                f"{{ {self.graph_user_node_id_property}: '{self.graph_user_node_id_value}' }}) RETURN u"
            )
            self.neo4j_initialized = True
            print(f"Neo4jGraph initialized for user: {self.graph_user_node_id_value}")
        except Exception as e:
            print(f"Warning: Could not connect to Neo4jGraph: {e}. Graph memory will not be available.")

        self.global_user_profile = global_user_profile_ref if global_user_profile_ref is not None else {}
        print(f"MemoryManager initialized for session: {self.graph_user_node_id_value}")

    def recall_information(self, user_input: str) -> dict:
        """
        Recalls relevant information from all memory types based on user input.
        """
        recalled_data = {}

        # 1. Recall from Conversation Entity Memory
        try:
            # Provide a dummy input string to avoid 'One input key expected got []' error
            entities = self.entity_memory.load_memory_variables(inputs={"input": user_input})
            recalled_data["entities"] = entities.get("entities", "No specific entities remembered yet.")
        except Exception as e:
            recalled_data["entities"] = f"Error recalling entities: {e}"

        # 2. Recall from Vector Store (semantic search)
        if self.vector_store:
            try:
                docs = self.vector_store.similarity_search(user_input, k=3)
                recalled_facts = "\n".join([doc.page_content for doc in docs]) if docs else "No relevant facts found."
                recalled_data["facts"] = recalled_facts
            except Exception as e:
                recalled_data["facts"] = f"Error recalling facts from vector store: {e}"
        else:
            recalled_data["facts"] = "Vector store not initialized."

        # 3. Recall from Neo4j Graph (topics discussed by this user)
        if self.neo4j_initialized and self.topic_graph:
            try:
                topics_query = (
                    f"MATCH (u:{self.graph_user_node_label} "
                    f"{{ {self.graph_user_node_id_property}: '{self.graph_user_node_id_value}' }})-"
                    f"[:{self.graph_relationship_type}]->(t:{self.graph_topic_node_label}) "
                    f"RETURN t.{self.graph_topic_name_property} AS topic_name"
                )
                topics_result = self.topic_graph.query(topics_query)
                recalled_topics = ", ".join([r['topic_name'] for r in topics_result]) if topics_result else "No particular topics identified yet."
                recalled_data["topics"] = recalled_topics
            except Exception as e:
                recalled_data["topics"] = f"Error recalling topics from Neo4j: {e}"
        else:
            recalled_data["topics"] = "Graph database not initialized."

        # 4. Add Global User Profile information
        # IMPORTANT: This passes the *actual* global_user_profile dictionary.
        # The Streamlit UI will display this directly.
        recalled_data["global_user_profile"] = json.dumps(self.global_user_profile) if self.global_user_profile else "No global user profile set."

        # 5. Add Context Buffer (recent turns)
        recalled_data["context_buffer"] = "\n".join(self.context_buffer) if self.context_buffer else "No recent context."

        return recalled_data
    
    def update_neo4j_with_entities(self):
        """
        Extracts entities from `ConversationEntityMemory` and updates the Neo4j graph.
        Handles escaping of single quotes for Cypher query insertion.
        """
        if not self.neo4j_initialized or not self.topic_graph:
            return

        try:
            current_entities = self.entity_memory.load_memory_variables(inputs={})
            entities_dict = current_entities.get("entities", {})

            for entity_name, entity_info in entities_dict.items():
                entity_label = "Entity"

                safe_entity_name = entity_name.replace("'", "''")
                safe_entity_info = entity_info.replace("'", "''")

                print(f"DEBUG: Processing entity: '{entity_name}' -> safe: '{safe_entity_name}'")
                query_merge = (
                    f"MERGE (e:{entity_label} {{name: '{safe_entity_name}'}})"
                    f"SET e.description = '{safe_entity_info}'"
                    f"RETURN e"
                )
                print(f"DEBUG: Neo4j MERGE Query = {query_merge}")
                self.topic_graph.query(query_merge)

                query_knows = (
                    f"MATCH (u:{self.graph_user_node_label} "
                    f"{{ {self.graph_user_node_id_property}: '{self.graph_user_node_id_value}' }}), "
                    f"(e:{entity_label} {{name: '{safe_entity_name}'}}) "
                    f"MERGE (u)-[:KNOWS]->(e)"
                )
                print(f"DEBUG: Neo4j KNOWS Query = {query_knows}")
                self.topic_graph.query(query_knows)

        except Exception as e:
            print(f"Error updating Neo4j with entities: {e}")

    def save_context(self, user_input: str, ai_response: str):
        """
        Saves the current conversation turn to all relevant memory components.
        """
        conversation_turn = f"User: {user_input}\nAI: {ai_response}"

        # 1. Add to Context Buffer (Short-term memory)
        self.context_buffer.append(conversation_turn)

        # 2. Update Conversation Entity Memory
        try:
            self.entity_memory.save_context(inputs={"input": user_input}, outputs={"output": ai_response})
        except Exception as e:
            print(f"Error saving context to entity memory: {e}")

        # 3. Add to Vector Store (Long-term memory) as a "fact"
        if self.vector_store:
            try:
                self.vector_store.add_texts([conversation_turn], metadatas=[{"source": "conversation"}])
            except Exception as e:
                print(f"Error adding text to vector store: {e}")

        # 4. Update Neo4j Graph with identified entities
        self.update_neo4j_with_entities()

        # 5. Identify and update topics in Neo4j based on user input and AI response
        if self.neo4j_initialized and self.topic_graph and self.domain_topics:
            combined_text = user_input + " " + ai_response
            for topic in self.domain_topics:
                if topic.lower() in combined_text.lower():
                    try:
                        # Escape single quotes for topic names as well
                        safe_topic = topic.replace("'", "''")
                        self.topic_graph.query(
                            f"MERGE (t:{self.graph_topic_node_label} "
                            f"{{ {self.graph_topic_name_property}: '{safe_topic}' }}) "
                            f"RETURN t"
                        )
                        # Make sure safe_user_node_id_value is defined or use self.graph_user_node_id_value
                        safe_user_node_id_value = self.graph_user_node_id_value.replace("'", "''")
                        self.topic_graph.query(
                            f"MATCH (u:{self.graph_user_node_label} "
                            f"{{ {self.graph_user_node_id_property}: '{safe_user_node_id_value}' }}), "
                            f"(t:{self.graph_topic_node_label} "
                            f"{{ {self.graph_topic_name_property}: '{safe_topic}' }}) "
                            f"MERGE (u)-[:{self.graph_relationship_type}]->(t)"
                        )
                        print(f"Linked user to topic: {topic}")
                    except Exception as e:
                        print(f"Error linking user to topic '{topic}' in Neo4j: {e}")

        # 6. Update Global User Profile using the LLM-based extractor
        self._update_global_user_profile(user_input)

    def periodic_refresh(self):
        """
        Performs periodic maintenance tasks on the memory components.
        - Summarizes context buffer to vector store if buffer is full.
        - Persists vector store.
        - Updates Neo4j with entities (re-runs entity extraction and graph updates).
        """
        if len(self.context_buffer) == self.max_context_buffer_size and self.vector_store:
            summary = "Summary of recent conversation:\n" + "\n".join(self.context_buffer)
            try:
                self.vector_store.add_texts([summary], metadatas=[{"source": "summary"}])
                self.vector_store.persist()
                self.context_buffer.clear()
                print("Context buffer summarized and added to vector store.")
            except Exception as e:
                print(f"Error summarizing context buffer: {e}")

        if self.vector_store:
            try:
                self.vector_store.persist()
            except Exception as e:
                print(f"Error persisting vector store: {e}")

        self.update_neo4j_with_entities()

    def replace_fact(self, key, new_value):
        """
        Completely replaces the field at `key` with `new_value`.
        For lists (like hobbies), this fully overwrites any existing values.
        """
        self.global_user_profile[key] = new_value

    def add_or_merge_fact(self, key, new_value):
        current_value = self.global_user_profile.get(key)
        if isinstance(new_value, list):
            if not isinstance(current_value, list):
                self.global_user_profile[key] = []
            merged = set(self.global_user_profile[key]) | set(new_value)
            self.global_user_profile[key] = list(merged)
        else:
            if new_value not in [None, "", current_value]:
                self.global_user_profile[key] = new_value

    def delete_fact(self, key, value=None):
        if key not in self.global_user_profile:
            return
        if value is None:
            self.global_user_profile.pop(key, None)
        elif isinstance(self.global_user_profile[key], list):
            if value in self.global_user_profile[key]:
                self.global_user_profile[key].remove(value)
            if not self.global_user_profile[key]:
                self.global_user_profile.pop(key, None)
        elif self.global_user_profile[key] == value:
            self.global_user_profile.pop(key, None)
    def delete_entity_relationships_and_node(self, entity_name: str):
        """
        Deletes KNOWS relationships between the user node and the specified entity node,
        then deletes the entity node itself with any remaining relationships.
        """
        try:
            safe_entity_name = entity_name.replace("'", "''")
            user_label = self.graph_user_node_label
            user_id_property = self.graph_user_node_id_property
            user_id_value = self.graph_user_node_id_value
            entity_label = "Entity"
        
            # Delete relationships
            query_delete_rel = (
                f"MATCH (u:{user_label} {{{user_id_property}: '{user_id_value}'}})-[r:KNOWS]->"
                f"(e:{entity_label} {{name: '{safe_entity_name}'}}) DELETE r"
            )
            self.topic_graph.query(query_delete_rel)
        
            # Delete the entity node and any remaining relationships
            query_delete_node = (
                f"MATCH (e:{entity_label} {{name: '{safe_entity_name}'}}) DETACH DELETE e"
            )
            self.topic_graph.query(query_delete_node)
        
        except Exception as e:
            print(f"Error deleting entity and relationships from Neo4j: {e}")
        
    def _update_global_user_profile(self, user_input: str):
        """
        Uses an LLM to extract user profile fields (name, location, hobbies, occupation, birthday)
        from user input and updates the shared global_user_profile dictionary.
        """
        print(f"DEBUG: LLM _update_global_user_profile called with input: '{user_input}'")

        # Define the comprehensive prompt for the LLM
        system_message_content = """You are an advanced information extraction system. Your sole purpose is to analyze user conversational input and extract specific personal profile details. Do NOT engage in conversation; only output the requested JSON.

Extract the following information from the user's statement:
- **name**: The user's full name.
- **location**: The user's current city, state, or country of residence.
- **hobbies**: A list of the user's distinct hobbies or interests.
- **occupation**: The user's job title or profession.
- **birthday**: The user's birth date. Format as 'YYYY-MM-DD' if a year is provided, 'MM-DD' if only month and day, or 'YYYY' if only the year.

If a piece of information is not found in the text, its corresponding value in the JSON should be `null` for single-value fields (name, location, occupation, birthday), or an empty list `[]` for 'hobbies'.

Example of expected JSON output (only if all fields are found):
```json
{
  "name": "Aditya Sharma",
  "location": "Noida, India",
  "hobbies": ["reading novels", "coding in Python", "playing guitar"],
  "occupation": "Software Engineer",
  "birthday": "1990-07-17"
}
Example if some fields are missing:
{
  "name": null,
  "location": "Mumbai",
  "hobbies": ["photography"],
  "occupation": null,
  "birthday": "11-25"
}
"""
        # CORRECTED LINE: Used escaped double quotes for the inner `user_input` within the f-string
        user_message_content = f"Now, extract information from the following user text.\nUser text: \"{user_input}\"\n\nJSON Output:"

        messages = [
            SystemMessage(content=system_message_content),
            HumanMessage(content=user_message_content)
        ]

        try:
            print(f"DEBUG: Sending LLM request for profile extraction for input: {user_input}")
            llm_response = self.llm_for_entity_extraction.invoke(messages)
            response_content = llm_response.content.strip()
            print(f"DEBUG: Raw LLM response content: {response_content}")

            # Robust JSON extraction: look for JSON wrapped in markdown code blocks
            json_match = re.search(r"```json\n(.*?)```", response_content, re.DOTALL)
            if json_match:
                json_string = json_match.group(1).strip()
                print(f"DEBUG: Extracted JSON string from markdown: {json_string}")
            else:
                json_string = response_content # Assume direct JSON if no markdown block
                print(f"DEBUG: Assuming direct JSON output: {json_string}")

            extracted_data = json.loads(json_string)
            print(f"DEBUG: Parsed JSON data: {extracted_data}")

            # Update global_user_profile with extracted data
            for key, value in extracted_data.items():
                if key == "hobbies" and value is not None and isinstance(value, list):
                    # Simple heuristic: replace on strong phrasing, otherwise merge
                    if any(phrase in user_input.lower() for phrase in ["my hobbies are", "set my hobbies to", "replace my hobbies with"]):
                        self.replace_fact("hobbies", value)
                    else:
                        self.add_or_merge_fact("hobbies", value)
                elif key == "skills" and value is not None and isinstance(value, list):
                    # Simple heuristic: replace on strong phrasing, otherwise merge
                    if any(phrase in user_input.lower() for phrase in ["my skills are", "set my skills to", "replace my skills with"]):
                        self.replace_fact("skills", value)
                    else:
                        self.add_or_merge_fact("skills", value)        
                elif value is not None and value != "" and (not isinstance(value, list) or value):
                    self.add_or_merge_fact(key, value)

            print(f"DEBUG: Final global user profile after LLM update: {self.global_user_profile}")

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to decode JSON from LLM response: {e}")
            print(f"Problematic LLM response content: {response_content}")
        except Exception as e:
            print(f"ERROR: General exception during LLM profile extraction: {e}")