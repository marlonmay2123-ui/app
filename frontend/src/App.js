import { useState, useEffect, useRef, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Send, MessageSquare, User, ChevronRight, Code, CheckCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Tech stack categories for organized display
const TECH_CATEGORIES = {
  "Languages": ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "PHP"],
  "Frontend": ["React", "Vue.js", "Angular", "Next.js"],
  "Backend": ["Node.js", "Express.js", "Django", "Flask", "FastAPI", "Spring Boot"],
  "Databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite"],
  "Cloud & DevOps": ["AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform"],
  "AI/ML": ["TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy"],
  "Tools": ["Git", "Linux", "REST APIs", "GraphQL", "CI/CD"]
};

// Position options
const POSITION_OPTIONS = [
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
];

// Experience options
const EXPERIENCE_OPTIONS = ["0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"];

// Welcome Screen Component
const WelcomeScreen = ({ onStart }) => {
  return (
    <div className="welcome-screen dot-pattern" data-testid="welcome-screen">
      <div className="welcome-card animate-fade-in-up">
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-gradient-to-br from-[#0052FF] to-[#0041CC] rounded-2xl flex items-center justify-center shadow-lg">
            <MessageSquare className="w-10 h-10 text-white" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-slate-900 mb-3">
          TalentScout AI
        </h1>
        <p className="text-slate-600 mb-8 leading-relaxed">
          Welcome to our AI-powered screening assistant. I'll help gather information about your background and assess your technical skills for exciting opportunities.
        </p>
        <div className="flex flex-col gap-3 mb-8 text-left">
          <div className="flex items-center gap-3 text-slate-700">
            <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
            <span>Quick 5-10 minute assessment</span>
          </div>
          <div className="flex items-center gap-3 text-slate-700">
            <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
            <span>Personalized technical questions</span>
          </div>
          <div className="flex items-center gap-3 text-slate-700">
            <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
            <span>Secure and confidential</span>
          </div>
        </div>
        <Button 
          data-testid="start-screening-btn"
          onClick={onStart}
          className="w-full bg-[#0052FF] hover:bg-[#0041CC] text-white rounded-full py-6 text-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300"
        >
          Start Screening
          <ChevronRight className="ml-2 w-5 h-5" />
        </Button>
      </div>
    </div>
  );
};

// Chat Header Component
const ChatHeader = ({ step, candidateName }) => {
  const steps = ["name", "email", "phone", "experience", "position", "location", "tech_stack", "questions", "summary"];
  const currentIndex = steps.indexOf(step);
  const progress = step === "ended" ? 100 : ((currentIndex + 1) / steps.length) * 100;

  return (
    <div className="chat-header" data-testid="chat-header">
      <div className="max-w-4xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[#0052FF] to-[#0041CC] rounded-xl flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-900">TalentScout AI</h2>
              <p className="text-sm text-slate-500">
                {candidateName ? `Screening ${candidateName}` : "AI Screening Assistant"}
              </p>
            </div>
          </div>
          <Badge variant="secondary" className="text-xs">
            {step === "ended" ? "Complete" : `Step ${currentIndex + 1}/${steps.length}`}
          </Badge>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${progress}%` }}
            data-testid="progress-bar"
          />
        </div>
      </div>
    </div>
  );
};

// Message Bubble Component
const MessageBubble = ({ message, isLatest }) => {
  const isBot = message.role === "bot";
  
  // Simple markdown-like formatting
  const formatContent = (content) => {
    if (!content) return "";
    
    // Handle bold
    let formatted = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Handle line breaks
    formatted = formatted.replace(/\n/g, '<br />');
    
    return formatted;
  };

  return (
    <div 
      className={`flex ${isBot ? 'justify-start' : 'justify-end'} ${isLatest ? 'animate-fade-in-up' : ''}`}
      data-testid={`message-${message.id}`}
    >
      <div className={`message-bubble ${isBot ? 'bot' : 'user'}`}>
        {isBot && (
          <div className="flex items-center gap-2 mb-2 text-xs text-slate-500">
            <Code className="w-3 h-3" />
            <span>TalentScout AI</span>
          </div>
        )}
        <div 
          className="message-content"
          dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
        />
      </div>
    </div>
  );
};

// Typing Indicator Component
const TypingIndicator = () => (
  <div className="typing-indicator" data-testid="typing-indicator">
    <span className="typing-dot" />
    <span className="typing-dot" />
    <span className="typing-dot" />
  </div>
);

// Options Selector Component
const OptionsSelector = ({ options, onSelect, multiSelect = false, selectedOptions = [] }) => {
  const [selected, setSelected] = useState(selectedOptions);

  const handleSelect = (option) => {
    if (multiSelect) {
      const newSelected = selected.includes(option)
        ? selected.filter(o => o !== option)
        : [...selected, option];
      setSelected(newSelected);
    } else {
      onSelect(option);
    }
  };

  const handleConfirm = () => {
    if (selected.length > 0) {
      onSelect(selected.join(", "));
    } else {
      toast.error("Please select at least one option");
    }
  };

  return (
    <div className="space-y-2 my-4" data-testid="options-selector">
      {options.map((option, index) => (
        <button
          key={index}
          onClick={() => handleSelect(option)}
          className={`option-btn ${selected.includes(option) ? 'selected' : ''}`}
          data-testid={`option-${option.toLowerCase().replace(/\s+/g, '-')}`}
        >
          {option}
        </button>
      ))}
      {multiSelect && (
        <Button
          onClick={handleConfirm}
          className="w-full mt-4 bg-[#0052FF] hover:bg-[#0041CC] rounded-full"
          disabled={selected.length === 0}
          data-testid="confirm-selection-btn"
        >
          Confirm Selection ({selected.length})
        </Button>
      )}
    </div>
  );
};

// Tech Stack Selector Component
const TechStackSelector = ({ onSelect }) => {
  const [selectedTechs, setSelectedTechs] = useState([]);

  const toggleTech = (tech) => {
    setSelectedTechs(prev => 
      prev.includes(tech) 
        ? prev.filter(t => t !== tech)
        : [...prev, tech]
    );
  };

  const handleConfirm = () => {
    if (selectedTechs.length > 0) {
      onSelect(selectedTechs.join(", "));
    } else {
      toast.error("Please select at least one technology");
    }
  };

  return (
    <div className="my-4 space-y-6" data-testid="tech-stack-selector">
      {Object.entries(TECH_CATEGORIES).map(([category, techs]) => (
        <div key={category}>
          <h4 className="text-sm font-semibold text-slate-600 mb-2">{category}</h4>
          <div className="flex flex-wrap gap-2">
            {techs.map(tech => (
              <button
                key={tech}
                onClick={() => toggleTech(tech)}
                className={`tech-pill ${selectedTechs.includes(tech) ? 'selected' : ''}`}
                data-testid={`tech-${tech.toLowerCase().replace(/[.\s+]/g, '-')}`}
              >
                {tech}
              </button>
            ))}
          </div>
        </div>
      ))}
      <div className="pt-4 border-t border-slate-200">
        <p className="text-sm text-slate-500 mb-3">
          Selected: {selectedTechs.length > 0 ? selectedTechs.join(", ") : "None"}
        </p>
        <Button
          onClick={handleConfirm}
          className="w-full bg-[#0052FF] hover:bg-[#0041CC] rounded-full py-6"
          disabled={selectedTechs.length === 0}
          data-testid="confirm-tech-stack-btn"
        >
          Confirm Tech Stack ({selectedTechs.length})
        </Button>
      </div>
    </div>
  );
};

// Chat Input Component
const ChatInput = ({ onSend, disabled, placeholder }) => {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative" data-testid="chat-input-form">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={placeholder || "Type your response..."}
        disabled={disabled}
        className="chat-input"
        data-testid="chat-input"
      />
      <button
        type="submit"
        disabled={!input.trim() || disabled}
        className="send-btn"
        aria-label="Send message"
        data-testid="send-message-btn"
      >
        {disabled ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Send className="w-5 h-5" />
        )}
      </button>
    </form>
  );
};

// Main Chat Component
const ChatScreen = () => {
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState("greeting");
  const [candidateInfo, setCandidateInfo] = useState({});
  const messagesEndRef = useRef(null);
  const [lastMessageType, setLastMessageType] = useState("text");

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Initialize session
  useEffect(() => {
    const initSession = async () => {
      try {
        setLoading(true);
        const response = await axios.post(`${API}/chat/session`);
        setSession(response.data);
        setMessages(response.data.messages || []);
        setCurrentStep(response.data.current_step);
        
        if (response.data.messages?.length > 0) {
          const lastMsg = response.data.messages[response.data.messages.length - 1];
          setLastMessageType(lastMsg.message_type || "text");
        }
      } catch (error) {
        console.error("Failed to create session:", error);
        toast.error("Failed to start chat session. Please refresh the page.");
      } finally {
        setLoading(false);
      }
    };

    initSession();
  }, []);

  const sendMessage = async (message) => {
    if (!session || loading) return;

    // Add user message to UI immediately
    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message,
      message_type: "text"
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await axios.post(`${API}/chat/send`, {
        session_id: session.id,
        message: message
      });

      // Update state with bot responses
      if (response.data.bot_messages?.length > 0) {
        setMessages(prev => [...prev, ...response.data.bot_messages]);
        
        const lastBotMsg = response.data.bot_messages[response.data.bot_messages.length - 1];
        setLastMessageType(lastBotMsg.message_type || "text");
      }
      
      setCurrentStep(response.data.current_step);
      setCandidateInfo(response.data.candidate_info || {});
    } catch (error) {
      console.error("Failed to send message:", error);
      toast.error("Failed to send message. Please try again.");
      // Remove the failed user message
      setMessages(prev => prev.filter(m => m.id !== userMsg.id));
    } finally {
      setLoading(false);
    }
  };

  // Get input placeholder based on current step
  const getPlaceholder = () => {
    const placeholders = {
      name: "Enter your full name...",
      email: "Enter your email address...",
      phone: "Enter your phone number...",
      experience: "Select your experience level...",
      position: "Select desired position(s)...",
      location: "Enter your location (City, Country)...",
      tech_stack: "Select your technologies...",
      questions: "Type your answer...",
      summary: "Any additional comments...",
      ended: "Chat ended"
    };
    return placeholders[currentStep] || "Type your response...";
  };

  // Check if we should show options/tech selector
  const shouldShowOptions = () => {
    if (loading) return false;
    const lastBotMessage = [...messages].reverse().find(m => m.role === "bot");
    return lastBotMessage?.message_type === "options" && currentStep !== "ended";
  };

  const shouldShowTechStack = () => {
    if (loading) return false;
    const lastBotMessage = [...messages].reverse().find(m => m.role === "bot");
    return lastBotMessage?.message_type === "tech_stack" && currentStep !== "ended";
  };

  // Get options for current step
  const getCurrentOptions = () => {
    if (currentStep === "experience") return EXPERIENCE_OPTIONS;
    if (currentStep === "position") return POSITION_OPTIONS;
    return [];
  };

  return (
    <div className="chat-container" data-testid="chat-screen">
      <ChatHeader step={currentStep} candidateName={candidateInfo?.full_name} />
      
      <ScrollArea className="flex-1">
        <div className="chat-messages max-w-4xl mx-auto">
          {messages.map((message, index) => (
            <MessageBubble 
              key={message.id || index} 
              message={message}
              isLatest={index === messages.length - 1}
            />
          ))}
          
          {loading && <TypingIndicator />}
          
          {/* Options Selector */}
          {shouldShowOptions() && (
            <OptionsSelector
              options={getCurrentOptions()}
              onSelect={sendMessage}
              multiSelect={currentStep === "position"}
            />
          )}
          
          {/* Tech Stack Selector */}
          {shouldShowTechStack() && (
            <TechStackSelector onSelect={sendMessage} />
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      
      <div className="chat-input-container">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSend={sendMessage}
            disabled={loading || currentStep === "ended" || shouldShowOptions() || shouldShowTechStack()}
            placeholder={getPlaceholder()}
          />
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [started, setStarted] = useState(false);

  return (
    <div className="App">
      <Toaster position="top-center" richColors />
      {!started ? (
        <WelcomeScreen onStart={() => setStarted(true)} />
      ) : (
        <ChatScreen />
      )}
    </div>
  );
}

export default App;
