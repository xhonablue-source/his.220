"""
Michigan History HIS 220 + AI Solutions Specialist - Complete Interactive App
Wayne County Community College District
WITH REAL CLAUDE API INTEGRATION for Michigan Residents
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

# 🔐 SECURE API KEY HANDLING
try:
    ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    ANTHROPIC_API_KEY = None

if not ANTHROPIC_API_KEY:
    ANTHROPIC_API_KEY = st.sidebar.text_input("🔑 Anthropic API Key (for testing)", type="password")

# Configure page
st.set_page_config(
    page_title="HIS 220 - Michigan History + AI Specialist",
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
        'questions_asked': {'Historical_Expert': [], 'Geography_Specialist': [], 'Detroit_Historian': []},
        'responses_received': {'Historical_Expert': [], 'Geography_Specialist': [], 'Detroit_Historian': []},
        'notes': {'Historical_Expert': '', 'Geography_Specialist': '', 'Detroit_Historian': ''},
        'essays': {'Historical_Expert': '', 'Geography_Specialist': '', 'Detroit_Historian': ''},
        'completed_specialists': set()
    }
if 'resident_verified' not in st.session_state:
    st.session_state.resident_verified = False
if 'ai_conversations' not in st.session_state:
    st.session_state.ai_conversations = []

# Course slides data
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
        "presenter_notes": "Welcome students and introduce the comprehensive nature of this course."
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
        "discussion_prompt": "How do you think Michigan's development would have been different if it weren't surrounded by the Great Lakes?"
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
        "presenter_notes": "Emphasize the cooperative nature of early French-Native relations."
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
        "activity_type": "discussion"
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
        * **Engage with AI specialist** for additional help
        * **Connect historical patterns** to modern Michigan
        """,
        "presenter_notes": "Emphasize the variety of assessment methods available to accommodate different learning styles."
    }
]

# AI Specialist Profiles - Michigan-focused experts
AI_SPECIALISTS = {
    "Historical_Expert": {
        "name": "Dr. Margaret Winters",
        "title": "Michigan Historical Expert",
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
    "Geography_Specialist": {
        "name": "Dr. James Lakeshore",
        "title": "Michigan Geography & Development Specialist", 
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
        "title": "Detroit Metro & Southeastern Michigan Historian",
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

# Michigan-focused quiz questions
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
                "explanation": "Antoine de la Mothe Cadillac founded Detroit on July 24, 1701, establishing Fort Pontchartrain at the strategic location between Lakes Erie and Huron."
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
                "explanation": "Michigan is surrounded by 4 of the 5 Great Lakes, giving it 3,000 miles of freshwater coastline and making water transportation central to its development."
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
                "explanation": "The French economy in Michigan centered on fur trading, establishing trading posts and maintaining partnerships with Native American tribes."
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
                "explanation": "The Three Fires Confederacy included the Ojibwe (Chippewa), Ottawa, and Potawatomi tribes, who were the primary Native groups in the Michigan region."
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
                "explanation": "Detroit sits at the narrowest point between Lakes Erie and Huron, making it a crucial control point for Great Lakes navigation and trade."
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
                "explanation": "While Michigan had timber, iron ore, and fertile soil that shaped its development, oil deposits were not a significant factor in its early history."
            }
        ]
    }
}

# Michigan resources for residents and students
MICHIGAN_RESOURCES = {
    "videos": [
        {
            "title": "Michigan's French Colonial Heritage",
            "url": "https://www.youtube.com/watch?v=michigan-french",
            "description": "Explore the lasting influence of French exploration and settlement",
            "duration": "12 minutes"
        },
        {
            "title": "Great Lakes: Michigan's Natural Highways", 
            "url": "https://www.youtube.com/watch?v=great-lakes-michigan",
            "description": "How the Great Lakes shaped Michigan's transportation and economy",
            "duration": "15 minutes"
        },
        {
            "title": "Detroit: From Trading Post to Motor City",
            "url": "https://www.youtube.com/watch?v=detroit-history",
            "description": "The transformation of Detroit from French fort to industrial center",
            "duration": "18 minutes"
        }
    ],
    "articles": [
        {
            "title": "Michigan History Center - State Timeline",
            "url": "https://www.michigan.gov/mhc/timeline",
            "description": "Comprehensive timeline of Michigan historical events"
        },
        {
            "title": "Detroit Historical Society Resources", 
            "url": "https://detroithistorical.org/learn",
            "description": "Primary sources and Detroit-focused historical materials"
        },
        {
            "title": "Michigan Native American History",
            "url": "https://www.michigan.gov/native-history", 
            "description": "Understanding the first peoples of Michigan"
        }
    ],
    "michigan_resident_resources": [
        {
            "title": "Michigan Government Services",
            "url": "https://www.michigan.gov/som",
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

def get_ai_specialist_response(specialist_name: str, question: str, user_location: str = None, anthropic_api_key: str = None) -> str:
    """Generate response from Michigan AI specialist using Claude API"""
    
    api_key = ANTHROPIC_API_KEY
    
    if not api_key:
        return """🚫 **Server Configuration Issue**
        
The instructor needs to set up the Anthropic API key for AI specialist responses. 
Students don't need to worry about this - just let your instructor know!

*This message only appears when the server isn't properly configured.*"""
    
    # Build the system prompt for Michigan specialist
    specialist = AI_SPECIALISTS[specialist_name]
    
    # Add resident-specific context if user is verified Michigan resident
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
    
    # Make API call
    headers = {
        "x-api-key": api_key,
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
            return "🔑 **API Key Issue** - Please contact your instructor to fix the server configuration."
        elif response.status_code == 429:
            return "⏰ **Rate Limited** - Too many students are using the system. Please wait a moment and try again."
        else:
            return f"🚫 **Server Error** - Status {response.status_code}. Please try again or contact your instructor."
            
    except requests.exceptions.Timeout:
        return "⏰ **Timeout** - The AI specialist is taking too long to respond. Please try again."
    except requests.exceptions.RequestException:
        return "🌐 **Connection Error** - Please check your internet connection and try again."
    except Exception:
        return "❌ **Unexpected Error** - Something went wrong. Please try again or contact your instructor."

def display_course_dashboard():
    """Main course dashboard with overview"""
    st.markdown("# 🏛️ Michigan History HIS 220")
    st.markdown("## Wayne County Community College District")
    
    # Course overview cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #1e3c72, #2a5298); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
            <h3>3.0</h3>
            <p>Credit Hours</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
            <h3>45</h3>
            <p>Contact Hours</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #f093fb, #f5576c); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
            <h3>0</h3>
            <p>Prerequisites</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Show AI specialist status
        if ANTHROPIC_API_KEY:
            st.markdown("""
            <div style="background: linear-gradient(45deg, #4facfe, #00f2fe); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <h3>✅</h3>
                <p>AI Specialist Active</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(45deg, #ff6b6b, #ee5a24); color: white; padding: 1rem; border-radius: 10px; text-align: center;">
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
    
    # Create grading scale chart
    grades = ['A (90-100%)', 'B (80-89.9%)', 'C (70-79.9%)', 'D (60-69.9%)', 'E (<60%)']
    colors = ['#28a745', '#17a2b8', '#ffc107', '#fd7e14', '#dc3545']
    ranges = [10, 10, 10, 10, 60]
    
    fig = go.Figure(data=[
        go.Bar(x=grades, y=ranges, marker_color=colors)
    ])
    fig.update_layout(
        title="Grading Scale Distribution",
        xaxis_title="Grade Levels", 
        yaxis_title="Percentage Range",
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

def display_ai_specialist():
    """Michigan AI Solutions Specialist for residents"""
    st.markdown("# 🤖 Michigan AI Solutions Specialist")
    st.markdown("## Your Go-To Resource as a Michigan Resident")
    
    # Resident verification
    if not st.session_state.resident_verified:
        st.markdown("### 📍 Resident Verification")
        st.info("Verify your Michigan residency to access specialized assistance for residents!")
        
        with st.form("resident_verification"):
            col1, col2 = st.columns(2)
            with col1:
                city = st.text_input("Michigan City/Town")
            with col2:
                zip_code = st.text_input("ZIP Code")
            
            verify_button = st.form_submit_button("Verify Michigan Residency")
            
            if verify_button and city and zip_code:
                # Simple verification (in production, this would be more robust)
                st.session_state.resident_verified = True
                st.session_state.user_location = f"{city}, Michigan {zip_code}"
                st.success(f"✅ Verified Michigan resident from {city}!")
                st.balloons()
                time.sleep(1)
                st.rerun()
    
    else:
        st.success(f"✅ Verified Michigan Resident: {st.session_state.user_location}")
        
        # Show available specialists
        st.markdown("## Meet Your Michigan Specialists")
        
        specialist_tabs = st.tabs([
            "🎓 Historical Expert", 
            "🗺️ Geography Specialist", 
            "🏙️ Detroit Historian"
        ])
        
        with specialist_tabs[0]:
            specialist = AI_SPECIALISTS["Historical_Expert"]
            st.markdown(f"### {specialist['name']}")
            st.markdown(f"**{specialist['title']}**")
            st.markdown(f"**Expertise:** {specialist['expertise']}")
            
            with st.expander("Areas of Focus"):
                for area in specialist['key_areas']:
                    st.markdown(f"- {area}")
            
            st.markdown("**How I Help Michigan Residents:**")
            st.info(specialist['resident_focus'])
        
        with specialist_tabs[1]:
            specialist = AI_SPECIALISTS["Geography_Specialist"]
            st.markdown(f"### {specialist['name']}")
            st.markdown(f"**{specialist['title']}**")
            st.markdown(f"**Expertise:** {specialist['expertise']}")
            
            with st.expander("Areas of Focus"):
                for area in specialist['key_areas']:
                    st.markdown(f"- {area}")
            
            st.markdown("**How I Help Michigan Residents:**")
            st.info(specialist['resident_focus'])
        
        with specialist_tabs[2]:
            specialist = AI_SPECIALISTS["Detroit_Historian"] 
            st.markdown(f"### {specialist['name']}")
            st.markdown(f"**{specialist['title']}**")
            st.markdown(f"**Expertise:** {specialist['expertise']}")
            
            with st.expander("Areas of Focus"):
                for area in specialist['key_areas']:
                    st.markdown(f"- {area}")
            
            st.markdown("**How I Help Michigan Residents:**") 
            st.info(specialist['resident_focus'])
        
        # AI Conversation Interface
        st.markdown("---")
        st.markdown("## 💬 Ask Your AI Specialist")
        
        if ANTHROPIC_API_KEY:
            st.success("✅ AI Specialist System Online - Real-time responses enabled!")
        else:
            st.error("❌ AI System Setup Needed - Contact instructor to enable live responses")
        
        # Specialist selection
        specialist_choice = st.selectbox(
            "Choose a specialist to ask:",
            ["Historical_Expert", "Geography_Specialist", "Detroit_Historian"],
            format_func=lambda x: f"{AI_SPECIALISTS[x]['name']} - {AI_SPECIALISTS[x]['title']}"
        )
        
        # Question categories for residents
        st.markdown("### 🎯 Question Categories for Michigan Residents:")
        
        question_categories = {
            "Historical Context": "How does Michigan's history relate to current issues or opportunities?",
            "Local Resources": "What historical sites, museums, or resources are available in my area?", 
            "Economic Development": "How did historical industries shape current job markets and opportunities?",
            "Cultural Heritage": "What cultural traditions and heritage sites reflect my community's history?",
            "Civic Engagement": "How can understanding Michigan history help me be a better citizen?",
            "Educational Opportunities": "What historical education or career paths are available in Michigan?"
        }
        
        selected_category = st.selectbox("Question Category:", list(question_categories.keys()))
        st.info(f"**Examples:** {question_categories[selected_category]}")
        
        # Question input
        user_question = st.text_area(
            "Ask your Michigan specialist:",
            placeholder=f"Example: As a resident of {st.session_state.get('user_location', 'Michigan')}, I'm wondering about...",
            height=100
        )
        
        # Ask question button
        if st.button("Ask Specialist", type="primary"):
            if user_question.strip():
                with st.spinner(f"💭 {AI_SPECIALISTS[specialist_choice]['name']} is researching your question..."):
                    response = get_ai_specialist_response(
                        specialist_choice, 
                        user_question,
                        st.session_state.get('user_location')
                    )
                
                # Display response
                st.markdown(f"### 🎭 {AI_SPECIALISTS[specialist_choice]['name']} responds:")
                st.markdown(response)
                
                # Save conversation
                conversation_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'specialist': specialist_choice,
                    'question': user_question,
                    'response': response,
                    'category': selected_category
                }
                st.session_state.ai_conversations.append(conversation_entry)
                
                # Feedback buttons
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("👍 Helpful"):
                        st.success("Thank you for the feedback!")
                with col2:
                    if st.button("👎 Not helpful"):
                        st.info("We'll work on improving our responses!")
                with col3:
                    if st.button("💾 Save to My Notes"):
                        st.success("Response saved to your conversation history!")
            else:
                st.warning("Please enter a question first!")
        
        # Conversation history
        if st.session_state.ai_conversations:
            st.markdown("---")
            st.markdown("## 📚 Your Conversation History")
            
            with st.expander(f"View Previous Conversations ({len(st.session_state.ai_conversations)} total)"):
                for i, conv in enumerate(reversed(st.session_state.ai_conversations[-10:])):  # Show last 10
                    specialist_name = AI_SPECIALISTS[conv['specialist']]['name']
                    timestamp = datetime.fromisoformat(conv['timestamp']).strftime("%Y-%m-%d %H:%M")
                    
                    st.markdown(f"**{timestamp} - {specialist_name}**")
                    st.markdown(f"*Q: {conv['question'][:100]}...*")
                    st.markdown(f"A: {conv['response'][:200]}...")
                    st.markdown("---")

def display_assignments():
    """Display course assignments with progress tracking"""
    st.markdown("# 📝 Course Assignments")
    
    # Assignment 1: Historical Analysis with AI Specialists
    st.markdown("## Assignment 1: Michigan Historical Analysis")
    st.markdown("### Explore Michigan History Through Specialist Consultations")
    
    with st.expander("📋 Assignment Instructions", expanded=True):
        st.markdown("""
        ### Your Mission:
        Conduct in-depth consultations with three Michigan AI specialists to understand different aspects of our state's development.
        
        **Requirements:**
        - Consult with **each specialist** (Historical Expert, Geography Specialist, Detroit Historian)
        - Ask **at least 3 focused questions** to each specialist
        - Take **detailed notes** on their responses
        - Write a **200-300 word reflection** for each specialist consultation
        
        **Focus Areas:**
        - **Historical Expert**: Political and social developments, key turning points
        - **Geography Specialist**: How location and resources shaped development
        - **Detroit Historian**: Urban development, industry, and cultural changes
        """)
    
    # Progress tracking
    st.markdown("## 📊 Your Progress")
    
    progress_data = st.session_state.assignment_progress
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        questions_asked = len(progress_data['questions_asked']['Historical_Expert'])
        st.metric("Historical Expert Questions", f"{questions_asked}/3")
        if questions_asked >= 3:
            st.success("✅ Complete")
    
    with col2:
        questions_asked = len(progress_data['questions_asked']['Geography_Specialist'])
        st.metric("Geography Specialist Questions", f"{questions_asked}/3") 
        if questions_asked >= 3:
            st.success("✅ Complete")
    
    with col3:
        questions_asked = len(progress_data['questions_asked']['Detroit_Historian'])
        st.metric("Detroit Historian Questions", f"{questions_asked}/3")
        if questions_asked >= 3:
            st.success("✅ Complete")
    
    # Specialist consultation interface
    st.markdown("## 💬 Specialist Consultations")
    
    specialist = st.selectbox(
        "Select specialist for consultation:",
        ["Historical_Expert", "Geography_Specialist", "Detroit_Historian"],
        format_func=lambda x: f"{AI_SPECIALISTS[x]['name']} - {AI_SPECIALISTS[x]['title']}"
    )
    
    # Show specialist expertise
    selected_specialist = AI_SPECIALISTS[specialist]
    st.markdown(f"### Consulting with {selected_specialist['name']}")
    st.info(f"**Expertise:** {selected_specialist['expertise']}")
    
    # Question input
    consultation_question = st.text_area(
        f"Ask {selected_specialist['name']} a focused question about Michigan history:",
        placeholder="Example: How did the Great Lakes influence early settlement patterns in Michigan?",
        height=80
    )
    
    if st.button(f"Consult {selected_specialist['name']}", type="primary"):
        if consultation_question.strip():
            with st.spinner(f"💭 {selected_specialist['name']} is analyzing your question..."):
                response = get_ai_specialist_response(specialist, consultation_question)
            
            st.markdown(f"### 🎓 {selected_specialist['name']} responds:")
            st.markdown(response)
            
            # Save to assignment progress
            progress_data['questions_asked'][specialist].append({
                'question': consultation_question,
                'timestamp': datetime.now().isoformat()
            })
            
            progress_data['responses_received'][specialist].append({
                'question': consultation_question,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            st.success("Consultation completed and saved to your assignment progress!")
        else:
            st.warning("Please enter a question for consultation.")
    
    # Notes section for each specialist
    st.markdown(f"## 📝 Notes on {selected_specialist['name']}")
    
    current_notes = st.text_area(
        f"Take notes on insights from {selected_specialist['name']}:",
        value=progress_data['notes'][specialist],
        height=150,
        placeholder="What key insights did you gain? How do their responses help you understand Michigan's development?"
    )
    
    if st.button(f"Save Notes for {selected_specialist['name']}"):
        progress_data['notes'][specialist] = current_notes
        st.success("Notes saved successfully!")
    
    # Reflection essay section
    questions_completed = len(progress_data['questions_asked'][specialist])
    if questions_completed >= 3:
        st.markdown(f"## ✍️ Reflection Essay: {selected_specialist['name']}")
        st.success(f"You've completed all consultations with {selected_specialist['name']}! Now write your reflection.")
        
        current_essay = st.text_area(
            f"Write a 200-300 word reflection on your consultations with {selected_specialist['name']}:",
            value=progress_data['essays'][specialist],
            height=200,
            placeholder=f"Based on your consultations with {selected_specialist['name']}, what did you learn about Michigan's development? How do their insights help you understand our state's history?"
        )
        
        # Word count tracking
        word_count = len(current_essay.split()) if current_essay else 0
        
        if word_count < 200:
            st.warning(f"Word count: {word_count}/200 (minimum) - Need {200-word_count} more words")
        elif word_count > 300:
            st.warning(f"Word count: {word_count}/300 (maximum) - Remove {word_count-300} words")
        else:
            st.success(f"Word count: {word_count} - Perfect length!")
        
        if st.button(f"Submit Reflection for {selected_specialist['name']}"):
            if 200 <= word_count <= 300:
                progress_data['essays'][specialist] = current_essay
                progress_data['completed_specialists'].add(specialist)
                st.balloons()
                st.success(f"Reflection submitted successfully for {selected_specialist['name']}!")
            else:
                st.error("Reflection must be between 200-300 words.")
    
    # Overall assignment completion
    st.markdown("## 🎯 Overall Assignment Progress")
    
    total_questions = sum(len(questions) for questions in progress_data['questions_asked'].values())
    total_reflections = len(progress_data['completed_specialists'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Consultations", f"{total_questions}/9")
    with col2:
        st.metric("Reflections Completed", f"{total_reflections}/3")
    
    # Assignment completion check
    if total_questions >= 9 and total_reflections >= 3:
        st.balloons()
        st.success("🎉 **Assignment 1 Complete!** You've successfully completed all specialist consultations and reflections.")
        
        # Export assignment results
        if st.button("📄 Export Assignment Results"):
            export_data = {
                'assignment': 'Assignment 1: Michigan Historical Analysis',
                'student_name': 'Student',  # In production, would get from user profile
                'completion_date': datetime.now().isoformat(),
                'consultations': progress_data['responses_received'],
                'notes': progress_data['notes'],
                'reflections': progress_data['essays'],
                'statistics': {
                    'total_consultations': total_questions,
                    'total_reflections': total_reflections,
                    'completed_specialists': list(progress_data['completed_specialists'])
                }
            }
            
            json_str = json.dumps(export_data, indent=2)
            st.download_button(
                "Download Assignment Results",
                json_str,
                file_name=f"michigan_history_assignment1_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

def display_slide(slide_data: dict) -> None:
    """Display course presentation slide"""
    st.markdown(slide_data["content"])
    
    # Interactive elements
    if slide_data.get("interactive"):
        if "discussion_prompt" in slide_data:
            st.markdown("---")
            st.markdown("### 💭 Discussion Question:")
            st.info(slide_data["discussion_prompt"])
            
            response_key = f"response_{slide_data['id']}"
            response = st.text_area(
                "Share your thoughts:",
                key=response_key,
                placeholder="What do you think? Share your perspective..."
            )
            if response:
                st.session_state.student_responses[response_key] = response
                st.success("Response saved!")

def display_quiz(quiz_id: str) -> None:
    """Display interactive quiz with detailed feedback"""
    if quiz_id not in QUIZ_DATA:
        st.error("Quiz not found!")
        return
    
    quiz = QUIZ_DATA[quiz_id]
    st.markdown(f"## 📝 {quiz['title']}")
    
    if quiz_id not in st.session_state.quiz_attempts:
        st.session_state.quiz_attempts[quiz_id] = 0
    
    with st.form(f"quiz_{quiz_id}"):
        answers = {}
        for i, q in enumerate(quiz["questions"]):
            st.markdown(f"**Question {i+1}:** {q['question']}")
            answer = st.radio(
                "Choose your answer:",
                options=q["options"],
                key=f"q_{quiz_id}_{i}",
                index=None
            )
            if answer:
                answers[i] = q["options"].index(answer)
        
        submitted = st.form_submit_button("Submit Quiz")
        
        if submitted and len(answers) == len(quiz["questions"]):
            st.session_state.quiz_attempts[quiz_id] += 1
            
            correct_count = 0
            total_questions = len(quiz["questions"])
            
            st.markdown("---")
            st.markdown("### 📊 Results:")
            
            for i, q in enumerate(quiz["questions"]):
                if i in answers:
                    is_correct = answers[i] == q["correct"]
                    if is_correct:
                        correct_count += 1
                        st.success(f"✅ Question {i+1}: Correct!")
                    else:
                        st.error(f"❌ Question {i+1}: Incorrect")
                        st.info(f"**Correct answer:** {q['options'][q['correct']]}")
                    
                    st.markdown(f"**Explanation:** {q['explanation']}")
                    st.markdown("---")
            
            score_pct = (correct_count / total_questions) * 100
            
            if score_pct >= 80:
                st.balloons()
                st.success(f"Excellent work! Score: {correct_count}/{total_questions} ({score_pct:.0f}%)")
            elif score_pct >= 60:
                st.success(f"Good job! Score: {correct_count}/{total_questions} ({score_pct:.0f}%)")
            else:
                st.warning(f"Keep studying! Score: {correct_count}/{total_questions} ({score_pct:.0f}%)")

def display_resources():
    """Display enhanced resources for students and residents"""
    st.markdown("# 📚 Learning Resources")
    st.markdown("Comprehensive resources for Michigan history students and residents")
    
    resource_tabs = st.tabs(["🎥 Videos", "📖 Articles", "🏠 For Michigan Residents"])
    
    with resource_tabs[0]:
        st.markdown("## Educational Videos")
        for video in MICHIGAN_RESOURCES["videos"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {video['title']}")
                st.markdown(video['description'])
                st.markdown(f"[Watch Video]({video['url']})")
            with col2:
                st.info(f"Duration: {video['duration']}")
            st.markdown("---")
    
    with resource_tabs[1]:
        st.markdown("## Recommended Articles & Sources")
        for article in MICHIGAN_RESOURCES["articles"]:
            st.markdown(f"- **[{article['title']}]({article['url']})** - {article['description']}")
    
    with resource_tabs[2]:
        st.markdown("## Resources for Michigan Residents")
        st.info("These resources help you connect Michigan history to current opportunities and services.")
        
        for resource in MICHIGAN_RESOURCES["michigan_resident_resources"]:
            st.markdown(f"- **[{resource['title']}]({resource['url']})** - {resource['description']}")

def sidebar_navigation() -> str:
    """Enhanced sidebar navigation with course and resident features"""
    st.sidebar.markdown("# 🏛️ Michigan History HIS 220")
    st.sidebar.markdown("**Wayne County Community College District**")
    
    # Mode selection
    mode = st.sidebar.radio(
        "Choose Your Experience:",
        [
            "🏠 Course Dashboard", 
            "📊 Course Presentation",
            "🤖 AI Specialist (Residents)",
            "📝 Assignments", 
            "🧠 Knowledge Quizzes", 
            "📚 Resources"
        ]
    )
    
    if mode == "📊 Course Presentation":
        st.sidebar.markdown("## Lecture Navigation")
        
        slide_titles = [f"{i+1}. {slide['title']}" for i, slide in enumerate(SLIDES)]
        selected_slide = st.sidebar.selectbox(
            "Jump to slide:",
            options=range(len(SLIDES)),
            format_func=lambda x: slide_titles[x],
            index=st.session_state.current_slide
        )
        
        if selected_slide != st.session_state.current_slide:
            st.session_state.current_slide = selected_slide
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("⬅️ Previous") and st.session_state.current_slide > 0:
                st.session_state.current_slide -= 1
                st.rerun()
        
        with col2:
            if st.button("Next ➡️") and st.session_state.current_slide < len(SLIDES) - 1:
                st.session_state.current_slide += 1
                st.rerun()
    
    # System status
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔧 System Status")
    if ANTHROPIC_API_KEY:
        st.sidebar.success("✅ AI Specialist Online")
        st.sidebar.caption("Real-time responses enabled")
    else:
        st.sidebar.error("❌ AI Setup Required")
        st.sidebar.caption("Contact instructor")
    
    # Quick stats
    if st.session_state.resident_verified:
        st.sidebar.success("✅ Michigan Resident Verified")
        conversations = len(st.session_state.ai_conversations)
        if conversations > 0:
            st.sidebar.caption(f"{conversations} AI conversations")
    
    return mode.split()[1].lower()

def main():
    """Main application with all functionality"""
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        background: linear-gradient(45deg, #1e3c72, #2a5298);
        color: white;
        font-weight: bold;
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #2a5298, #1e3c72);
        transform: translateY(-1px);
    }
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    .stTextArea > div > div > textarea {
        border-radius: 8px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get current mode from sidebar
    current_mode = sidebar_navigation()
    
    if current_mode == "course":
        display_course_dashboard()
    
    elif current_mode == "course":
        current_slide = SLIDES[st.session_state.current_slide]
        display_slide(current_slide)
        
        progress = (st.session_state.current_slide + 1) / len(SLIDES)
        st.progress(progress)
        st.caption(f"Slide {st.session_state.current_slide + 1} of {len(SLIDES)}")
    
    elif current_mode == "ai":
        display_ai_specialist()
    
    elif current_mode == "assignments":
        display_assignments()
    
    elif current_mode == "knowledge":
        st.markdown("# 🧠 Knowledge Check Quizzes")
        
        quiz_choice = st.selectbox(
            "Select a quiz:",
            ["michigan_basics", "geography_influence"],
            format_func=lambda x: QUIZ_DATA[x]["title"]
        )
        
        display_quiz(quiz_choice)
    
    elif current_mode == "resources":
        display_resources()

if __name__ == "__main__":
    main()
