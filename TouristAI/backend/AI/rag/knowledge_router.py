# backend/AI/rag/knowledge_router.py
from typing import Dict, Any, List
from .schemas import CollectionType, RoutePlan

class KnowledgeRouter:
    """
    Intelligent Knowledge Router & Retrieval Sub-Query Planner.
    Routes queries to target domain collections and decomposes complex prompts.
    """

    def route_query(self, query: str, agent_context: Dict[str, Any]) -> RoutePlan:
        agent_name = agent_context.get("agent", "GeneralAgent")
        city = agent_context.get("city", "Madurai")
        query_lower = query.lower()

        collections: List[CollectionType] = []
        sub_queries: List[str] = []

        # 1. Agent-based routing
        if agent_name == "HotelAgent":
            collections.append(CollectionType.HOTELS)
            collections.append(CollectionType.ADVISORIES)
            sub_queries.append(f"Hotels, stay options, and eco-lodges in {city}")

        elif agent_name == "RestaurantAgent":
            collections.append(CollectionType.RESTAURANTS)
            collections.append(CollectionType.CUSTOMS)
            sub_queries.append(f"Traditional food, authentic restaurants, and dining etiquette in {city}")

        elif agent_name == "BudgetAgent":
            collections.append(CollectionType.ATTRACTIONS)
            collections.append(CollectionType.HERITAGE)
            collections.append(CollectionType.TRANSPORT)
            sub_queries.append(f"Official entry fees, camera charges, and transport fares in {city}")

        elif agent_name == "CalendarAgent":
            collections.append(CollectionType.FESTIVALS)
            collections.append(CollectionType.WEATHER)
            sub_queries.append(f"Temple festivals, cultural processions, and seasonal weather in {city}")

        elif agent_name == "NearbyAgent":
            collections.append(CollectionType.ATTRACTIONS)
            collections.append(CollectionType.WILDLIFE)
            collections.append(CollectionType.TREKKING)
            sub_queries.append(f"Opening hours, entry restrictions, and trekking permits in {city}")

        elif agent_name == "EmergencyAssistant":
            collections.append(CollectionType.EMERGENCY)
            collections.append(CollectionType.ADVISORIES)
            sub_queries.append(f"Hospitals, police stations, and tourist emergency helplines in {city}")

        else:
            # Default Itinerary / Supervisor Agent routing
            collections = [
                CollectionType.ATTRACTIONS,
                CollectionType.HERITAGE,
                CollectionType.CUSTOMS,
                CollectionType.FESTIVALS
            ]
            sub_queries.append(f"Top sightseeing attractions and heritage spots in {city}")
            sub_queries.append(f"Dress codes, temple customs, and photography rules in {city}")

        # Intent override checks
        if "fee" in query_lower or "ticket" in query_lower or "cost" in query_lower:
            if CollectionType.ATTRACTIONS not in collections:
                collections.append(CollectionType.ATTRACTIONS)

        if "dress" in query_lower or "temple" in query_lower or "rule" in query_lower:
            if CollectionType.CUSTOMS not in collections:
                collections.append(CollectionType.CUSTOMS)

        metadata_filters = {"city": city}

        return RoutePlan(
            collections=collections,
            metadata_filters=metadata_filters,
            top_k=5,
            sub_queries=sub_queries
        )
