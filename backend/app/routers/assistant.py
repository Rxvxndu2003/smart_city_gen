"""
AI Assistant router - GPT-powered urban planning assistant endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatConversation, ChatMessage, MessageRole
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import openai

router = APIRouter()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "")


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    conversation_id: Optional[int] = None
    message: str
    query_type: Optional[str] = "GENERAL"


class MessageResponse(BaseModel):
    """Message response."""
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


@router.post("/chat", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message and get AI response.
    Creates a new conversation if conversation_id is not provided.
    """
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = db.query(ChatConversation).filter(
                ChatConversation.id == request.conversation_id,
                ChatConversation.user_id == current_user.id
            ).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation with title from first message
            title = request.message[:50] + "..." if len(request.message) > 50 else request.message
            conversation = ChatConversation(
                user_id=current_user.id,
                title=title
            )
            db.add(conversation)
            db.flush()
        
        # Save user message
        user_message = ChatMessage(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.message
        )
        db.add(user_message)
        db.flush()
        
        # Get conversation history for context
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.id
        ).order_by(ChatMessage.created_at).all()
        
        # Prepare messages for OpenAI
        openai_messages = [
            {
                "role": "system",
                "content": """You are an expert AI assistant for Smart City Urban Planning in Sri Lanka. 
You have deep knowledge of:
- Sri Lankan UDA (Urban Development Authority) building regulations
- Urban planning principles and best practices
- Building design and architecture
- Compliance and regulatory requirements
- Sustainability and green building practices
- Project management and feasibility studies

Provide accurate, detailed, and helpful responses to help users with their urban planning projects.
When discussing regulations, be specific and cite relevant UDA codes when applicable.
Always prioritize safety, compliance, and sustainability in your recommendations."""
            }
        ]
        
        # Add conversation history (limit to last 10 messages for context)
        recent_messages = messages[-10:]
        for msg in recent_messages:
            openai_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Call OpenAI API
        if openai.api_key and openai.api_key != "":
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=openai_messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                assistant_content = response.choices[0].message.content
            except Exception as e:
                # Fallback to template response if OpenAI fails
                assistant_content = _get_fallback_response(request.message, request.query_type)
        else:
            # Use template response if no API key
            assistant_content = _get_fallback_response(request.message, request.query_type)
        
        # Save assistant response
        assistant_message = ChatMessage(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=assistant_content
        )
        db.add(assistant_message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(assistant_message)
        
        return assistant_message
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all conversations for the current user."""
    conversations = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.id
    ).order_by(ChatConversation.updated_at.desc()).all()
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with all messages."""
    conversation = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation."""
    conversation = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
    
    return {"success": True, "message": "Conversation deleted"}


@router.post("/conversations/new")
async def create_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    conversation = ChatConversation(
        user_id=current_user.id,
        title="New Conversation"
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


def _get_fallback_response(message: str, query_type: str) -> str:
    """Generate intelligent fallback response when OpenAI is unavailable."""
    message_lower = message.lower()
    
    # Check for specific city/location planning requests
    if any(city in message_lower for city in ['kegalle', 'colombo', 'galle', 'kandy', 'jaffna', 'city', 'town']):
        # Extract city name
        cities = {
            'kegalle': 'Kegalle',
            'colombo': 'Colombo', 
            'galle': 'Galle',
            'kandy': 'Kandy',
            'jaffna': 'Jaffna'
        }
        city_name = next((cities[c] for c in cities if c in message_lower), 'the city')
        
        return f"""**Smart City Development Plan for {city_name}**

Here's a comprehensive urban planning framework:

**1. SITE ANALYSIS & ASSESSMENT**
• Population demographics and growth projections
• Current infrastructure inventory (roads, utilities, public transport)
• Environmental constraints (topography, water bodies, flood zones)
• Cultural and heritage sites to preserve
• Land use patterns and zoning requirements

**2. MASTER PLAN COMPONENTS**

**Residential Zones:**
• Mixed-income housing developments
• Density: 30-50 units per acre (medium density)
• Building heights: 3-5 floors in residential areas
• 35% open space requirement per UDA regulations
• Green corridors connecting neighborhoods

**Commercial & Business Districts:**
• Central Business District (CBD) with high-rise potential
• Neighborhood commercial centers (15-minute city concept)
• Mixed-use developments along main corridors
• Technology and innovation hubs

**Industrial Areas:**
• Light industrial zones with environmental controls
• Technology parks and industrial estates
• Buffer zones between residential and industrial
• Waste management and recycling facilities

**3. INFRASTRUCTURE REQUIREMENTS**

**Transportation:**
• Hierarchical road network (arterial, collector, local roads)
• Public transportation corridors (bus rapid transit)
• Bicycle lanes and pedestrian pathways
• Park-and-ride facilities at city periphery
• Smart traffic management systems

**Utilities:**
• Water supply: 150 liters per capita per day
• Sewage treatment plants (capacity for 25-year growth)
• Stormwater drainage with retention ponds
• Underground utility corridors in new developments

**Smart City Features:**
• IoT sensors for traffic, water, waste management
• Smart street lighting (LED with motion sensors)
• Wi-Fi hotspots in public areas
• Integrated command and control center

**4. GREEN SPACES & SUSTAINABILITY**
• Central park (minimum 5% of total area)
• Neighborhood parks every 0.5 km radius
• Urban forest zones for carbon sequestration
• Rooftop gardens and vertical greenery
• Solar power installations on public buildings

**5. SOCIAL INFRASTRUCTURE**
• Schools: 1 per 5,000 population
• Healthcare facilities: Hospitals, clinics strategically located
• Community centers and libraries
• Sports complexes and recreation facilities
• Cultural and religious spaces

**6. PHASING & IMPLEMENTATION**

**Phase 1 (Years 1-3):**
• Land acquisition and master plan approval
• Core infrastructure development
• Pilot residential and commercial projects

**Phase 2 (Years 4-7):**
• Major infrastructure completion
• Expansion of residential zones
• Smart city technology deployment

**Phase 3 (Years 8-10):**
• Final zone development
• System optimization and expansion
• Sustainability goals achievement

**7. REGULATORY COMPLIANCE**
• UDA approval for all zones
• Environmental Impact Assessment (EIA)
• Building permits with design guidelines
• Regular monitoring and enforcement

**8. ESTIMATED COSTS** (Approximate)
• Infrastructure: 60% of budget
• Buildings and facilities: 30%
• Land acquisition: 10%
• Contingency: 10-15%

**9. SUSTAINABILITY TARGETS**
• 40% renewable energy by 2035
• Zero-waste goals with 80% recycling
• 30% green cover maintained
• Net-positive water management

**10. ECONOMIC DEVELOPMENT**
• Job creation: Target 10,000+ jobs
• Tax incentives for businesses
• Innovation and startup ecosystem
• Tourism infrastructure

**NEXT STEPS:**
1. Conduct detailed feasibility study
2. Engage stakeholders and community
3. Prepare detailed master plan documents
4. Submit to UDA for approval
5. Secure funding and partnerships

Would you like me to elaborate on any specific aspect of this plan?"""
    
    # Specific design/planning questions
    elif any(word in message_lower for word in ['design', 'plan', 'layout', 'create', 'develop', 'build']):
        return """I can help you with urban planning and design! To provide specific guidance, please tell me:

**1. Project Type:**
• Residential development?
• Commercial complex?
• Mixed-use project?
• Industrial area?
• Public infrastructure?

**2. Key Details:**
• Location/city
• Site area (in perches, acres, or hectares)
• Target population or units
• Budget range
• Special requirements

**3. Your Main Goals:**
• Compliance with UDA regulations?
• Sustainability features?
• Cost optimization?
• Community amenities?

**Example questions I can answer:**
• "Plan a 5-acre residential development in Kandy"
• "Design guidelines for a shopping complex in Colombo"
• "Housing layout for 100 units with UDA compliance"
• "Green building features for commercial project"

Please provide more details and I'll give you a comprehensive plan!"""
    
    # UDA regulations
    elif "uda" in message_lower or "regulation" in message_lower:
        return """**Sri Lankan UDA (Urban Development Authority) Regulations Overview:**

The UDA regulations are designed to ensure sustainable and safe urban development. Here are the key aspects:

**Building Setbacks:**
- Front setback: Minimum 10 feet from road boundary
- Rear setback: Minimum 10 feet from property line
- Side setbacks: Minimum 5 feet on each side
- These ensure adequate spacing, natural light, and ventilation

**Building Coverage:**
- Maximum 65% of plot area for residential buildings
- Remaining 35% must be maintained as open space
- Helps prevent overcrowding and maintains green spaces

**Height Restrictions:**
- Residential buildings: Maximum 3 floors / 35 feet
- Each floor: 9-12 feet ceiling height recommended
- Ensures adequate light and air circulation

**Room Requirements:**
- Bedrooms: Minimum 100 sq.ft, 9ft width
- Living rooms: Minimum 120 sq.ft, 10ft width  
- Kitchens: Minimum 60 sq.ft, 6ft width
- Bathrooms: Minimum 35 sq.ft, 5ft width

**Ventilation & Parking:**
- Minimum 10% window area per room
- At least 1 parking space (9ft × 18ft) required

Would you like more details on any specific regulation?"""

    elif "setback" in message_lower:
        return """**Building Setbacks Explained:**

Setbacks are mandatory open spaces between your building and property boundaries:

**Why Setbacks Matter:**
1. **Fire Safety:** Prevents fire spread between buildings
2. **Natural Light:** Ensures all buildings receive adequate sunlight
3. **Ventilation:** Allows proper air circulation
4. **Privacy:** Maintains distance between neighboring properties
5. **Emergency Access:** Provides space for emergency vehicles

**UDA Setback Requirements:**
- **Front:** 10 feet from road boundary
- **Rear:** 10 feet from back property line
- **Sides:** 5 feet from each side boundary

**Common Violations to Avoid:**
- Building too close to boundaries
- Encroaching on setback areas with permanent structures
- Not accounting for property line surveys

Proper setback compliance is essential for project approval."""

    elif "coverage" in message_lower:
        return """**Building Coverage Ratio Explained:**

Building coverage is the percentage of your plot covered by the building footprint.

**UDA Standard:** Maximum 65% coverage for residential buildings

**Calculation Example:**
- Plot area: 1000 sq.m
- Maximum building footprint: 650 sq.m (65%)
- Minimum open space: 350 sq.m (35%)

**Benefits of Proper Coverage:**
- Adequate green space for environment
- Natural drainage and water absorption
- Outdoor recreation areas
- Better aesthetics and property value
- Compliance with fire safety norms

**What Counts in Coverage:**
- Main building footprint
- Covered porches and verandas
- Attached garages
- Permanent structures

**What Doesn't Count:**
- Open terraces
- Uncovered parking
- Gardens and landscaping
- Swimming pools (often)

Maintaining proper coverage ensures sustainable development."""
    
    # Parking questions
    elif 'parking' in message_lower:
        return """**Parking Requirements & Design Guide:**

**UDA Minimum Standards:**
• Residential: 1 space per unit (9ft × 18ft)
• Commercial: 1 space per 30 sq.m floor area
• Office: 1 space per 50 sq.m floor area
• Restaurant: 1 space per 10 seats

**Design Recommendations:**

**Layout Options:**
1. **Parallel Parking:** 8ft × 22ft per space
   - Best for narrow driveways
   - Slower traffic flow
   
2. **Perpendicular (90°):** 9ft × 18ft per space
   - Maximum efficiency
   - Requires 24ft aisle width
   
3. **Angled (60°):** 9ft × 20ft per space
   - Easiest maneuvering
   - One-way traffic flow
   - Requires 18ft aisle

**Accessibility:**
• 5% accessible spaces (min. 1)
• Size: 12ft × 18ft with 5ft access aisle
• Located nearest to entrances
• Maximum 200ft from building

**Additional Features:**
• Motorcycle parking: 4ft × 8ft
• Bicycle parking: 2ft × 6ft
• Visitor parking: 0.5 spaces per unit
• Loading zones for commercial

**Calculations Example:**
For 50-unit apartment:
• Required: 50 spaces minimum
• Recommended: 75 spaces (1.5 per unit)
• Accessible: 3 spaces
• Visitor: 10 spaces
• Total: 85 spaces

**Safety & Amenities:**
• Lighting: 10 lux minimum
• CCTV coverage
• Clear signage and markings
• Speed bumps at 50m intervals
• Drainage for rainwater
• Shade trees for every 10 spaces

Would you like parking layout drawings or calculations for your specific project?"""
    
    # Room size/standards questions
    elif any(word in message_lower for word in ['room', 'bedroom', 'living', 'kitchen', 'bathroom']):
        return """**UDA Room Size Standards & Requirements:**

**BEDROOMS (Residential):**
• Minimum area: 100 sq.ft (9.3 sq.m)
• Minimum width: 9 feet
• Ceiling height: 9-10 feet
• Window area: 10% of floor area
• Ventilation: Cross ventilation required
• Door: Minimum 3ft wide

**LIVING ROOMS:**
• Minimum area: 120 sq.ft (11.1 sq.m)
• Minimum width: 10 feet
• Ceiling height: 10-12 feet
• Window area: 15% of floor area
• Natural lighting essential
• Open to balcony recommended

**KITCHENS:**
• Minimum area: 60 sq.ft (5.6 sq.m)
• Minimum width: 6 feet
• Ceiling height: 9 feet minimum
• Ventilation: 20% window area OR exhaust
• Separate utility area recommended
• Gas connection safety standards

**BATHROOMS:**
• Minimum area: 35 sq.ft (3.3 sq.m)
• Minimum width: 5 feet
• Ceiling height: 8 feet minimum
• Ventilation: 15% opening OR exhaust fan
• Waterproofing mandatory
• Accessible bathroom: 5ft × 7ft minimum

**DINING AREAS:**
• Minimum: 80 sq.ft for 4-person dining
• Can be combined with living room
• Natural ventilation preferred

**BALCONIES/VERANDAS:**
• Minimum width: 4 feet
• Depth: 6-8 feet recommended
• Railing height: 3.5 feet minimum
• Not counted in building coverage

**CORRIDORS/PASSAGES:**
• Internal: 3 feet minimum width
• External: 4 feet minimum
• Public buildings: 5-6 feet

**OPTIMAL ROOM SIZES (Recommended):**
• Master bedroom: 150-180 sq.ft
• Standard bedroom: 120-140 sq.ft
• Living room: 180-250 sq.ft
• Kitchen: 80-100 sq.ft
• Dining: 100-120 sq.ft

**CEILING HEIGHTS:**
• Residential: 9-10 feet
• Commercial: 10-12 feet
• Showrooms: 12-15 feet
• Warehouses: 15-20 feet

These standards ensure comfort, safety, and regulatory compliance."""
    
    # Cost/budget questions  
    elif any(word in message_lower for word in ['cost', 'price', 'budget', 'expensive', 'cheap']):
        return """**Construction Cost Estimates (Sri Lanka 2025):**

**RESIDENTIAL CONSTRUCTION:**

**Basic Standard:**
• Rs. 60,000 - 75,000 per sq.ft
• Simple design, standard finishes
• Basic fixtures and fittings

**Medium Standard:**
• Rs. 80,000 - 120,000 per sq.ft
• Good quality finishes
• Modern fixtures and amenities

**High-End/Luxury:**
• Rs. 150,000 - 250,000+ per sq.ft
• Premium materials and finishes
• Smart home features, luxury fittings

**COMMERCIAL BUILDINGS:**
• Office space: Rs. 100,000 - 150,000 per sq.ft
• Retail/Shops: Rs. 120,000 - 180,000 per sq.ft
• Warehouses: Rs. 40,000 - 60,000 per sq.ft

**INFRASTRUCTURE COSTS:**

**Roads:**
• Asphalt: Rs. 8,000 - 12,000 per sq.m
• Concrete: Rs. 15,000 - 20,000 per sq.m
• Paver blocks: Rs. 6,000 - 10,000 per sq.m

**Utilities:**
• Water supply: Rs. 500,000 - 1M per km
• Sewage system: Rs. 800,000 - 1.5M per km
• Electricity lines: Rs. 300,000 - 600,000 per km
• Drainage: Rs. 400,000 - 800,000 per km

**LANDSCAPING:**
• Basic: Rs. 500 - 1,000 per sq.ft
• Premium: Rs. 1,500 - 3,000 per sq.ft

**COST BREAKDOWN (Typical Residential):**
• Foundation & Structure: 35%
• Walls & Roofing: 25%
• Finishes & Fittings: 20%
• Electrical & Plumbing: 12%
• Doors & Windows: 8%

**COST-SAVING TIPS:**
1. Use local materials (reduces transport)
2. Standard room sizes (less waste)
3. Simple architectural design
4. Bulk purchasing for multiple units
5. Proper planning (avoid changes mid-construction)

**ADDITIONAL COSTS:**
• Architectural fees: 5-8% of construction
• Engineering fees: 3-5%
• Approvals & permits: 2-3%
• Contingency: 10-15% buffer

These are approximate rates and vary by location, materials, and market conditions."""
    
    # How to / process questions
    elif any(word in message_lower for word in ['how', 'process', 'steps', 'procedure', 'approval']):
        return """**UDA Project Approval Process - Step by Step:**

**STEP 1: PRELIMINARY PREPARATION**
□ Land ownership documents
□ Survey plan (certified surveyor)
□ Soil test report
□ Site photographs
□ Location map

**STEP 2: DESIGN DEVELOPMENT**
□ Hire registered architect
□ Prepare architectural drawings
  - Site plan (1:500 scale)
  - Floor plans (1:100 scale)
  - Elevations and sections
  - 3D renderings (optional)
□ Structural engineer's drawings
□ MEP (Mechanical, Electrical, Plumbing) designs

**STEP 3: COMPLIANCE CHECK**
□ Verify setbacks (10ft front/rear, 5ft sides)
□ Calculate building coverage (max 65%)
□ Check height restrictions (max 35ft/3 floors)
□ Confirm room sizes meet standards
□ Parking requirements satisfied
□ Accessibility provisions

**STEP 4: DOCUMENT SUBMISSION TO UDA**
Required Documents:
1. Application form (duly filled)
2. Land deed/title (certified copy)
3. Survey plan (2 copies)
4. Architectural drawings (3 sets)
5. Structural drawings (2 sets)
6. Drainage plan
7. Landscape plan
8. Calculation sheets (coverage, parking, etc.)
9. Professional certificates
10. Fee payment receipt

**STEP 5: UDA REVIEW PROCESS**
• Initial review: 2-3 weeks
• Site inspection if required
• Comments/revisions requested
• Re-submission if needed
• Technical committee review

**STEP 6: APPROVAL & PERMITS**
• Approval in principle: 4-8 weeks
• Building permit issued
• Valid for 2 years (renewable)
• Construction can commence

**STEP 7: DURING CONSTRUCTION**
□ Display permit at site
□ Foundation inspection
□ Structural inspections
□ MEP inspections
□ Maintain site diary
□ Follow approved plans

**STEP 8: COMPLETION**
□ Final inspection request
□ Completion certificate from architect
□ As-built drawings submission
□ Occupancy certificate from UDA
□ Utility connections approval

**TIMELINE:**
• Design phase: 2-3 months
• Approval process: 2-4 months
• Construction: 12-24 months (depends on size)
• Final certification: 1 month

**COMMON DELAYS TO AVOID:**
• Incomplete documentation
• Non-compliance with regulations
• Missing professional certificates
• Incorrect drawings/calculations
• Land ownership disputes

**FEES (Approximate):**
• Application fee: Rs. 5,000 - 20,000
• Processing fee: Based on project value
• Inspection fees: Rs. 10,000 - 50,000

**PROFESSIONAL REQUIREMENTS:**
• Architect: SLIA registered
• Engineer: IESL registered
• Surveyor: Licensed surveyor

Need help with any specific step?"""
    
    # Default for unclear questions
    else:
        return f"""I can help you with **{message}**! 

To give you the most accurate and useful answer, could you clarify what you need?

**I can assist with:**

**Planning & Design:**
• City master plans and urban layouts
• Residential, commercial, or mixed-use developments
• Site analysis and feasibility studies
• Sustainable design principles

**Regulations & Compliance:**
• UDA building regulations and standards
• Setback, coverage, and height requirements
• Room size standards and specifications
• Parking and accessibility requirements

**Technical Guidance:**
• Construction costs and budgeting
• Material selection and specifications
• Infrastructure requirements (roads, utilities)
• Green building and sustainability

**Processes:**
• UDA approval procedures
• Required documents and permits
• Timeline and fees
• Professional requirements

**Examples of specific questions:**
• "How do I get UDA approval for my building?"
• "What's the cost per square foot for construction?"
• "Plan a residential layout for 2-acre land"
• "Setback requirements for commercial building"

Please provide more details about your specific needs, and I'll give you a detailed, actionable answer!"""


# Singleton
_assistant_service = None

def get_assistant_service():
    """Get or create assistant service instance."""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = {}
    return _assistant_service

    """Generate design rationale response."""
    return f"""**Design Rationale for {prompt}:**

**Strategic Decisions:**

1. **Regulatory Compliance:**
   - All design decisions align with UDA building regulations
   - Setbacks calculated to ensure legal compliance
   - Building coverage maintained within 65% limit
   - Height restrictions adhered to for safety

2. **Functional Efficiency:**
   - Space allocation optimized for intended use
   - Traffic flow and circulation carefully planned
   - Natural lighting maximized through strategic placement
   - Ventilation designed for comfort and health

3. **Sustainability Considerations:**
   - Green space preserved for environmental balance
   - Energy-efficient design principles applied
   - Water management and drainage planned
   - Future adaptability considered

4. **Community Impact:**
   - Design respects surrounding context
   - Parking adequately provided
   - Accessibility for all users ensured
   - Safety and security integrated

5. **Economic Viability:**
   - Cost-effective material selection
   - Construction feasibility verified
   - Long-term maintenance considered
   - Property value optimization

**Justification:**
This design approach balances regulatory requirements, functional needs, environmental responsibility, and economic considerations to create a sustainable and valuable development.

Would you like me to elaborate on any specific design decision?"""


def _generate_report_response(prompt: str) -> str:
    """Generate project report response."""
    return f"""**Project Analysis Report: {prompt}**

**Executive Summary:**
This report provides a comprehensive analysis of the project, including compliance status, design evaluation, and recommendations for improvement.

**1. Compliance Analysis:**
✓ UDA Regulations: Under review
✓ Building Setbacks: Verification required
✓ Coverage Ratio: Analysis needed
✓ Height Restrictions: Assessment pending
✓ Room Standards: Evaluation in progress

**2. Design Evaluation:**
- **Strengths:**
  • Efficient space utilization
  • Adherence to planning principles
  • Consideration of sustainability
  
- **Areas for Improvement:**
  • Optimize natural ventilation
  • Enhance green space integration
  • Review parking allocation

**3. Technical Assessment:**
- Structural feasibility: Good
- Systems integration: Adequate
- Accessibility compliance: To be verified
- Fire safety measures: Standard protocols

**4. Environmental Considerations:**
- Green space allocation: Under review
- Energy efficiency: Moderate potential
- Water management: Basic systems planned
- Waste management: Standard provisions

**5. Economic Analysis:**
- Cost efficiency: Competitive
- ROI potential: Favorable
- Market positioning: Strong
- Long-term value: Positive outlook

**6. Recommendations:**
1. Conduct detailed UDA compliance check
2. Optimize building orientation for natural light
3. Enhance sustainable features
4. Review parking and circulation
5. Strengthen community amenities

**Next Steps:**
- Complete compliance verification
- Finalize design optimizations
- Submit for regulatory approval
- Begin stakeholder engagement

For detailed analysis of specific aspects, please request additional information."""


def _generate_recommendations_response(prompt: str) -> str:
    """Generate recommendations response."""
    prompt_lower = prompt.lower()
    
    if "parking" in prompt_lower:
        return """**Parking Design Recommendations:**

**UDA Minimum Requirements:**
- At least 1 parking space per residential unit
- Dimensions: 9 feet × 18 feet per space
- Additional guest parking recommended

**Best Practice Recommendations:**

1. **Space Allocation:**
   - Provide 1.5 spaces per unit (1 covered + 0.5 visitor)
   - Larger units (3+ bedrooms): 2 spaces
   - Consider future vehicle ownership growth

2. **Design Optimization:**
   - Use parallel parking for narrow areas
   - Perpendicular parking for maximum efficiency
   - Angled parking (45°-60°) for easier access
   - Include motorcycle/bicycle parking

3. **Accessibility:**
   - 5% of spaces should be accessible parking
   - Located closest to entrances
   - Wider spaces (12 feet) with access aisles

4. **Safety Features:**
   - Adequate lighting (minimum 10 lux)
   - Clear signage and markings
   - CCTV coverage recommended
   - Speed control measures

5. **Environmental Considerations:**
   - Permeable paving for drainage
   - Shade trees to reduce heat island effect
   - EV charging points (future-ready)
   - Rainwater harvesting from parking areas

6. **Traffic Flow:**
   - Minimum 20-foot-wide driveways
   - One-way systems for efficiency
   - Clear entry/exit separation
   - Turning radius for all vehicle types

**Cost-Benefit Analysis:**
- Underground parking: Higher cost, more usable space
- Surface parking: Lower cost, consumes open area
- Multi-level parking: Moderate cost, optimal land use

Would you like specific calculations for your project?"""
    
    else:
        return f"""**Recommendations for {prompt}:**

**Priority Improvements:**

1. **Regulatory Compliance:**
   - Verify all UDA regulation requirements
   - Ensure setback compliance (10ft front/rear, 5ft sides)
   - Confirm building coverage stays within 65%
   - Review height restrictions (max 35 feet)

2. **Design Enhancements:**
   - Optimize room layouts for functionality
   - Maximize natural light and ventilation
   - Improve circulation and accessibility
   - Enhance green space integration

3. **Sustainability Upgrades:**
   - Install energy-efficient lighting (LED)
   - Consider solar panels for common areas
   - Implement rainwater harvesting
   - Use sustainable building materials
   - Plan for waste segregation facilities

4. **Safety & Security:**
   - Adequate fire safety measures
   - Emergency exits clearly marked
   - Security lighting in common areas
   - CCTV in parking and entrances
   - Proper boundary walls/fencing

5. **Amenity Improvements:**
   - Children's play area
   - Community gathering spaces
   - Adequate parking (1+ spaces per unit)
   - Bicycle storage facilities
   - Package delivery area

6. **Future-Ready Features:**
   - EV charging infrastructure
   - Fiber optic connectivity
   - Smart home pre-wiring
   - Flexible space design
   - Expansion provisions

7. **Cost Optimization:**
   - Value engineering opportunities
   - Local material sourcing
   - Phased construction approach
   - Energy savings calculations
   - Long-term maintenance planning

**Implementation Priority:**
1. Address regulatory compliance issues immediately
2. Implement critical safety features
3. Add sustainability measures progressively
4. Enhance amenities based on budget
5. Plan future-ready features for next phase

Would you like detailed guidance on implementing any of these recommendations?"""


def _generate_general_response(prompt: str) -> str:
    """Generate general response for other queries."""
    return f"""Thank you for your question about **{prompt}**.

As your AI urban planning assistant, I can help you with:

**Design & Planning:**
- Site analysis and feasibility studies
- Layout optimization
- Regulatory compliance guidance
- Building code interpretation

**UDA Regulations:**
- Setback requirements
- Building coverage calculations
- Height restrictions
- Room standards and specifications

**Best Practices:**
- Sustainable design principles
- Energy efficiency strategies
- Safety and accessibility standards
- Cost optimization techniques

**Project Support:**
- Compliance reports
- Design rationale documentation
- Recommendations for improvements
- Problem-solving strategies

To provide you with the most accurate and helpful information, could you please:
1. Specify which aspect you'd like to focus on
2. Provide context about your project (if applicable)
3. Indicate your primary concern or goal

I'm here to assist with any urban planning, regulatory, or design questions you may have!"""


# Singleton instance
_assistant_service = None

def get_assistant_service():
    """Get or create assistant service instance."""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = {}
    return _assistant_service
