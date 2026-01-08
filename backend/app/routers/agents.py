"""
Router for AI City Council Agents (Multi-Agent Simulation).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from pydantic import BaseModel
from typing import List, Optional
import os
import openai

# Check for OpenAI API Key (or use a mock)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter()

class AgentRequest(BaseModel):
    project_id: int

class AgentMessage(BaseModel):
    agent_id: str  # 'eco', 'dev', 'regulator', 'mayor'
    agent_name: str
    content: str

class CouncilResponse(BaseModel):
    conversation: List[AgentMessage]
    consensus: str

@router.post("/convene", response_model=CouncilResponse)
async def convene_council(
    request: AgentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulate a debate between 4 specialized AI agents regarding a project.
    """
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Construct Project Context for the LLM
    project_summary = f"""
    Project Name: {project.name}
    Type: {project.project_type}
    Description: {project.description}
    Site Area: {project.site_area_m2} m2
    Building Height: {project.building_height} m
    Target Population: {project.target_population}
    """

    # If no API key is available, return a mock simulation for demo purposes
    if not OPENAI_API_KEY:
        return get_mock_simulation(project.project_type)

    try:
        # Call LLM to simulate the multi-turn conversation
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        system_prompt = f"""
        You are a simulator for an "AI City Council". You must generate a script of a debate between 4 agents discussing an urban planning project.
        
        The Project:
        {project_summary}
        
        The Agents:
        1. ECO_AGENT (Green, focus on sustainability, trees, carbon)
        2. DEV_AGENT (Developer, focus on cost, density, profit, efficiency)
        3. REGULATOR (Government, focus on safety, UDA laws, setbacks, compliance)
        4. MAYOR (Mediator, finds a compromise)
        
        Format your response as a JSON object with this structure:
        {{
            "conversation": [
                {{ "agent_id": "eco", "agent_name": "Eco Agent", "content": "..." }},
                {{ "agent_id": "dev", "agent_name": "Developer Agent", "content": "..." }},
                ... (at least 4 turns)
            ],
            "consensus": "Final recommendation by the Mayor..."
        }}
        Ensure the debate is realistic and conflicting based on the project details.
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}],
            response_format={ "type": "json_object" }
        )
        
        import json
        result = json.loads(completion.choices[0].message.content)
        return result

    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback to mock on error
        return get_mock_simulation(project.project_type)

def get_mock_simulation(project_type: str) -> CouncilResponse:
    """Returns a hardcoded simulation for demo/fallback."""
    return {
        "conversation": [
            {
                "agent_id": "eco",
                "agent_name": "Eco Agent",
                "content": f"I've reviewed the {project_type} plan. The green coverage is concerningly low. We need strictly 20% canopy cover to mitigate the heat island effect here."
            },
            {
                "agent_id": "dev",
                "agent_name": "Developer Agent",
                "content": "20% is unrealistic! That eats into our rentable floor area. We're already on a tight margin. I suggest vertical gardens instead of losing ground space."
            },
            {
                "agent_id": "regulator",
                "agent_name": "Regulator Agent",
                "content": "Vertical gardens are fine, but they don't count towards the mandatory UDA open space requirement of 10%. Also, check the fire truck access on the north side."
            },
            {
                "agent_id": "mayor",
                "agent_name": "The Mayor",
                "content": "Let's find a middle ground. We'll stick to the 10% ground requirement for the Regulator, but use the Developer's vertical garden idea to reach the Eco Agent's goal. Everyone wins?"
            }
        ],
        "consensus": "Approved with conditions: Maintain 10% ground open space implies strict UDA compliance, supplemented by vertical green walls to satisfy sustainability goals without reducing building footprint."
    }
