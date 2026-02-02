from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Models ==============

class Message(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # 'bot' or 'user'
    content: str
    message_type: str = "text"  # 'text', 'options', 'tech_stack', 'questions'
    options: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CandidateInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    years_of_experience: Optional[int] = None
    desired_positions: Optional[List[str]] = None
    current_location: Optional[str] = None
    tech_stack: Optional[List[str]] = None

class ChatSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_info: CandidateInfo = Field(default_factory=CandidateInfo)
    messages: List[Message] = []
    current_step: str = "greeting"  # greeting, name, email, phone, experience, position, location, tech_stack, questions, summary, ended
    questions_asked: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    bot_messages: List[Message]
    current_step: str
    candidate_info: CandidateInfo

# ============== Conversation Flow ==============

CONVERSATION_STEPS = [
    "greeting",
    "name",
    "email",
    "phone",
    "experience",
    "position",
    "location",
    "tech_stack",
    "questions",
    "summary",
    "ended"
]

EXIT_KEYWORDS = ["bye", "goodbye", "exit", "quit", "end", "stop", "thank you", "thanks", "done"]

TECH_STACK_OPTIONS = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "PHP",
    "React", "Vue.js", "Angular", "Next.js", "Node.js", "Express.js", "Django", "Flask", "FastAPI", "Spring Boot",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
    "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
    "Git", "Linux", "REST APIs", "GraphQL", "CI/CD"
]

POSITION_OPTIONS = [
    "Software Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Data Scientist",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Mobile Developer",
    "QA Engineer"
]

def check_exit_intent(message: str) -> bool:
    """Check if the user wants to end the conversation."""
    message_lower = message.lower().strip()
    return any(keyword in message_lower for keyword in EXIT_KEYWORDS)

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number (basic validation)."""
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10

def get_greeting_message() -> Message:
    """Generate the initial greeting message."""
    return Message(
        role="bot",
        content="Hello! 👋 Welcome to TalentScout's AI Screening Assistant.\n\nI'm here to help gather some information about your background and assess your technical skills for potential opportunities. This conversation will take about 5-10 minutes.\n\nLet's get started! What is your full name?",
        message_type="text"
    )

def get_step_prompt(step: str, candidate_info: CandidateInfo) -> List[Message]:
    """Get the prompt message for each conversation step."""
    messages = []
    
    if step == "name":
        messages.append(Message(
            role="bot",
            content="What is your full name?",
            message_type="text"
        ))
    elif step == "email":
        messages.append(Message(
            role="bot",
            content=f"Nice to meet you, {candidate_info.full_name}! 🎉\n\nWhat is your email address?",
            message_type="text"
        ))
    elif step == "phone":
        messages.append(Message(
            role="bot",
            content="Great! What is your phone number?",
            message_type="text"
        ))
    elif step == "experience":
        messages.append(Message(
            role="bot",
            content="How many years of professional experience do you have?",
            message_type="options",
            options=["0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"]
        ))
    elif step == "position":
        messages.append(Message(
            role="bot",
            content="What position(s) are you interested in? You can select multiple.",
            message_type="options",
            options=POSITION_OPTIONS
        ))
    elif step == "location":
        messages.append(Message(
            role="bot",
            content="Where are you currently located? (City, Country)",
            message_type="text"
        ))
    elif step == "tech_stack":
        messages.append(Message(
            role="bot",
            content="Now, let's talk about your technical skills! 💻\n\nPlease select all the technologies you're proficient in:",
            message_type="tech_stack",
            options=TECH_STACK_OPTIONS
        ))
    elif step == "summary":
        summary = f"""Thank you for completing the screening, {candidate_info.full_name}! 🎉

Here's a summary of the information you provided:

📧 **Email:** {candidate_info.email}
📱 **Phone:** {candidate_info.phone}
💼 **Experience:** {candidate_info.years_of_experience} years
🎯 **Desired Position(s):** {', '.join(candidate_info.desired_positions or [])}
📍 **Location:** {candidate_info.current_location}
🛠️ **Tech Stack:** {', '.join(candidate_info.tech_stack or [])}

Our recruitment team will review your profile and technical responses. We'll be in touch within 3-5 business days.

Is there anything else you'd like to share or any questions you have for us?"""
        messages.append(Message(
            role="bot",
            content=summary,
            message_type="text"
        ))
    elif step == "ended":
        messages.append(Message(
            role="bot",
            content="Thank you for your time! We appreciate your interest in joining our team. Have a great day! 👋",
            message_type="text"
        ))
    
    return messages

async def generate_technical_questions(tech_stack: List[str]) -> List[Dict[str, str]]:
    """Generate technical questions based on the candidate's tech stack using LLM."""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.error("EMERGENT_LLM_KEY not found")
            return get_fallback_questions(tech_stack)
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"tech-questions-{uuid.uuid4()}",
            system_message="""You are a technical interviewer for a recruitment agency. 
Your task is to generate relevant technical questions based on the candidate's tech stack.
Generate exactly 4 questions that test practical knowledge and problem-solving skills.
Questions should range from intermediate to advanced level.
Format your response as a numbered list with clear, concise questions.
Focus on real-world scenarios and best practices."""
        ).with_model("openai", "gpt-4o")
        
        tech_list = ", ".join(tech_stack[:5])  # Limit to top 5 technologies
        prompt = f"""Generate 4 technical interview questions for a candidate proficient in: {tech_list}

Include:
1. One conceptual question about core principles
2. One practical coding/implementation question
3. One question about best practices or design patterns
4. One problem-solving scenario question

Format each question clearly and make them specific to the technologies mentioned."""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse the response into individual questions
        questions = []
        lines = response.strip().split('\n')
        current_question = ""
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                if current_question:
                    questions.append({"question": current_question.strip(), "tech": tech_list})
                # Remove numbering and clean up
                current_question = re.sub(r'^[\d\.\-\)\*]+\s*', '', line)
            elif line and current_question:
                current_question += " " + line
        
        if current_question:
            questions.append({"question": current_question.strip(), "tech": tech_list})
        
        # Ensure we have at least 3 questions
        if len(questions) < 3:
            return get_fallback_questions(tech_stack)
        
        return questions[:4]
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return get_fallback_questions(tech_stack)

def get_fallback_questions(tech_stack: List[str]) -> List[Dict[str, str]]:
    """Fallback questions if LLM fails."""
    questions = []
    tech_questions_map = {
        "Python": [
            "Explain the difference between a list and a tuple in Python. When would you use each?",
            "What are decorators in Python and how would you implement one?"
        ],
        "JavaScript": [
            "Explain the concept of closures in JavaScript with an example.",
            "What is the difference between == and === in JavaScript?"
        ],
        "React": [
            "Explain the useEffect hook and its cleanup function.",
            "What are the benefits of using React hooks over class components?"
        ],
        "Node.js": [
            "How does the event loop work in Node.js?",
            "Explain the difference between process.nextTick() and setImmediate()."
        ],
        "SQL": [
            "Explain the difference between INNER JOIN and LEFT JOIN.",
            "How would you optimize a slow-running SQL query?"
        ],
        "MongoDB": [
            "When would you use MongoDB over a relational database?",
            "Explain indexing in MongoDB and its importance."
        ],
        "Docker": [
            "What is the difference between a Docker image and a container?",
            "How would you optimize a Dockerfile for production?"
        ],
        "AWS": [
            "Explain the difference between EC2 and Lambda. When would you use each?",
            "How would you design a highly available application on AWS?"
        ]
    }
    
    for tech in tech_stack[:4]:
        if tech in tech_questions_map:
            questions.append({"question": tech_questions_map[tech][0], "tech": tech})
    
    # Fill with generic questions if needed
    generic_questions = [
        {"question": "Describe a challenging technical problem you solved recently.", "tech": "General"},
        {"question": "How do you approach debugging a complex issue in production?", "tech": "General"},
        {"question": "Explain how you would design a scalable REST API.", "tech": "General"},
        {"question": "What testing strategies do you use in your projects?", "tech": "General"}
    ]
    
    while len(questions) < 4:
        questions.append(generic_questions[len(questions) % len(generic_questions)])
    
    return questions[:4]

# ============== API Endpoints ==============

@api_router.get("/")
async def root():
    return {"message": "TalentScout AI Screening API"}

@api_router.post("/chat/session", response_model=ChatSession)
async def create_session():
    """Create a new chat session."""
    session = ChatSession()
    greeting = get_greeting_message()
    session.messages.append(greeting)
    session.current_step = "name"
    
    # Save to database
    doc = session.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    for msg in doc['messages']:
        msg['timestamp'] = msg['timestamp'].isoformat()
    
    await db.chat_sessions.insert_one(doc)
    
    return session

@api_router.get("/chat/session/{session_id}", response_model=ChatSession)
async def get_session(session_id: str):
    """Get an existing chat session."""
    session_doc = await db.chat_sessions.find_one({"id": session_id}, {"_id": 0})
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Convert ISO strings back to datetime
    if isinstance(session_doc['created_at'], str):
        session_doc['created_at'] = datetime.fromisoformat(session_doc['created_at'])
    if isinstance(session_doc['updated_at'], str):
        session_doc['updated_at'] = datetime.fromisoformat(session_doc['updated_at'])
    for msg in session_doc['messages']:
        if isinstance(msg['timestamp'], str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    return ChatSession(**session_doc)

@api_router.post("/chat/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Process user message and return bot response."""
    session_doc = await db.chat_sessions.find_one({"id": request.session_id}, {"_id": 0})
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Convert timestamps
    if isinstance(session_doc['created_at'], str):
        session_doc['created_at'] = datetime.fromisoformat(session_doc['created_at'])
    if isinstance(session_doc['updated_at'], str):
        session_doc['updated_at'] = datetime.fromisoformat(session_doc['updated_at'])
    for msg in session_doc['messages']:
        if isinstance(msg['timestamp'], str):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
    
    session = ChatSession(**session_doc)
    user_message = request.message.strip()
    
    # Add user message
    user_msg = Message(role="user", content=user_message)
    session.messages.append(user_msg)
    
    bot_messages = []
    
    # Check for exit intent
    if check_exit_intent(user_message):
        session.current_step = "ended"
        end_messages = get_step_prompt("ended", session.candidate_info)
        bot_messages.extend(end_messages)
        session.messages.extend(end_messages)
    else:
        # Process based on current step
        current_step = session.current_step
        next_step = current_step
        
        if current_step == "name":
            if len(user_message) >= 2:
                session.candidate_info.full_name = user_message
                next_step = "email"
            else:
                bot_messages.append(Message(
                    role="bot",
                    content="Please provide your full name (at least 2 characters).",
                    message_type="text"
                ))
        
        elif current_step == "email":
            if validate_email(user_message):
                session.candidate_info.email = user_message
                next_step = "phone"
            else:
                bot_messages.append(Message(
                    role="bot",
                    content="That doesn't look like a valid email address. Please enter a valid email (e.g., name@example.com).",
                    message_type="text"
                ))
        
        elif current_step == "phone":
            if validate_phone(user_message):
                session.candidate_info.phone = user_message
                next_step = "experience"
            else:
                bot_messages.append(Message(
                    role="bot",
                    content="Please enter a valid phone number (at least 10 digits).",
                    message_type="text"
                ))
        
        elif current_step == "experience":
            # Parse experience from options or text
            exp_map = {"0-1 years": 0, "1-3 years": 2, "3-5 years": 4, "5-10 years": 7, "10+ years": 12}
            if user_message in exp_map:
                session.candidate_info.years_of_experience = exp_map[user_message]
            else:
                # Try to extract number
                numbers = re.findall(r'\d+', user_message)
                if numbers:
                    session.candidate_info.years_of_experience = int(numbers[0])
                else:
                    session.candidate_info.years_of_experience = 0
            next_step = "position"
        
        elif current_step == "position":
            # Handle multiple positions
            positions = [p.strip() for p in user_message.split(',')]
            valid_positions = [p for p in positions if p in POSITION_OPTIONS or len(p) > 2]
            if valid_positions:
                session.candidate_info.desired_positions = valid_positions
                next_step = "location"
            else:
                bot_messages.append(Message(
                    role="bot",
                    content="Please select at least one position from the options or enter your desired role.",
                    message_type="options",
                    options=POSITION_OPTIONS
                ))
        
        elif current_step == "location":
            if len(user_message) >= 2:
                session.candidate_info.current_location = user_message
                next_step = "tech_stack"
            else:
                bot_messages.append(Message(
                    role="bot",
                    content="Please provide your current location (City, Country).",
                    message_type="text"
                ))
        
        elif current_step == "tech_stack":
            # Parse tech stack
            techs = [t.strip() for t in user_message.split(',')]
            valid_techs = [t for t in techs if t in TECH_STACK_OPTIONS or len(t) > 1]
            if valid_techs:
                session.candidate_info.tech_stack = valid_techs
                next_step = "questions"
            else:
                bot_messages.append(Message(
                    role="bot",
                    content="Please select at least one technology from your skill set.",
                    message_type="tech_stack",
                    options=TECH_STACK_OPTIONS
                ))
        
        elif current_step == "questions":
            # Store the answer to the current question
            if session.questions_asked:
                current_q_index = len([q for q in session.questions_asked if 'answer' in q])
                if current_q_index < len(session.questions_asked):
                    session.questions_asked[current_q_index]['answer'] = user_message
            
            # Check if we need to generate questions
            if not session.questions_asked:
                # Generate technical questions
                questions = await generate_technical_questions(session.candidate_info.tech_stack or [])
                session.questions_asked = questions
                
                # Send intro message
                bot_messages.append(Message(
                    role="bot",
                    content=f"Excellent! Now let's assess your technical knowledge. I'll ask you {len(questions)} questions based on your tech stack. Take your time to answer each one. 📝",
                    message_type="text"
                ))
                
                # Send first question
                if questions:
                    bot_messages.append(Message(
                        role="bot",
                        content=f"**Question 1/{len(questions)}:**\n\n{questions[0]['question']}",
                        message_type="questions"
                    ))
            else:
                # Check how many questions answered
                answered = len([q for q in session.questions_asked if 'answer' in q])
                total = len(session.questions_asked)
                
                if answered < total:
                    # Ask next question
                    next_q = session.questions_asked[answered]
                    bot_messages.append(Message(
                        role="bot",
                        content=f"**Question {answered + 1}/{total}:**\n\n{next_q['question']}",
                        message_type="questions"
                    ))
                else:
                    # All questions answered, move to summary
                    next_step = "summary"
        
        elif current_step == "summary":
            next_step = "ended"
        
        # Get next step prompts if step changed
        if next_step != current_step and not bot_messages:
            step_messages = get_step_prompt(next_step, session.candidate_info)
            bot_messages.extend(step_messages)
        elif next_step != current_step and next_step not in ["questions"]:
            step_messages = get_step_prompt(next_step, session.candidate_info)
            bot_messages.extend(step_messages)
        
        session.current_step = next_step
    
    # Add bot messages to session
    session.messages.extend(bot_messages)
    session.updated_at = datetime.now(timezone.utc)
    
    # Update database
    update_doc = session.model_dump()
    update_doc['created_at'] = update_doc['created_at'].isoformat()
    update_doc['updated_at'] = update_doc['updated_at'].isoformat()
    for msg in update_doc['messages']:
        msg['timestamp'] = msg['timestamp'].isoformat()
    
    await db.chat_sessions.update_one(
        {"id": request.session_id},
        {"$set": update_doc}
    )
    
    return ChatResponse(
        session_id=session.id,
        bot_messages=bot_messages,
        current_step=session.current_step,
        candidate_info=session.candidate_info
    )

@api_router.get("/candidates", response_model=List[CandidateInfo])
async def get_candidates():
    """Get all candidates who completed the screening."""
    sessions = await db.chat_sessions.find(
        {"current_step": {"$in": ["summary", "ended"]}},
        {"_id": 0, "candidate_info": 1}
    ).to_list(100)
    
    return [s['candidate_info'] for s in sessions if s.get('candidate_info', {}).get('full_name')]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
