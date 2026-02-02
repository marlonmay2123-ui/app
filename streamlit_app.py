"""
TechScreen AI - Technical Screening Assistant
A Streamlit-based intelligent chatbot for candidate technical assessment powered by Gemini
"""

import streamlit as st
import os
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="TechScreen AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for TechScreen AI dark theme styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Dark theme base */
    .main {
        background-color: #0A0A0B;
        color: #E5E7EB;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #0A0A0B;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        animation: fadeIn 0.4s ease-in-out;
        backdrop-filter: blur(10px);
    }
    
    .bot-message {
        background: linear-gradient(135deg, #1F2937 0%, #111827 100%);
        border: 1px solid #374151;
        color: #F3F4F6;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    
    .user-message {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white;
        border: 1px solid #60A5FA;
        margin-left: 3rem;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
    }
    
    /* Progress bar */
    .progress-container {
        background-color: #1F2937;
        height: 10px;
        border-radius: 8px;
        overflow: hidden;
        margin: 1.5rem 0;
        border: 1px solid #374151;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #3B82F6 0%, #10B981 100%);
        height: 100%;
        transition: width 0.5s ease;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.6);
    }
    
    /* Tech stack badges */
    .tech-badge {
        display: inline-block;
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
        color: #BFDBFE;
        padding: 0.5rem 1rem;
        border-radius: 24px;
        margin: 0.3rem;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #3B82F6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
        color: white;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        border: 1px solid #60A5FA;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
        transform: translateY(-2px);
    }
    
    /* Input styling */
    .stTextInput>div>div>input {
        background-color: #1F2937;
        color: #F3F4F6;
        border-radius: 12px;
        border: 2px solid #374151;
        padding: 1rem;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
        background-color: #111827;
    }
    
    /* Textarea styling */
    .stTextArea>div>div>textarea {
        background-color: #1F2937;
        color: #F3F4F6;
        border-radius: 12px;
        border: 2px solid #374151;
    }
    
    .stTextArea>div>div>textarea:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
    }
    
    /* Animation */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Summary card */
    .summary-card {
        background: linear-gradient(135deg, #1F2937 0%, #111827 100%);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        margin: 1.5rem 0;
        border: 1px solid #374151;
    }
    
    /* Info badge */
    .info-badge {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
        color: #BFDBFE;
        padding: 0.75rem 1.25rem;
        border-radius: 12px;
        font-size: 0.9rem;
        margin: 0.5rem 0;
        border: 1px solid #3B82F6;
    }
    
    /* Labels */
    label {
        color: #D1D5DB !important;
        font-weight: 500;
    }
    
    /* Markdown text */
    .markdown-text-container {
        color: #E5E7EB;
    }
    
    /* Checkbox styling */
    [data-testid="stCheckbox"] {
        background-color: #1F2937;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #374151;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stCheckbox"]:hover {
        background-color: #111827;
        border-color: #3B82F6;
    }
    
    [data-testid="stCheckbox"] label {
        color: #E5E7EB !important;
        font-size: 0.9rem;
    }
    
    /* Checkbox input */
    input[type="checkbox"] {
        accent-color: #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
TECH_STACK_OPTIONS = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "PHP",
    "React", "Vue.js", "Angular", "Next.js", "Node.js", "Express.js", "Django", "Flask", 
    "FastAPI", "Spring Boot", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", 
    "SQLite", "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "TensorFlow", 
    "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Git", "Linux", "REST APIs", "GraphQL", "CI/CD"
]

POSITION_OPTIONS = [
    "Software Engineer", "Frontend Developer", "Backend Developer", "Full Stack Developer",
    "Data Scientist", "Machine Learning Engineer", "DevOps Engineer", "Cloud Engineer",
    "Mobile Developer", "QA Engineer"
]

EXPERIENCE_OPTIONS = ["0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"]

EXIT_KEYWORDS = ["bye", "goodbye", "exit", "quit", "end", "stop", "no thanks", "done"]

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'started' not in st.session_state:
        st.session_state.started = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'candidate_info' not in st.session_state:
        st.session_state.candidate_info = {
            'full_name': None,
            'email': None,
            'phone': None,
            'years_of_experience': None,
            'desired_positions': [],
            'current_location': None,
            'tech_stack': []
        }
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'greeting'
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'current_question_idx' not in st.session_state:
        st.session_state.current_question_idx = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if 'selected_techs' not in st.session_state:
        st.session_state.selected_techs = []
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    if 'submit_triggered' not in st.session_state:
        st.session_state.submit_triggered = False

# Validation functions
def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number (basic validation)"""
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10

def check_exit_intent(message: str) -> bool:
    """Check if user wants to exit"""
    return any(keyword in message.lower() for keyword in EXIT_KEYWORDS)

def analyze_sentiment(text: str) -> str:
    """Simple sentiment analysis based on keywords"""
    positive_words = ['great', 'good', 'excellent', 'love', 'excited', 'happy', 'awesome']
    negative_words = ['bad', 'terrible', 'hate', 'difficult', 'hard', 'frustrated', 'poor']
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return "positive 😊"
    elif neg_count > pos_count:
        return "negative 😔"
    else:
        return "neutral 😐"

def validate_answer(answer: str, question_type: str = "general") -> tuple[bool, str]:
    """Validate if answer is sufficient and meaningful"""
    answer = answer.strip()
    
    # Check minimum length
    if len(answer) < 10:
        return False, "Your answer seems too short. Please provide more detail (at least 10 characters)."
    
    # Check for generic/placeholder responses
    generic_responses = ['idk', 'i don\'t know', 'no idea', 'not sure', 'na', 'n/a', 'pass', 'skip']
    if answer.lower() in generic_responses:
        return False, "Please try to provide a meaningful answer. If you're unsure, share your understanding or thoughts."
    
    # Check if answer has at least a few words
    words = answer.split()
    if len(words) < 3:
        return False, "Please provide a more detailed answer with at least a few words."
    
    return True, ""

# LLM Integration for question generation
def generate_technical_questions(tech_stack: List[str]) -> List[Dict[str, str]]:
    """
    Generate technical questions using Gemini API
    Creates unique, technology-specific questions for each skill
    """
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            st.warning("⚠️ Gemini API key not found. Using fallback questions.")
            return get_fallback_questions(tech_stack)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        questions = []
        
        # Generate unique questions for each technology (up to 4)
        for i, tech in enumerate(tech_stack[:4]):
            system_prompt = f"""You are an experienced technical interviewer specializing in {tech}.
Create one thoughtful, practical interview question that assesses real-world knowledge."""

            user_prompt = f"""Generate exactly ONE technical interview question specifically about {tech}.

Requirements:
- Question must be specific to {tech}, not generic programming
- Should assess practical knowledge and real-world application
- Clear and unambiguous
- Intermediate to advanced difficulty
- 2-3 sentences maximum
- Focus on concepts, best practices, or problem-solving

Provide ONLY the question text, no formatting or prefixes."""

            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.8,
                        max_output_tokens=200
                    )
                )
                
                question_text = response.text.strip()
                # Clean up any formatting
                question_text = re.sub(r'^(Q\d+[:\.]?\s*|Question\s*\d*[:\.]?\s*)', '', question_text, flags=re.IGNORECASE)
                
                questions.append({
                    'question': question_text,
                    'tech': tech,
                    'number': i + 1
                })
            except Exception as e:
                # If individual question fails, use fallback for that tech
                fallback = get_fallback_questions([tech])
                if fallback:
                    questions.append(fallback[0])
        
        if len(questions) < 3:
            return get_fallback_questions(tech_stack)
        
        return questions
        
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return get_fallback_questions(tech_stack)

def get_fallback_questions(tech_stack: List[str]) -> List[Dict[str, str]]:
    """Fallback questions if LLM fails"""
    tech_questions_map = {
        "Python": [
            "Explain the difference between a list and a tuple in Python. When would you use each?",
            "What are Python decorators and how would you implement one for timing function execution?"
        ],
        "JavaScript": [
            "Explain how closures work in JavaScript and provide a practical use case.",
            "What is the difference between '==' and '===' in JavaScript? Provide examples."
        ],
        "React": [
            "Explain the useEffect hook and when you would use its cleanup function.",
            "How does React's virtual DOM improve performance compared to direct DOM manipulation?"
        ],
        "Node.js": [
            "How does the event loop work in Node.js? Why is it important?",
            "Explain the difference between process.nextTick() and setImmediate()."
        ],
        "Python": [
            "What are list comprehensions in Python and when should you use them?",
            "Explain the Global Interpreter Lock (GIL) and its implications."
        ],
        "SQL": [
            "Explain the difference between INNER JOIN and LEFT JOIN with examples.",
            "How would you optimize a slow-running SQL query?"
        ],
        "MongoDB": [
            "When would you choose MongoDB over a relational database?",
            "Explain indexing in MongoDB and why it's important for performance."
        ],
        "Docker": [
            "What is the difference between a Docker image and a container?",
            "How would you optimize a Dockerfile for production deployment?"
        ],
        "AWS": [
            "Explain the difference between EC2 and Lambda. When would you use each?",
            "How would you design a highly available application architecture on AWS?"
        ]
    }
    
    questions = []
    for tech in tech_stack[:4]:
        if tech in tech_questions_map:
            questions.append({
                'question': tech_questions_map[tech][0],
                'tech': tech,
                'number': len(questions) + 1
            })
    
    # Fill with generic questions if needed
    generic_questions = [
        {"question": "Describe a challenging technical problem you solved recently and your approach.", "tech": "General"},
        {"question": "How do you approach debugging a complex issue in a production environment?", "tech": "General"},
        {"question": "Explain how you would design a scalable REST API from scratch.", "tech": "General"},
        {"question": "What testing strategies do you implement in your development workflow?", "tech": "General"}
    ]
    
    while len(questions) < 4:
        q = generic_questions[len(questions) % len(generic_questions)]
        questions.append({
            'question': q['question'],
            'tech': q['tech'],
            'number': len(questions) + 1
        })
    
    return questions[:4]

def add_message(role: str, content: str, message_type: str = "text"):
    """Add a message to the chat"""
    st.session_state.messages.append({
        'role': role,
        'content': content,
        'message_type': message_type,
        'timestamp': datetime.now().strftime("%H:%M")
    })

def display_messages():
    """Display all chat messages"""
    for msg in st.session_state.messages:
        css_class = "user-message" if msg['role'] == 'user' else "bot-message"
        icon = "👤" if msg['role'] == 'user' else "🤖"
        
        st.markdown(f"""
        <div class="chat-message {css_class}">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span>{icon}</span>
                <strong>{"You" if msg['role'] == 'user' else "TechScreen AI"}</strong>
                <span style="font-size: 0.8rem; opacity: 0.7;">{msg['timestamp']}</span>
            </div>
            <div>{msg['content']}</div>
        </div>
        """, unsafe_allow_html=True)

def get_progress():
    """Calculate conversation progress"""
    steps = ['greeting', 'name', 'email', 'phone', 'experience', 'position', 
             'location', 'tech_stack', 'questions', 'summary', 'ended']
    current_idx = steps.index(st.session_state.current_step) if st.session_state.current_step in steps else 0
    return int((current_idx / len(steps)) * 100)

def handle_greeting():
    """Handle the greeting step"""
    if not any(msg['role'] == 'bot' for msg in st.session_state.messages):
        greeting = """Hello! 👋 Welcome to **TalentScout's AI Screening Assistant**.

I'm here to help gather information about your background and assess your technical skills for exciting opportunities. This conversation will take about **5-10 minutes**.

**What we'll cover:**
- Your contact information and experience
- Desired positions and location
- Technical skills assessment
- Personalized technical questions

Let's get started! What is your **full name**?"""
        add_message('bot', greeting)
        st.session_state.current_step = 'name'

def process_user_input(user_input: str):
    """
    Process user input based on current conversation step
    
    CONTEXT MANAGEMENT:
    - Maintains conversation state across steps
    - Validates inputs before progression
    - Handles unexpected inputs gracefully
    - Provides helpful error messages
    """
    
    # Check for exit intent
    if check_exit_intent(user_input):
        add_message('user', user_input)
        add_message('bot', "Thank you for your time! We appreciate your interest. If you'd like to continue later, feel free to start a new session. Have a great day! 👋")
        st.session_state.current_step = 'ended'
        return
    
    step = st.session_state.current_step
    
    # Name step
    if step == 'name':
        if len(user_input.strip()) >= 2:
            st.session_state.candidate_info['full_name'] = user_input.strip()
            add_message('user', user_input)
            add_message('bot', f"Nice to meet you, **{user_input}**! 🎉\n\nWhat is your **email address**?")
            st.session_state.current_step = 'email'
        else:
            add_message('user', user_input)
            add_message('bot', "⚠️ Please provide your full name (at least 2 characters).")
    
    # Email step
    elif step == 'email':
        if validate_email(user_input.strip()):
            st.session_state.candidate_info['email'] = user_input.strip()
            add_message('user', user_input)
            add_message('bot', "Great! What is your **phone number**?")
            st.session_state.current_step = 'phone'
        else:
            add_message('user', user_input)
            add_message('bot', "⚠️ That doesn't look like a valid email address. Please enter a valid email (e.g., name@example.com).")
    
    # Phone step
    elif step == 'phone':
        if validate_phone(user_input.strip()):
            st.session_state.candidate_info['phone'] = user_input.strip()
            add_message('user', user_input)
            add_message('bot', "Perfect! How many **years of professional experience** do you have?\n\nYou can type a number or choose from: " + ", ".join(EXPERIENCE_OPTIONS))
            st.session_state.current_step = 'experience'
        else:
            add_message('user', user_input)
            add_message('bot', "⚠️ Please enter a valid phone number (at least 10 digits).")
    
    # Experience step
    elif step == 'experience':
        exp_map = {"0-1 years": 0, "1-3 years": 2, "3-5 years": 4, "5-10 years": 7, "10+ years": 12}
        if user_input in exp_map:
            st.session_state.candidate_info['years_of_experience'] = exp_map[user_input]
        else:
            # Try to extract number
            numbers = re.findall(r'\d+', user_input)
            if numbers:
                st.session_state.candidate_info['years_of_experience'] = int(numbers[0])
            else:
                add_message('user', user_input)
                add_message('bot', "⚠️ Please provide your years of experience as a number or choose from the options.")
                return
        
        add_message('user', user_input)
        positions_text = "\n".join([f"- {pos}" for pos in POSITION_OPTIONS])
        add_message('bot', f"Excellent! What **position(s)** are you interested in? You can list multiple separated by commas.\n\n**Available positions:**\n{positions_text}")
        st.session_state.current_step = 'position'
    
    # Position step
    elif step == 'position':
        positions = [p.strip() for p in user_input.split(',')]
        valid_positions = [p for p in positions if p in POSITION_OPTIONS or len(p) > 2]
        
        if valid_positions:
            st.session_state.candidate_info['desired_positions'] = valid_positions
            add_message('user', user_input)
            add_message('bot', "Great choices! 🎯\n\nWhere are you currently **located**? (City, Country)")
            st.session_state.current_step = 'location'
        else:
            add_message('user', user_input)
            add_message('bot', "⚠️ Please select at least one position from the list or enter your desired role.")
    
    # Location step
    elif step == 'location':
        if len(user_input.strip()) >= 2:
            st.session_state.candidate_info['current_location'] = user_input.strip()
            add_message('user', user_input)
            
            # Display tech stack in categories
            tech_display = "Now, let's talk about your **technical skills**! 💻\n\nPlease select all technologies you're proficient in from the checkboxes below.\n\n"
            tech_display += "**Available technologies:**\n"
            tech_display += "Languages: Python, JavaScript, Java, C++, Go, etc.\n"
            tech_display += "Frameworks: React, Django, Flask, Node.js, etc.\n"
            tech_display += "Databases: PostgreSQL, MongoDB, MySQL, etc.\n"
            tech_display += "Cloud: AWS, Azure, GCP, Docker, Kubernetes, etc.\n"
            
            add_message('bot', tech_display)
            st.session_state.current_step = 'tech_stack'
            st.session_state.selected_techs = []
        else:
            add_message('user', user_input)
            add_message('bot', "⚠️ Please provide your current location (City, Country).")
    
    # Tech stack step
    elif step == 'tech_stack':
        techs = [t.strip() for t in user_input.split(',')]
        valid_techs = [t for t in techs if t in TECH_STACK_OPTIONS or len(t) > 1]
        
        if valid_techs:
            st.session_state.candidate_info['tech_stack'] = valid_techs
            add_message('user', user_input)
            
            # Generate technical questions
            with st.spinner('🤔 Generating personalized technical questions...'):
                questions = generate_technical_questions(valid_techs)
                st.session_state.questions = questions
                st.session_state.current_question_idx = 0
            
            tech_badges = " ".join([f'<span class="tech-badge">{tech}</span>' for tech in valid_techs])
            add_message('bot', f"Excellent! Your tech stack:\n\n{tech_badges}\n\nNow let's assess your technical knowledge. I'll ask you **{len(questions)} questions** based on your skills. Take your time to answer each one thoughtfully. 📝", "html")
            
            # Ask first question
            if questions:
                first_q = questions[0]
                add_message('bot', f"**Question {first_q['number']}/{len(questions)}** (Related to: {first_q['tech']})\n\n{first_q['question']}")
                st.session_state.current_step = 'questions'
        else:
            add_message('user', user_input)
            add_message('bot', "⚠️ Please list at least one technology from your skill set.")
    
    # Questions step
    elif step == 'questions':
        # Validate answer
        is_valid, validation_msg = validate_answer(user_input)
        
        if not is_valid:
            add_message('user', user_input)
            add_message('bot', f"⚠️ {validation_msg}\n\nLet me ask you again:\n\n{st.session_state.questions[st.session_state.current_question_idx]['question']}")
            return
        
        # Store answer
        st.session_state.answers.append({
            'question': st.session_state.questions[st.session_state.current_question_idx]['question'],
            'answer': user_input,
            'sentiment': analyze_sentiment(user_input)
        })
        add_message('user', user_input)
        
        # Move to next question or summary
        st.session_state.current_question_idx += 1
        
        if st.session_state.current_question_idx < len(st.session_state.questions):
            # Ask next question
            next_q = st.session_state.questions[st.session_state.current_question_idx]
            add_message('bot', f"Thank you! Next question...\n\n**Question {next_q['number']}/{len(st.session_state.questions)}** (Related to: {next_q['tech']})\n\n{next_q['question']}")
        else:
            # All questions answered, show summary
            show_summary()
            st.session_state.current_step = 'summary'
    
    # Summary step
    elif step == 'summary':
        add_message('user', user_input)
        add_message('bot', "Thank you for sharing! Our recruitment team has all the information they need. We'll be in touch within **3-5 business days**. Have a great day! 🎉👋")
        st.session_state.current_step = 'ended'

def show_summary():
    """Display candidate information summary"""
    info = st.session_state.candidate_info
    
    summary = f"""Thank you for completing the screening, **{info['full_name']}**! 🎉

Here's a summary of your information:

📧 **Email:** {info['email']}
📱 **Phone:** {info['phone']}
💼 **Experience:** {info['years_of_experience']} years
🎯 **Desired Position(s):** {', '.join(info['desired_positions'])}
📍 **Location:** {info['current_location']}
🛠️ **Tech Stack:** {', '.join(info['tech_stack'])}

**Technical Assessment:**
You answered {len(st.session_state.answers)} technical questions.

Our recruitment team will review your profile and responses. We appreciate your time and interest!

Is there anything else you'd like to share or any questions for us?"""
    
    add_message('bot', summary)

def handle_input_submit():
    """Handle input submission on Enter key"""
    st.session_state.submit_triggered = True

def save_session_data():
    """Save session data to file"""
    try:
        data = {
            'session_id': st.session_state.session_id,
            'candidate_info': st.session_state.candidate_info,
            'questions_and_answers': st.session_state.answers,
            'timestamp': datetime.now().isoformat()
        }
        
        os.makedirs('sessions', exist_ok=True)
        filename = f"sessions/session_{st.session_state.session_id}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    except Exception as e:
        st.error(f"Error saving session: {e}")
        return None

# Main application
def main():
    """Main application function"""
    init_session_state()
    
    # Welcome screen
    if not st.session_state.started:
        st.markdown("""
        <div class="header-container">
            <h1 style="margin: 0; font-size: 3rem; font-weight: 700;">🤖 TechScreen AI</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.3rem; opacity: 0.95; font-weight: 500;">AI-Powered Technical Screening</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1F2937 0%, #111827 100%); padding: 3rem; border-radius: 20px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5); border: 1px solid #374151; margin-top: 2rem;">
                <h2 style="color: #60A5FA; margin-top: 0; font-size: 2rem; font-weight: 600; margin-bottom: 1.5rem;">👋 Welcome to TechScreen AI!</h2>
                <p style="color: #D1D5DB; line-height: 1.8; font-size: 1.1rem; margin-bottom: 2rem;">
                    I'm your AI screening assistant powered by advanced language models. I'll help assess your technical skills and experience through an intelligent conversation.
                </p>
                <div style="margin: 2rem 0;">
                    <div style="padding: 1rem 1.5rem; background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%); border-radius: 12px; margin: 1rem 0; border: 1px solid #3B82F6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">✅</span>
                        <span style="color: #BFDBFE; font-weight: 500; font-size: 1.05rem;">Quick 5-10 minute assessment</span>
                    </div>
                    <div style="padding: 1rem 1.5rem; background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%); border-radius: 12px; margin: 1rem 0; border: 1px solid #3B82F6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">🧠</span>
                        <span style="color: #BFDBFE; font-weight: 500; font-size: 1.05rem;">AI-generated technical questions</span>
                    </div>
                    <div style="padding: 1rem 1.5rem; background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%); border-radius: 12px; margin: 1rem 0; border: 1px solid #3B82F6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">🔒</span>
                        <span style="color: #BFDBFE; font-weight: 500; font-size: 1.05rem;">Secure and confidential</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
            
            if st.button("🚀 Start Screening", use_container_width=True, type="primary"):
                st.session_state.started = True
                handle_greeting()
                st.rerun()
    
    # Chat interface
    else:
        # Header
        st.markdown("""
        <div class="header-container">
            <h1 style="margin: 0; font-size: 1.8rem;">🤖 TechScreen AI</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Screening in progress...</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress bar
        progress = get_progress()
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress}%"></div>
        </div>
        <p style="text-align: center; color: #64748B; font-size: 0.9rem; margin-top: 0.5rem;">
            Progress: {progress}% Complete
        </p>
        """, unsafe_allow_html=True)
        
        # Chat container
        chat_container = st.container()
        with chat_container:
            display_messages()
        
        # Input area
        if st.session_state.current_step != 'ended':
            with st.container():
                # Special handling for tech_stack step with checkboxes
                if st.session_state.current_step == 'tech_stack':
                    st.markdown("### Select your technologies:")
                    
                    # Create columns for checkboxes
                    cols = st.columns(4)
                    for idx, tech in enumerate(TECH_STACK_OPTIONS):
                        col_idx = idx % 4
                        with cols[col_idx]:
                            if st.checkbox(tech, key=f"tech_{tech}"):
                                if tech not in st.session_state.selected_techs:
                                    st.session_state.selected_techs.append(tech)
                            else:
                                if tech in st.session_state.selected_techs:
                                    st.session_state.selected_techs.remove(tech)
                    
                    st.markdown(f"**Selected:** {len(st.session_state.selected_techs)} technologies")
                    
                    if st.button("✅ Confirm Selection", use_container_width=True, type="primary"):
                        if st.session_state.selected_techs:
                            user_input = ", ".join(st.session_state.selected_techs)
                            process_user_input(user_input)
                            st.session_state.selected_techs = []
                            st.rerun()
                        else:
                            st.warning("Please select at least one technology.")
                else:
                    # Regular text input for other steps
                    user_input = st.text_input(
                        "Your message:",
                        key=f"user_input_{st.session_state.input_key}",
                        placeholder="Type your response here and press Enter...",
                        label_visibility="collapsed",
                        on_change=handle_input_submit
                    )
                    
                    # Check if submit was triggered
                    if st.session_state.submit_triggered and user_input:
                        process_user_input(user_input)
                        st.session_state.input_key += 1
                        st.session_state.submit_triggered = False
                        st.rerun()
                    
                    col1, col2 = st.columns([6, 1])
                    with col2:
                        send_button = st.button("Send 📨", use_container_width=True)
                    
                    if send_button and user_input:
                        process_user_input(user_input)
                        st.session_state.input_key += 1
                        st.rerun()
                
                # Exit hint
                st.caption("💡 You can type 'bye', 'exit', or 'quit' at any time to end the conversation.")
        
        else:
            st.success("✅ Screening completed! Thank you for your time.")
            
            # Save session button
            if st.button("💾 Save Session Data"):
                filename = save_session_data()
                if filename:
                    st.success(f"Session saved to: {filename}")
            
            # Restart button
            if st.button("🔄 Start New Screening"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()
