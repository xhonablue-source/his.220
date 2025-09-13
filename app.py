"""
Michigan History HIS 220 + Michigan State AI - Complete Functional Application
Wayne County Community College District
WITH WORKING CLAUDE API INTEGRATION + INTERACTIVE SLIDES
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random
import base64

# 🔐 SECURE API KEY HANDLING
try:
    ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    ANTHROPIC_API_KEY = None

if not ANTHROPIC_API_KEY:
    ANTHROPIC_API_KEY = st.sidebar.text_input("🔑 Anthropic API Key (for testing)", type="password")

# Configure page
st.set_page_config(
    page_title="HIS 220 - Michigan History + Michigan State AI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_slide' not in st.session_state:
    st.session_state.current_slide = 0
if 'timer_active' not in st.session_state:
    st.session_state.timer_active = False
if 'timer_end' not in st.session_state:
    st.session_state.timer_end = None
if 'student_responses' not in st.session_state:
    st.session_state.student_responses = {}
if 'quiz_attempts' not in st.session_state:
    st.session_state.quiz_attempts = {}
if 'assignment_progress' not in st.session_state:
    st.session_state.assignment_progress = {
        'questions_asked': {'Historical_Expert': [], 'Geography_Expert': [], 'Detroit_Historian': []},
        'responses_received': {'Historical_Expert': [], 'Geography_Expert': [], 'Detroit_Historian': []},
        'notes': {'Historical_Expert': '', 'Geography_Expert': '', 'Detroit_Historian': ''},
        'essays': {'Historical_Expert': '', 'Geography_Expert': '', 'Detroit_Historian': ''},
        'completed_experts': set()
    }
if 'resident_verified' not in st.session_state:
    st.session_state.resident_verified = False
if 'ai_conversations' not in st.session_state:
    st.session_state.ai_conversations = []
if 'api_test_result' not in st.session_state:
    st.session_state.api_test_result = None

# Enhanced course slides data with interactive elements
SLIDES = [
    {
        "id": "welcome",
        "title": "Welcome to Michigan History",
        "content": """
        # 🏛️ History of Michigan (HIS 220)
        
        ## Wayne County Community College District
        **3 Credit Hours | 45 Contact Hours**
        
        > "From French exploration to modern innovation - discover the rich tapestry of Michigan's development and its unique role in American history."
        
        ### Course Focus:
        * Historical development from French exploration to present
        * Major political, social, and economic developments
        * Special emphasis on southeastern Michigan and Detroit metro
        * Michigan's unique geographical influence on development
        """,
        "presenter_notes": "Welcome students and introduce the comprehensive nature of this course.",
        "background_color": "#f0f8ff",
        "animation": "fade_in"
    },
    {
        "id": "geography_influence",
        "title": "Geography's Role in Michigan Development",
        "content": """
        # 🗺️ Michigan's Unique Geographic Setting
        
        ## The Great Lakes Advantage
        * **Surrounded by 4 of 5 Great Lakes** - Superior, Michigan, Huron, Erie
        * **3,000 miles of freshwater coastline** - more than any other state
        * **Strategic location** for transportation and trade
        
        ## Natural Resources Shaped Development
        * **Timber** - Fueled early logging industry
        * **Iron ore** - Upper Peninsula mining boom
        * **Coal** - Energy for industrial growth
        * **Fertile soil** - Agricultural development
        
        ## Geographic Challenges
        * **Two peninsulas** connected by bridge (1957)
        * **Harsh winters** influenced settlement patterns
        * **Water transportation** crucial before railroads
        """,
        "presenter_notes": "Emphasize how geography directly influenced every aspect of Michigan's development.",
        "interactive": True,
        "discussion_prompt": "How do you think Michigan's development would have been different if it weren't surrounded by the Great Lakes?",
        "background_color": "#e6f3ff",
        "map_data": {
            "great_lakes": ["Superior", "Michigan", "Huron", "Erie"],
            "resources": ["Timber", "Iron ore", "Coal", "Fertile soil"]
        }
    },
    {
        "id": "french_exploration",
        "title": "French Exploration Era",
        "content": """
        # 🇫🇷 French Exploration and Settlement (1600s-1760s)
        
        ## Key Explorers and Missionaries
        * **Étienne Brûlé** (1610s) - First European in Michigan
        * **Jean Nicolet** (1634) - Explored Lake Michigan
        * **Jacques Marquette** (1668) - Founded Sault Ste. Marie
        * **René-Robert Cavelier, Sieur de La Salle** - Explored Great Lakes system
        
        ## French Influence
        * **Fur trading** - Primary economic activity
        * **Missionary work** - Converting Native Americans
        * **Alliance with Native tribes** - Unlike other European powers
        * **Place names** - Detroit, Sault Ste. Marie, Marquette
        
        ## Native American Relations
        * **Ojibwe (Chippewa)** - Largest tribe in region
        * **Ottawa** and **Potawatomi** - Part of Three Fires Confederacy
        * **Trade partnerships** - Europeans dependent on Native knowledge
        """,
        "presenter_notes": "Emphasize the cooperative nature of early French-Native relations.",
        "background_color": "#fff8e7",
        "timeline": {
            "1610s": "Étienne Brûlé arrives",
            "1634": "Jean Nicolet explores",
            "1668": "Jacques Marquette founds Sault Ste. Marie",
            "1701": "Detroit founded"
        }
    },
    {
        "id": "detroit_founding",
        "title": "The Founding of Detroit",
        "content": """
        # 🏙️ Detroit: The Birth of a City (1701)
        
        ## Antoine de la Mothe Cadillac
        * **Founded Detroit** on July 24, 1701
        * **"Ville d'Étroit"** - City of the Strait
        * **Strategic location** - Narrowest point between Lakes Erie and Huron
        
        ## Early Detroit Characteristics
        * **Fort Pontchartrain** - Military and trading post
        * **Ribbon farms** - Long, narrow plots along river
        * **Multicultural population** - French, Native Americans, eventually British
        * **Trading hub** - Controlled Great Lakes water route
        
        ## Geographic Advantages
        * **Detroit River** - Natural highway for transportation
        * **Fertile land** - Agricultural potential
        * **Strategic military position** - Control of Great Lakes access
        """,
        "presenter_notes": "Connect Detroit's founding to its continued importance as a transportation hub.",
        "timer_minutes": 15,
        "activity_type": "discussion",
        "background_color": "#f0fff0",
        "interactive_map": True
    },
    {
        "id": "assessment",
        "title": "Course Assessment Methods",
        "content": """
        # 📝 How You'll Be Assessed
        
        ## Assessment Variety
        * **Examinations** - Test comprehension and analysis
        * **Quizzes** - Regular knowledge checks
        * **Case Studies** - Analyze historical scenarios
        * **Oral Conversations** - Discuss historical topics
        * **Group Discussions** - Collaborative learning
        * **Oral Presentations** - Share research findings
        
        ## Grading Scale
        * **A: 90%-100%** - Exceptional work
        * **B: 80%-89.9%** - Good work  
        * **C: 70%-79.9%** - Satisfactory work
        * **D: 60%-69.9%** - Below expectations
        * **E: <60%** - Unsatisfactory work
        
        ## Success Strategies
        * **Regular attendance** and participation
        * **Engage with Michigan State AI** for additional help
        * **Connect historical patterns** to modern Michigan
        """,
        "presenter_notes": "Emphasize the variety of assessment methods available to accommodate different learning styles.",
        "background_color": "#fff0f5"
    }
]

# Michigan State AI Expert Profiles
MICHIGAN_AI_EXPERTS = {
    "Historical_Expert": {
        "name": "Dr. Margaret Winters",
        "title": "Michigan State AI - Historical Expert",
        "expertise": "Michigan history from French exploration through modern times, with special focus on political and social developments",
        "background": "I am a digital historian specializing in Michigan's development. I have deep knowledge of how geographical, political, and social factors shaped our state from Native American settlements through the automotive age to today's innovations.",
        "resident_focus": "I help Michigan residents understand how our state's history connects to current issues, local governance, economic opportunities, and community development.",
        "key_areas": [
            "French exploration and Native American relations",
            "Territorial period and statehood",
            "Civil War and Reconstruction era",
            "Industrial revolution and labor movements",
            "Modern political and social developments"
        ],
        "personality": "scholarly but accessible, connects historical patterns to current events, passionate about Michigan's unique story"
    },
    "Geography_Expert": {
        "name": "Dr. James Lakeshore",
        "title": "Michigan State AI - Geography & Development Expert", 
        "expertise": "How Michigan's unique geography influenced development, natural resources, transportation, and settlement patterns",
        "background": "I specialize in understanding how Michigan's geography - our Great Lakes location, natural resources, and climate - shaped every aspect of our development and continues to influence life here today.",
        "resident_focus": "I help Michigan residents understand how geography affects everything from job opportunities to recreation, climate challenges, and why certain industries developed where they did.",
        "key_areas": [
            "Great Lakes influence on development",
            "Natural resources and industry location",
            "Transportation networks and trade routes",
            "Climate patterns and agricultural development",
            "Urban development patterns"
        ],
        "personality": "practical and scientific, emphasizes cause-and-effect relationships, helps residents understand their local environment"
    },
    "Detroit_Historian": {
        "name": "Dr. Rosa Martinez", 
        "title": "Michigan State AI - Detroit Metro Historian",
        "expertise": "Southeastern Michigan's development, Detroit's rise and transformation, automotive industry, civil rights, urban development",
        "background": "I focus on southeastern Michigan's unique role in American history - from frontier trading post to industrial powerhouse to modern innovation hub. I understand Detroit's complex story and its impact on the region.",
        "resident_focus": "I help southeastern Michigan residents understand their communities' histories, current challenges and opportunities, and how Detroit's story connects to broader Michigan development.",
        "key_areas": [
            "Detroit's founding and early development", 
            "Automotive industry rise and impact",
            "Great Migration and demographic changes",
            "Civil rights movements and social justice",
            "Urban renewal, decline, and revitalization efforts"
        ],
        "personality": "passionate about urban history, understands complex social dynamics, optimistic about Detroit's future while acknowledging challenges"
    }
}

# Enhanced quiz questions
QUIZ_DATA = {
    "michigan_basics": {
        "title": "Michigan History Fundamentals", 
        "questions": [
            {
                "question": "Who founded Detroit in 1701?",
                "options": [
                    "Jacques Marquette",
                    "Antoine de la Mothe Cadillac", 
                    "René-Robert Cavelier",
                    "Jean Nicolet"
                ],
                "correct": 1,
                "explanation": "Antoine de la Mothe Cadillac founded Detroit on July 24, 1701, establishing Fort Pontchartrain at the strategic location between Lakes Erie and Huron.",
                "difficulty": "Easy"
            },
            {
                "question": "Which geographic feature most influenced Michigan's early development?",
                "options": [
                    "The Appalachian Mountains",
                    "The Great Plains", 
                    "The Great Lakes",
                    "The Mississippi River"
                ],
                "correct": 2,
                "explanation": "Michigan is surrounded by 4 of the 5 Great Lakes, giving it 3,000 miles of freshwater coastline and making water transportation central to its development.",
                "difficulty": "Medium"
            },
            {
                "question": "What was the primary economic activity during French rule?",
                "options": [
                    "Agriculture",
                    "Manufacturing",
                    "Fur trading", 
                    "Mining"
                ],
                "correct": 2,
                "explanation": "The French economy in Michigan centered on fur trading, establishing trading posts and maintaining partnerships with Native American tribes.",
                "difficulty": "Easy"
            },
            {
                "question": "Which Native American confederacy was important in early Michigan?",
                "options": [
                    "Iroquois Confederacy",
                    "Three Fires Confederacy",
                    "Powhatan Confederacy", 
                    "Creek Confederacy"
                ],
                "correct": 1,
                "explanation": "The Three Fires Confederacy included the Ojibwe (Chippewa), Ottawa, and Potawatomi tribes, who were the primary Native groups in the Michigan region.",
                "difficulty": "Medium"
            }
        ]
    },
    "geography_influence": {
        "title": "Geography and Development",
        "questions": [
            {
                "question": "Why was Detroit's location strategically important?",
                "options": [
                    "It was the highest point in Michigan",
                    "It controlled the narrowest point between two Great Lakes",
                    "It had the most fertile soil",
                    "It was closest to major Eastern cities"
                ],
                "correct": 1,
                "explanation": "Detroit sits at the narrowest point between Lakes Erie and Huron, making it a crucial control point for Great Lakes navigation and trade.",
                "difficulty": "Medium"
            },
            {
                "question": "Which natural resource was NOT a major factor in early Michigan development?",
                "options": [
                    "Timber",
                    "Iron ore", 
                    "Oil deposits",
                    "Fertile soil"
                ],
                "correct": 2,
                "explanation": "While Michigan had timber, iron ore, and fertile soil that shaped its development, oil deposits were not a significant factor in its early history.",
                "difficulty": "Hard"
            }
        ]
    }
}

# Resources with working links
MICHIGAN_RESOURCES = {
    "videos": [
        {
            "title": "Michigan's French Colonial Heritage",
            "url": "https://www.youtube.com/results?search_query=michigan+french+colonial+history",
            "description": "Explore the lasting influence of French exploration and settlement",
            "duration": "12 minutes",
            "topic": "French Period"
        },
        {
            "title": "Great Lakes: Michigan's Natural Highways", 
            "url": "https://www.youtube.com/results?search_query=great+lakes+michigan+geography",
            "description": "How the Great Lakes shaped Michigan's transportation and economy",
            "duration": "15 minutes",
            "topic": "Geography"
        },
        {
            "title": "Detroit: From Trading Post to Motor City",
            "url": "https://www.youtube.com/results?search_query=detroit+history+motor+city",
            "description": "The transformation of Detroit from French fort to industrial center",
            "duration": "18 minutes",
            "topic": "Detroit History"
        }
    ],
    "articles": [
        {
            "title": "Michigan History Center - State Timeline",
            "url": "https://www.michigan.gov/mhc",
            "description": "Comprehensive timeline of Michigan historical events"
        },
        {
            "title": "Detroit Historical Society Resources", 
            "url": "https://detroithistorical.org",
            "description": "Primary sources and Detroit-focused historical materials"
        },
        {
            "title": "Michigan State University - Michigan History",
            "url": "https://msu.edu",
            "description": "Academic resources for Michigan history research"
        }
    ],
    "michigan_resident_resources": [
        {
            "title": "Michigan Government Services",
            "url": "https://www.michigan.gov",
            "description": "Access state services, licensing, and information for residents"
        },
        {
            "title": "Pure Michigan Tourism", 
            "url": "https://www.michigan.org",
            "description": "Discover Michigan attractions, events, and natural areas"
        },
        {
            "title": "Michigan Economic Development",
            "url": "https://www.michiganbusiness.org",
            "description": "Business resources, job opportunities, and economic data"
        }
    ]
}

def test_api_key():
    """Test if the API key works with a simple request"""
    if not ANTHROPIC_API_KEY:
        return False, "No API key provided"
    
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    test_data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "API key working"
        elif response.status_code == 401:
            return False, "Invalid API key"
        elif response.status_code == 429:
            return False, "Rate limited"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def get_ai_specialist_response(specialist_name: str, question: str, user_location: str = None) -> str:
    """Generate response from Michigan State AI using Claude API with enhanced error handling"""
    
    if not ANTHROPIC_API_KEY:
        return """🔑 **API Key Missing**
        
No Anthropic API key found. Please add your API key to Streamlit secrets as `ANTHROPIC_API_KEY` or enter it in the sidebar for testing.

To get an API key:
1. Go to console.anthropic.com
2. Create an account
3. Generate an API key
4. Add it to your Streamlit secrets"""
    
    # Test API key first time
    if st.session_state.api_test_result is None:
        working, message = test_api_key()
        st.session_state.api_test_result = (working, message)
    
    if not st.session_state.api_test_result[0]:
        return f"""❌ **API Key Issue**
        
{st.session_state.api_test_result[1]}

Please check your API key and try again. Make sure:
- Key starts with 'sk-ant-api03-'
- Key is active and has credits
- No extra spaces or characters"""
    
    # Build the system prompt
    specialist = MICHIGAN_AI_EXPERTS[specialist_name]
    
    resident_context = ""
    if st.session_state.resident_verified:
        resident_context = f"""
IMPORTANT: This user is a verified Michigan resident. {specialist['resident_focus']}

Provide practical, actionable information that helps them as a Michigan resident. Connect historical knowledge to current opportunities, challenges, and resources available in Michigan.
"""
    
    system_prompt = f"""You are {specialist['name']}, {specialist['title']}.

Background: {specialist['background']}

Your expertise areas:
{chr(10).join(f"- {area}" for area in specialist['key_areas'])}

Your personality: {specialist['personality']}

{resident_context}

Respond as this specialist, providing educational content that helps the user understand Michigan history and its relevance today. Be helpful, knowledgeable, and encouraging. Keep responses to 2-3 paragraphs unless the question requires more detail."""

    user_message = f"As a Michigan history specialist, can you help me with this question: {question}"
    if user_location:
        user_message += f" (I'm asking from {user_location})"
    
    # Make API call with proper error handling
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json", 
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 500,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data["content"][0]["text"]
        elif response.status_code == 401:
            st.session_state.api_test_result = (False, "Invalid API key")
            return "🔑 **Authentication Failed** - Your API key is invalid or expired."
        elif response.status_code == 429:
            return "⏰ **Rate Limited** - Too many requests. Please wait a moment and try again."
        elif response.status_code == 400:
            return "❌ **Bad Request** - There was an issue with the request format."
        else:
            return f"🚫 **API Error** - HTTP {response.status_code}. Please try again."
            
    except requests.exceptions.Timeout:
        return "⏰ **Timeout** - The request took too long. Please try again."
    except requests.exceptions.ConnectionError:
        return "🌐 **Connection Error** - Unable to reach the API. Check your internet connection."
    except requests.exceptions.RequestException as e:
        return f"🚫 **Request Failed** - {str(e)}"
    except Exception as e:
        return f"❌ **Unexpected Error** - {str(e)}"

def create_interactive_slide(slide_data: dict) -> None:
    """Create an interactive slide with animations and enhanced visuals"""
    
    # Custom CSS for this slide
    bg_color = slide_data.get('background_color', '#ffffff')
    
    st.markdown(f"""
    <style>
    .slide-container {{
        background: linear-gradient(135deg, {bg_color} 0%, #ffffff 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin: 1rem 0;
        animation: slideIn 0.8s ease-out;
    }}
    
    @keyframes slideIn {{
        from {{
            opacity: 0;
            transform: translateY(30px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .timeline-item {{
        background: rgba(255,255,255,0.8);
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4a90e2;
        border-radius: 5px;
    }}
    
    .resource-item {{
        background: rgba(0,123,255,0.1);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border: 1px solid rgba(0,123,255,0.2);
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Main slide content in container
    st.markdown('<div class="slide-container">', unsafe_allow_html=True)
    
    # Display main content
    st.markdown(slide_data["content"])
    
    # Add interactive elements based on slide type
    if slide_data.get("timeline"):
        st.markdown("### 📅 Historical Timeline")
        for year, event in slide_data["timeline"].items():
            st.markdown(f'<div class="timeline-item"><strong>{year}:</strong> {event}</div>', 
                       unsafe_allow_html=True)
    
    if slide_data.get("map_data"):
        st.markdown("### 🗺️ Interactive Elements")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Great Lakes:**")
            for lake in slide_data["map_data"]["great_lakes"]:
                st.markdown(f"• {lake}")
        
        with col2:
            st.markdown("**Natural Resources:**")
            for resource in slide_data["map_data"]["resources"]:
                st.markdown(f"• {resource}")
    
    # Interactive discussion prompt
    if slide_data.get("interactive") and slide_data.get("discussion_prompt"):
        st.markdown("---")
        st.markdown("### 💭 Think About This:")
        st.info(slide_data["discussion_prompt"])
        
        response_key = f"response_{slide_data['id']}"
        response = st.text_area(
            "Share your thoughts:",
            key=response_key,
            placeholder="What do you think? Type your response here...",
            height=100
        )
        if response:
            st.session_state.student_responses[response_key] = response
            st.success("Response saved!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_course_dashboard():
    """Enhanced course dashboard with Michigan State AI status"""
    st.markdown("# 🏛️ Michigan History HIS 220")
    st.markdown("## Wayne County Community College District")
    
    # Course overview cards with animations
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #1e3c72, #2a5298); color: white; padding: 1.5rem; border-radius: 15px; text-align: center; animation: pulse 2s infinite;">
            <h3>3.0</h3>
            <p>Credit Hours</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <h3>45</h3>
            <p>Contact Hours</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #f093fb, #f5576c); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
            <h3>0</h3>
            <p>Prerequisites</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Enhanced Michigan State AI status with real testing
        if ANTHROPIC_API_KEY:
            if st.session_state.api_test_result is None:
                with st.spinner("Testing Michigan State AI..."):
                    working, message = test_api_key()
                    st.session_state.api_test_result = (working, message)
            
            if st.session_state.api_test_result[0]:
                st.markdown("""
                <div style="background: linear-gradient(45deg, #4facfe, #00f2fe); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
                    <h3>✅</h3>
                    <p>Michigan State AI</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
                    <h3>⚠️</h3>
                    <p>AI Setup Needed</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; padding: 1.5rem; border-radius: 15px; text-align: center;">
                <h3>❌</h3>
                <p>AI Setup Needed</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Course description and objectives
    st.markdown("## Course Focus")
    st.info("""
    This course covers the historical development of Michigan from the period of French exploration 
    to the present. We examine the major political, social and economic developments of the state, 
    with special emphasis on southeastern Michigan and the metropolitan Detroit area.
    
    **Key Learning Objective:** Recognize Michigan's unique geographical setting and understand 
    how geography influenced the state's development.
    """)
    
    # Grading scale visualization
    st.markdown("## Grading Scale")
    
    # Create normal distribution grading scale chart
    grades = ['A (90-100%)', 'B (80-89.9%)', 'C (70-79.9%)', 'D (60-69.9%)', 'E (<60%)']
    colors = ['#28a745', '#17a2b8', '#ffc107', '#fd7e14', '#dc3545']
    
    # Normal distribution: most students get C, fewer get B/D, fewest get A/E
    student_distribution = [15, 25, 35, 20, 5]  # Percentages that typically earn each grade
    
    fig = go.Figure(data=[
        go.Bar(x=grades, y=student_distribution, marker_color=colors)
    ])
    fig.update_layout(
        title="Expected Grade Distribution (Normal Curve)",
        xaxis_title="Grade Levels", 
        yaxis_title="Percentage of Students",
        showlegend=False,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
