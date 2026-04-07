import { useState, useEffect, useRef, useLayoutEffect } from 'react';
import {
  Send, Paperclip, Mic, Settings, Search, Plus, Moon, Sun,
  Database, MessageSquare, ChevronRight, User, Bot, Trash2,
  FileText, Headphones, BarChart, ChevronLeft, Loader2, Upload, Eye, EyeOff,
  Copy, Check, X, Download
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Lenis from 'lenis';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { chatService, ChatResponse, Source, SystemStatus, InventoryItem } from './services/api';

// // Define the types
type Role = 'student' | 'teacher' | 'admin';



interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  timestamp: Date;
  metadata?: {
    score?: number;
    source?: string;
    sources?: Source[];
  };
}

interface ChatHistory {
  id: string;
  title: string;
  date: Date;
}

interface UploadTask {
  id: string;
  name: string;
  status: 'uploading' | 'indexing' | 'completed' | 'error';
  progress: number;
}

const CodeBlock = ({ node, inline, className, children, theme, ...props }: any) => {
  const match = /language-(\w+)/.exec(className || '');
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!inline && match) {
    return (
      <div className="code-block-wrapper">
        <div className="code-header">
          <span className="code-lang">{match[1]}</span>
          <button onClick={handleCopy} className="copy-btn">
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? 'Copied!' : 'Copy code'}
          </button>
        </div>
        <SyntaxHighlighter
          style={theme === 'dark' ? vscDarkPlus : oneLight}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      </div>
    );
  }

  return (
    <code className={className} {...props}>
      {children}
    </code>
  );
};

export default function App() {
  // State for Role-Based Access Control
  const [userRole, setUserRole] = useState<Role>('student');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false); // New State
  // Inside export default function App() { [cite: 13]
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleLoginAttempt = (role: Role) => {
    if (role === 'student') {
      handleLogin('student');
      return;
    }
    // Open the new custom modal instead of prompt()
    setSelectedRole(role);
    setShowLoginModal(true);
    setLoginError('');
  };

  const submitLogin = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const result = await response.json();

      if (result.success) {
        setShowLoginModal(false);
        setUsername('');
        setPassword('');
        handleLogin(result.role as Role);
      } else {
        setLoginError(result.message || "Invalid credentials.");
      }
    } catch (error) {
      setLoginError("Authentication Server Error. Ensure api.py is running.");
    }
  };

  const handleLogin = (role: Role) => {
    setUserRole(role);
    setIsInitializing(true); // Start the BIT loader [cite: 16]

    setTimeout(() => {
      setIsInitializing(false); // Stop loader [cite: 16]
      setIsLoggedIn(true);      // Show Dashboard [cite: 14]
    }, 1000); // 1-second delay to clear the "Ghost" [cite: 16]
  };

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'bot',
      content: 'Hello, I am the College Assistant. How can I assist you today?',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [history] = useState<ChatHistory[]>([
    { id: '1', title: 'Syllabus', date: new Date() },
    { id: '2', title: 'Fees', date: new Date(Date.now() - 86400000) },
    { id: '3', title: 'About Department', date: new Date(Date.now() - 172800000) },
  ]);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const bulkFileInputRef = useRef<HTMLInputElement>(null);
  const lenisRef = useRef<Lenis | null>(null);

  const [isKBOpen, setIsKBOpen] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [kbStatus, setKBStatus] = useState<SystemStatus | null>(null);
  const [isKBLoading, setIsKBLoading] = useState(false);
  const [kbSearch, setKBSearch] = useState('');
  const [uploadQueue, setUploadQueue] = useState<UploadTask[]>([]);
  const [isUploadPanelOpen, setIsUploadStatusVisible] = useState(false);
  const [isUploadPanelMinimized, setIsUploadStatusMinimized] = useState(false);

  const fetchKBStatus = async () => {
    console.log("Fetching Knowledge Base status...");
    setIsKBLoading(true);
    try {
      const status = await chatService.getStatus();
      console.log("KB Status Received:", status);
      if (status && status.inventory) {
        setKBStatus(status);
      } else {
        console.warn("KB Status received but inventory is missing or empty.");
      }
    } catch (error) {
      console.error('CRITICAL: Failed to fetch KB status:', error);
      alert("Backend Connection Error: Could not retrieve Knowledge Base. Ensure api.py is running on port 8000.");
    } finally {
      setIsKBLoading(false);
    }
  };

  useEffect(() => {
    if (isKBOpen) {
      fetchKBStatus();
    } else {
      setSelectedFolder(null);
    }
  }, [isKBOpen]);

  const handleDeleteFile = async (filePath: string) => {
    if (!window.confirm("Are you sure you want to permanently delete this file and its vectors?")) return;

    try {
      await chatService.deleteFile(filePath);
      fetchKBStatus(); // Refresh the list
    } catch (error) {
      alert("Failed to delete file.");
    }
  };

  const folders = [
    { id: 'pdf', name: 'PDF Documents', icon: FileText, color: '#ef4444' },
    { id: 'csv', name: 'Structured Data', icon: BarChart, color: '#10b981' },
    { id: 'audio', name: 'Audio Recordings', icon: Headphones, color: '#8b5cf6' },
    { id: 'txt', name: 'Plain Text', icon: MessageSquare, color: '#f59e0b' },
  ];

  const getFileCount = (type: string) => {
    if (!kbStatus) return 0;
    return kbStatus.inventory.filter(f => f.type === type).length;
  };

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setIsSidebarOpen(false);
      } else {
        setIsSidebarOpen(true);
      }
    };

    window.addEventListener('resize', handleResize);
    // Run once on mount
    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useLayoutEffect(() => {
    if (scrollRef.current) {
      const lenis = new Lenis({
        wrapper: scrollRef.current,
        content: scrollRef.current.firstElementChild as HTMLElement,
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      });

      lenisRef.current = lenis;

      function raf(time: number) {
        lenis.raf(time);
        requestAnimationFrame(raf);
      }

      requestAnimationFrame(raf);

      return () => {
        lenis.destroy();
      };
    }
  }, []);

  const scrollToBottom = () => {
    if (lenisRef.current && scrollRef.current) {
      lenisRef.current.scrollTo(scrollRef.current.scrollHeight, {
        duration: 1.5,
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const result: ChatResponse = await chatService.sendMessage(query);

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: result.response,
        timestamp: new Date(),
        metadata: {
          score: result.sources[0]?.score,
          source: result.sources[0]?.metadata?.source || 'Knowledge Base',
          sources: result.sources
        }
      };
      setMessages(prev => [...prev, botResponse]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        content: "I'm sorry, I encountered an error while processing your request. Please ensure the backend server is running.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadSingleFile(file);
  };

  const handleBulkUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const filesArray = Array.from(files);
    for (const file of filesArray) {
      uploadSingleFile(file); // Run in parallel
    }
  };

  const uploadSingleFile = async (file: File) => {
    // 1. Define "Academic" keywords
    const academicKeywords = ['syllabus', 'assignment', 'notes', 'bit', 'durg', 'lecture', 'exam', 'result', 'timetable'];

    // 2. Check if the file is an image or document
    const isAcademic = academicKeywords.some(keyword =>
      file.name.toLowerCase().includes(keyword)
    );

    // 3. Validation Check
    if (!isAcademic && !file.type.startsWith('image/')) {
      alert("Access Denied: Please upload only BIT-related or Study-related documents.");
      return; // Stop the upload immediately
    }

    const taskId = Math.random().toString(36).substring(7);
    const newTask: UploadTask = {
      id: taskId,
      name: file.name,
      status: 'uploading',
      progress: 0
    };

    setUploadQueue(prev => [newTask, ...prev]);
    setIsUploadStatusVisible(true);
    setIsUploadStatusMinimized(false);

    try {
      // Simulate upload progress
      const interval = setInterval(() => {
        setUploadQueue(prev => prev.map(t =>
          t.id === taskId ? { ...t, progress: Math.min(t.progress + 20, 90) } : t
        ));
      }, 200);

      await chatService.uploadFile(file);
      clearInterval(interval);

      // Switch to indexing phase
      setUploadQueue(prev => prev.map(t =>
        t.id === taskId ? { ...t, status: 'indexing', progress: 100 } : t
      ));

      // Fetch status to confirm it's being indexed
      await fetchKBStatus();

      // Mark as completed after a brief moment to show 'Indexing'
      setTimeout(() => {
        setUploadQueue(prev => prev.map(t =>
          t.id === taskId ? { ...t, status: 'completed' } : t
        ));
      }, 2000);

    } catch (error) {
      setUploadQueue(prev => prev.map(t =>
        t.id === taskId ? { ...t, status: 'error' } : t
      ));
    }
  };

  const clearCompletedUploads = () => {
    setUploadQueue(prev => prev.filter(t => t.status !== 'completed' && t.status !== 'error'));
    if (uploadQueue.filter(t => t.status !== 'completed' && t.status !== 'error').length === 0) {
      setIsUploadStatusVisible(false);
    }
  };


  if (!isLoggedIn) {
    return (
      <div className="login-screen" style={{
        height: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-main)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Decorative Background Blobs */}
        <div className="decorative-blob-1" />
        <div className="decorative-blob-2" />

        <AnimatePresence mode="wait">
          {isInitializing ? (
            /* --- NEW: SYSTEM INITIALIZING LOADER --- */
            <motion.div
              key="loader"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.1 }}
              className="flex flex-col items-center gap-6"
              style={{ textAlign: 'center', zIndex: 20 }}
            >
              <div className="relative">
                <Loader2 size={60} className="animate-spin text-[var(--accent)]" />
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontWeight: 800, fontSize: '14px' }}>T</div>
              </div>
              <div>
                <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>Initializing System</h2>
                <p style={{ fontSize: '14px', color: 'var(--text-secondary)', letterSpacing: '0.5px' }}>
                  Authenticating {userRole} portal...
                </p>
              </div>
            </motion.div>
          ) : (
            /* --- THE ROLE SELECTION CARD --- */
            <motion.div
              key="card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="login-card"
              style={{
                background: 'var(--bg-glass)',
                backdropFilter: 'blur(12px)',
                border: '1px solid var(--border-glass)',
                padding: '48px',
                borderRadius: '32px',
                textAlign: 'center',
                zIndex: 10,
                maxWidth: '450px',
                width: '90%'
              }}
            >
              <div className="logo-box" style={{ margin: '0 auto 20px', width: '60px', height: '60px', fontSize: '24px' }}>T</div>
              <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '8px' }}>Academia RAG</h1>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '40px' }}>Select your portal to continue</p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {[
                  { id: 'student', label: 'Student Portal', icon: User, desc: 'View syllabus & timetables' },
                  { id: 'teacher', label: 'Faculty Portal', icon: Bot, desc: 'Academic assistance & resources' },
                  { id: 'admin', label: 'Admin Dashboard', icon: Settings, desc: 'Manage knowledge base' }
                ].map((role) => (
                  <button
                    key={role.id}
                    onClick={() => handleLoginAttempt(role.id as Role)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '20px',
                      padding: '20px',
                      borderRadius: '16px',
                      border: '1px solid var(--border-glass)',
                      background: 'rgba(255,255,255,0.03)',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.08)'}
                    onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                  >
                    <div style={{ background: 'var(--accent)', padding: '12px', borderRadius: '12px', color: '#000' }}>
                      <role.icon size={24} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '16px' }}>{role.label}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>{role.desc}</div>
                    </div>
                    <ChevronRight size={18} style={{ marginLeft: 'auto', color: 'var(--text-tertiary)' }} />
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <p style={{ position: 'absolute', bottom: '30px', fontSize: '12px', color: 'var(--text-tertiary)' }}>
          • Bhilai Institute of Technology, DURG •
        </p>

        {/* Place this inside the <AnimatePresence> tag in the !isLoggedIn return */}
        {showLoginModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
              background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(12px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
            }}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              style={{
                background: 'rgba(255,255,255,0.05)', padding: '40px', borderRadius: '24px',
                border: '1px solid var(--border-glass)', width: '90%', maxWidth: '400px',
                textAlign: 'center', boxShadow: '0 25px 50px rgba(0,0,0,0.5)'
              }}
            >
              <h2 style={{ marginBottom: '8px', color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                {selectedRole} Portal
              </h2>
              <p style={{ color: 'var(--text-tertiary)', fontSize: '14px', marginBottom: '24px' }}>
                Bhilai Institute of Technology Faculty Login
              </p>

              {loginError && (
                <div style={{ color: '#ff4d4d', marginBottom: '16px', fontSize: '13px', background: 'rgba(255,77,77,0.1)', padding: '8px', borderRadius: '8px' }}>
                  {loginError}
                </div>
              )}

              <input
                type="text" placeholder="Username"
                value={username} onChange={(e) => setUsername(e.target.value)}
                style={{ width: '100%', padding: '14px', marginBottom: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.3)', color: '#fff', outline: 'none' }}
              />
              <div style={{ position: 'relative', width: '100%', marginBottom: '24px' }}>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '14px',
                    paddingRight: '45px', // 👈 Space so text doesn't go under the eye
                    borderRadius: '12px',
                    border: '1px solid var(--border-glass)',
                    background: 'rgba(0,0,0,0.3)',
                    color: '#fff',
                    outline: 'none'
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-tertiary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => setShowLoginModal(false)}
                  style={{ flex: 1, padding: '12px', borderRadius: '12px', border: '1px solid var(--border-glass)', background: 'transparent', color: '#fff', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  onClick={submitLogin}
                  style={{ flex: 1, padding: '12px', borderRadius: '12px', background: 'var(--accent)', color: '#000', fontWeight: 700, border: 'none', cursor: 'pointer' }}
                >
                  Login
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}

      </div>
    );
  }

  return (

    <div className="app-container">
      <div className="decorative-blob-1" />
      <div className="decorative-blob-2" />


      <AnimatePresence>
        {isSidebarOpen && (
          <>
            {/* 1. THE BACKDROP: This captures the click 'outside' the sidebar */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsSidebarOpen(false)}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(0, 0, 0, 0.4)', // Dims the UI
                backdropFilter: 'blur(4px)',      // Professional BIT Glassmorphism
                zIndex: 999,                      // Below sidebar
                cursor: 'pointer'
              }}
            />

            {/* 2. THE SIDEBAR */}
            <motion.aside
              initial={{ x: -300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -300, opacity: 0 }}
              transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
              className={`sidebar ${isSidebarOpen ? 'open' : ''}`} // 👈 This toggle handles the CSS move
              style={{ zIndex: 1000, position: 'fixed', display: isLoggedIn ? 'flex' : 'none' }}
            >
              <div className="sidebar-header">
                <div className="logo-box">T</div>
                <span className="brand-title">Academia RAG</span>
              </div>

              {userRole !== 'admin' && (
                <button className="new-chat-btn" onClick={() => setMessages([messages[0]])}>
                  <Plus size={18} />
                  New Conversation
                </button>
              )}

              {userRole !== 'admin' && (
                <div style={{ flex: 1, overflowY: 'auto' }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    /* FORCE SOLID COLOR: Dark Charcoal for light mode, Light Grey for dark mode */
                    color: theme === 'light' ? '#333333' : '#a0a0a0',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    padding: '10px 24px'
                  }}>
                    Recent Activity
                  </div>
                  {history.map(item => (
                    <div
                      key={item.id}
                      className="history-item"
                      /* FORCE SOLID COLOR for the text and icons */
                      style={{ color: theme === 'light' ? '#222222' : '#ffffff' }}
                    >
                      <MessageSquare size={16} />
                      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.title}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <div style={{ padding: '16px 12px', borderTop: '1px solid var(--border-glass)' }}>
                {userRole === 'admin' && (
                  <>
                    <button
                      className="sidebar-action"
                      onClick={() => setIsKBOpen(true)}
                      style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '12px', padding: '10px', borderRadius: '10px', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                    >
                      <Database size={18} />
                      <span style={{ fontSize: '14px' }}>Knowledge Base</span>
                    </button>

                    <button
                      className="sidebar-action"
                      style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '12px', padding: '10px', borderRadius: '10px', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                    >
                      <Settings size={18} />
                      <span style={{ fontSize: '14px' }}>Settings</span>
                    </button>
                  </>
                )}
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isKBOpen && (
          <div className="kb-overlay" onClick={() => setIsKBOpen(false)}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="kb-panel"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="kb-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div className="logo-box">K</div>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: 700 }}>Knowledge Base</h2>
                    <p style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>Active Intelligence Inventory</p>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    className="icon-btn"
                    onClick={fetchKBStatus}
                    disabled={isKBLoading}
                    title="Sync with Backend"
                  >
                    <motion.div animate={isKBLoading ? { rotate: 360 } : {}} transition={isKBLoading ? { repeat: Infinity, duration: 1, ease: "linear" } : {}}>
                      <Database size={20} />
                    </motion.div>
                  </button>
                  <button className="kb-bulk-upload-btn" onClick={() => bulkFileInputRef.current?.click()}>
                    <Upload size={16} />
                    <span>Bulk Upload</span>
                  </button>
                  <input
                    type="file"
                    ref={bulkFileInputRef}
                    style={{ display: 'none' }}
                    multiple
                    accept=".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg,.csv,.wav,.mp3"
                    onChange={handleBulkUpload}
                  />
                  <button className="icon-btn" onClick={() => setIsKBOpen(false)}>
                    <X size={24} />
                  </button>
                </div>
              </div>

              <div className="kb-stats-bar">
                <div className="stat-item">
                  <span className="stat-label">Knowledge Size</span>
                  <span className="stat-value">{(kbStatus?.total_vectors || 0).toLocaleString()} Vectors</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Loaded Files</span>
                  <span className="stat-value">{kbStatus?.inventory.length || 0} Documents</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Compute Unit</span>
                  <span className="stat-value">{kbStatus?.device || 'Detecting...'}</span>
                </div>
              </div>

              <div className="kb-list-container">
                <AnimatePresence mode="wait">
                  {!selectedFolder ? (
                    <motion.div
                      key="folders"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="kb-folders-view"
                    >
                      <div className="kb-folder-grid">
                        {folders.map((folder) => (
                          <button
                            key={folder.id}
                            className="kb-folder-card"
                            onClick={() => setSelectedFolder(folder.id)}
                          >
                            <div className="folder-icon-wrapper" style={{ color: folder.color }}>
                              <folder.icon size={28} />
                            </div>
                            <div className="folder-info">
                              <span className="folder-name">{folder.name}</span>
                              <span className="folder-count">{getFileCount(folder.id)} files</span>
                            </div>
                            <ChevronRight size={18} className="folder-arrow" />
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="files"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="kb-files-view"
                    >
                      <div className="kb-breadcrumb">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
                          <button className="back-btn" onClick={() => setSelectedFolder(null)} style={{ flexShrink: 0 }}>
                            <ChevronLeft size={16} />
                            <span>All Folders</span>
                          </button>
                          <span className="breadcrumb-sep" style={{ flexShrink: 0 }}>/</span>
                          <span className="breadcrumb-current" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {folders.find(f => f.id === selectedFolder)?.name}
                          </span>
                        </div>

                        <div className="kb-search-container" style={{ flexShrink: 0 }}>
                          <Search size={14} className="search-icon" />
                          <input
                            type="text"
                            placeholder="Search files..."
                            value={kbSearch}
                            onChange={(e) => setKBSearch(e.target.value)}
                            className="kb-search-input"
                          />
                        </div>
                      </div>

                      <div className="kb-list-header">
                        <span>Name</span>
                        <span style={{ textAlign: 'center' }}>Status</span>
                        <span style={{ textAlign: 'center' }}>Weight</span>
                        <span style={{ textAlign: 'right' }}>Action</span>
                      </div>
                      <div className="kb-scroll-area">
                        {kbStatus?.inventory
                          .filter(item => item.type === selectedFolder)
                          .filter(item => item.name.toLowerCase().includes(kbSearch.toLowerCase()))
                          .map((item) => (
                            <div key={item.id} className="kb-row">
                              <div className="kb-file-info">
                                {item.type === 'pdf' && <FileText size={18} color="#ef4444" />}
                                {item.type === 'csv' && <BarChart size={18} color="#10b981" />}
                                {item.type === 'audio' && <Headphones size={18} color="#8b5cf6" />}
                                {item.type === 'txt' && <MessageSquare size={18} color="#f59e0b" />}
                                <div className="kb-file-details">
                                  <div className="kb-file-name">{item.name}</div>
                                  <div className="kb-file-meta">{item.size}</div>
                                </div>
                              </div>
                              <div style={{ textAlign: 'center' }}>
                                <span className={`kb-status-tag ${item.status}`}>
                                  {item.status}
                                </span>
                              </div>
                              <div className="kb-vectors">
                                {item.vectors > 0 ? `${item.vectors} v` : '--'}
                              </div>
                              <div className="kb-actions">
                                <button
                                  className="kb-delete-btn"
                                  title="Purge file"
                                  onClick={() => handleDeleteFile(item.full_path)}
                                >
                                  <Trash2 size={16} />
                                </button>
                              </div>
                            </div>
                          ))}
                        {kbStatus && kbStatus.inventory.filter(f => f.type === selectedFolder).length === 0 && (
                          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '14px' }}>
                            No files found in this category.
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>


      <main className="main-content" style={{ display: isLoggedIn ? 'flex' : 'none' }}>
        {/* 1. HEADER: Always visible for all roles */}
        <header className="top-header">
          <div className="header-left">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="icon-btn"
            >
              <motion.div animate={{ rotate: isSidebarOpen ? 0 : 180 }}>
                <ChevronLeft size={20} />
              </motion.div>
            </button>
            <div className="header-title">Academic AI</div>
          </div>

          <div className="header-right">
            {/* DEMO TOOL: Dropdown to switch roles during your presentation */}
            {/* <select
            value={userRole}
            onChange={(e) => setUserRole(e.target.value as Role)}
            className="role-selector"
            style={{ background: 'var(--bg-glass)', color: 'var(--text-primary)', border: '1px solid var(--border-glass)', borderRadius: '6px', padding: '2px 8px', fontSize: '12px', marginRight: '10px' }}
          >
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
            <option value="admin">Admin</option>
          </select> */}

            <div className="status-badge">
              <div className="status-dot" />
              Gemini 2.5 Flash
            </div>
            <button onClick={toggleTheme} className="icon-btn">
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>
          </div>
        </header>

        {/* 2. CONDITIONAL CONTENT: Admin Dashboard vs. Chat Interface */}
        {userRole === 'admin' ? (
          /* --- ADMIN VIEW: Dashboard instead of Chat --- */
          <div className="admin-view-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>

            {/* /* ADMIN VIEW: Inside your conditional check in <main>  */}
            <div className="admin-card" style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-glass)', padding: '32px', borderRadius: '24px', textAlign: 'center', maxWidth: '500px' }}>
              <Database size={48} className="text-[var(--accent)] mb-4 mx-auto" />
              <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '12px' }}>Admin Control Panel</h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
                Welcome, Administrator. Use the Sidebar to manage the Knowledge Base,
                upload new syllabi, or purge existing vector data.
              </p>

              {/* --- NEW DESIGN FOR THE BUTTON --- */}
              {/* --- PROFESSIONAL ADMIN BUTTON --- */}
              <button
                onClick={() => setIsKBOpen(true)}
                className="admin-action-btn"
                style={{
                  marginTop: '20px',
                  padding: '14px 28px',         /* Added heavy padding to all sides */
                  borderRadius: '50px',        /* Makes it a sleek pill shape */
                  background: 'var(--accent)',  /* BIT Gold/Yellow */
                  color: '#000',               /* Black text for contrast */
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '14px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',                 /* Space between icon and text */
                  margin: '0 auto',            /* Centers it in the card */
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 15px rgba(0,0,0,0.3)'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = 'scale(1.05)';
                  e.currentTarget.style.opacity = '0.9';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.opacity = '1';
                }}
              >
                <Database size={18} />
                Open Knowledge Manager
              </button>
            </div>
          </div>
        ) : (
          /* --- STUDENT & TEACHER VIEW: Standard Chat --- */
          <div className="chat-container">
            <div className="chat-scroll-area" ref={scrollRef}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
                <AnimatePresence initial={false}>
                  {messages.map((msg) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`message-wrapper ${msg.role}`}
                    >
                      <div className={`avatar ${msg.role}`}>
                        {msg.role === 'user' ? 'U' : 'T'}
                      </div>

                      <div className="message-content">
                        <div className="bubble">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              code: (props) => <CodeBlock {...props} theme={theme} />,
                              ul: ({ children }) => <ul className="markdown-list">{children}</ul>,
                              ol: ({ children }) => <ol className="markdown-list">{children}</ol>,
                              table: ({ children }) => (
                                <div className="table-wrapper">
                                  <table className="markdown-table">{children}</table>
                                </div>
                              ),
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>

                        {msg?.metadata?.source && (
                          <div className="metadata-container">
                            <div className="metadata">
                              <div className="doc-tag">
                                {msg.metadata.source.toLowerCase().endsWith('.pdf') && <FileText size={12} />}
                                <span>{msg.metadata.source}</span>
                              </div>
                              {msg.metadata.score != null && (
                                <>
                                  <span>•</span>
                                  <span>Confidence {(msg.metadata.score * 100).toFixed(1)}%</span>
                                </>
                              )}
                            </div>

                            <div className="mt-4">
                              <a
                                /* We extract just the filename from the full path to send to our new route */
                                href={`http://localhost:8000/download/${msg.metadata.source.split('\\').pop()}`}
                                className="bg-[var(--accent)] p-2 rounded-lg text-sm flex items-center gap-2 transition-all hover:opacity-90 w-fit"
                                target="_blank"
                                rel="noopener noreferrer"
                                download // This forces the browser to download the file
                              >
                                <Download size={14} />
                                Download Official {msg.metadata.source.split('\\').pop()}
                              </a>
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}

                  {isLoading && (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="message-wrapper bot"
                    >
                      <div className="avatar bot">T</div>
                      <div className="message-content">
                        <div className="bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Loader2 size={18} className="animate-spin text-[var(--accent)]" />
                          <span>Analysing documents...</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* 3. INPUT AREA: Only visible for Students/Teachers */}
            <div className="input-area">
              <div className="input-container">
                <button
                  className="action-btn"
                  title="Upload"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Paperclip size={20} />
                </button>
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  style={{ display: 'none' }}
                  onChange={handleFileUpload}
                />
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInput}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Message Academia RAG..."
                  className="textarea"
                  rows={1}
                  disabled={isLoading}
                />
                <button className="action-btn">
                  <Mic size={20} />
                </button>
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className={`send-btn ${input.trim() && !isLoading ? 'active' : ''}`}
                >
                  {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                </button>
              </div>
              <p style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '12px' }}>
                Bhilai Institute of Technology RAG System.
              </p>
            </div>
          </div>
        )}
      </main>


      {/* Upload Status Panel - Drive Style */}
      <AnimatePresence>
        {isUploadPanelOpen && (
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            className={`upload-panel ${isUploadPanelMinimized ? 'minimized' : ''}`}
          >
            <div className="upload-header" onClick={() => setIsUploadStatusMinimized(!isUploadPanelMinimized)}>
              <span className="upload-title">
                {uploadQueue.filter(t => t.status !== 'completed').length > 0
                  ? `Processing ${uploadQueue.filter(t => t.status !== 'completed').length} files...`
                  : 'Uploads complete'}
              </span>
              <div className="upload-controls">
                <button onClick={(e) => { e.stopPropagation(); setIsUploadStatusMinimized(!isUploadPanelMinimized); }}>
                  {isUploadPanelMinimized ? <ChevronRight size={18} style={{ transform: 'rotate(-90deg)' }} /> : <ChevronRight size={18} style={{ transform: 'rotate(90deg)' }} />}
                </button>
                <button onClick={(e) => { e.stopPropagation(); setIsUploadStatusVisible(false); }}>
                  <X size={18} />
                </button>
              </div>
            </div>

            {!isUploadPanelMinimized && (
              <div className="upload-body">
                {uploadQueue.map(task => (
                  <div key={task.id} className="upload-item">
                    <div className="upload-item-info">
                      {task.status === 'uploading' || task.status === 'indexing'
                        ? <Loader2 size={16} className="animate-spin text-accent" />
                        : task.status === 'completed'
                          ? <Check size={16} className="text-[#10b981]" />
                          : <X size={16} className="text-[#ef4444]" />
                      }
                      <span className="upload-file-name">{task.name}</span>
                    </div>
                    <div className="upload-item-status">
                      {task.status === 'uploading' ? `${task.progress}%` : task.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
