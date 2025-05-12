import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { FiSend, FiRefreshCw, FiInfo, FiAlertCircle, FiMessageSquare, FiMenu, FiX } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import ChatMessage from './components/ChatMessage.jsx';
import config from './config';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [sessionId, setSessionId] = useState('');
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [showWelcome, setShowWelcome] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const endOfMessagesRef = useRef(null);
  const inputRef = useRef(null);
  const currentStreamingMessage = useRef('');

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Focus input when chat is ready
  useEffect(() => {
    if (!initializing && connected && inputRef.current) {
      inputRef.current.focus();
    }
  }, [initializing, connected]);
  
  const createNewSession = async () => {
    setInitializing(true);
    setError(null);
    
    try {
      const response = await axios.post(`${config.backendUrl}/api/session`);
      setSessionId(response.data.session_id);
      
      // Initialize WebSocket connection
      initializeWebSocket(response.data.session_id);
    } catch (err) {
      console.error('Error creating session:', err);
      setError('Failed to create chat session. Please try again.');
      setInitializing(false);
    }
  };
  
  const initializeWebSocket = (sid) => {
    // Use the WebSocket configuration from config.js
    const wsUrl = `${config.wsProtocol}//${config.wsUrl}/ws/${sid}`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      setInitializing(false);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'stream') {
        // Accumulate the token in our ref
        currentStreamingMessage.current += data.content;
        
        // Update the messages array
        setMessages(prevMessages => {
          const newMessages = [...prevMessages];
          const lastIndex = newMessages.length - 1;
          
          // If the last message is from the assistant, update it
          if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
            newMessages[lastIndex] = {
              ...newMessages[lastIndex],
              content: currentStreamingMessage.current
            };
          } else {
            // Otherwise create a new assistant message
            newMessages.push({
              role: 'assistant',
              content: currentStreamingMessage.current,
              timestamp: new Date().toISOString(),
              sources: []
            });
          }
          
          return newMessages;
        });
      } else if (data.type === 'end') {
        // End of stream
        setLoading(false);
        
        // Make sure the final message is preserved in the messages array
        // We don't reset currentStreamingMessage.current here to ensure the message stays
        
        setTimeout(scrollToBottom, 100);
      } else if (data.type === 'error') {
        // Handle error
        setError(data.content);
        setLoading(false);
      } else if (data.type === 'status') {
        // Handle status updates
        console.log('Status update:', data.content);
      } else if (data.type === 'bot_message') {
        // Handle complete bot message (for backward compatibility)
        const botMessage = {
          role: 'assistant',
          content: data.message,
          timestamp: data.timestamp,
          sources: data.sources || []
        };
        
        setMessages((prevMessages) => [...prevMessages, botMessage]);
        setLoading(false);
        
        // Scroll to bottom after message is rendered
        setTimeout(scrollToBottom, 100);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      
      if (!initializing) {
        setError('Connection lost. Please refresh the page to reconnect.');
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error. Please refresh the page to try again.');
      setConnected(false);
      setInitializing(false);
    };
    
    setSocket(ws);
  };
  
  // Initialize session on component mount
  useEffect(() => {
    createNewSession();
    
    // Cleanup WebSocket on unmount
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const sendMessage = () => {
    if (!input.trim() || !connected || initializing) return;
    
    // Create user message
    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
    
    // Save the current messages to ensure we don't lose them
    const currentMessages = [...messages, userMessage];
    
    // Add user message to the chat
    setMessages(currentMessages);
    setShowWelcome(false);
    
    // Reset the streaming message ref for the new message
    currentStreamingMessage.current = '';
    
    // Send message to server
    socket.send(JSON.stringify({
      message: input,
      timestamp: new Date().toISOString()
    }));
    
    // Clear input and set loading
    setInput('');
    setLoading(true);
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  const refreshArticles = async () => {
    if (!connected || initializing) return;
    
    setLoading(true);
    
    try {
      await axios.post(`${config.backendUrl}/api/refresh`);
      
      // Add system message
      const systemMessage = {
        role: 'system',
        content: 'News articles have been refreshed. You can now ask about the latest news.',
        timestamp: new Date().toISOString()
      };
      
      setMessages((prevMessages) => [...prevMessages, systemMessage]);
    } catch (err) {
      console.error('Error refreshing articles:', err);
      setError('Failed to refresh news articles. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const clearChat = () => {
    if (sessionId && connected) {
      axios.delete(`/api/sessions/${sessionId}`)
        .then(() => {
          setMessages([]);
          setShowWelcome(true);
        })
        .catch((err) => {
          console.error('Error clearing chat:', err);
          setError('Failed to clear chat history. Please try again.');
        });
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-custom">
      {/* Header */}
      <header className="header">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center space-x-2"
          >
            <div className="logo">
              <FiMessageSquare className="w-5 h-5" />
            </div>
            <h1 className="title">
              News RAG Chatbot
            </h1>
          </motion.div>
          
          {/* Desktop menu */}
          <div className="hidden md:flex items-center space-x-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="flex items-center"
            >
              <span className={`inline-block w-2 h-2 rounded-full mr-1.5 ${connected ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="text-sm text-gray-600">{connected ? 'Connected' : 'Disconnected'}</span>
            </motion.div>
            
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={refreshArticles}
              disabled={initializing || !connected}
              className="btn btn-primary"
            >
              <FiRefreshCw className="w-4 h-4 mr-1.5" />
              <span>Refresh News</span>
            </motion.button>
            
            <motion.button 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={clearChat}
              disabled={initializing || !connected || messages.length === 0}
              className="flex items-center text-sm text-gray-600 hover:text-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors px-3 py-1.5 rounded-md hover:bg-gray-100"
            >
              <FiX className="w-4 h-4 mr-1.5" />
              <span>Clear Chat</span>
            </motion.button>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            >
              {mobileMenuOpen ? <FiX className="w-5 h-5" /> : <FiMenu className="w-5 h-5" />}
            </button>
          </div>
        </div>
        
        {/* Mobile menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden mt-2 pt-2 border-t border-gray-200"
            >
              <div className="flex flex-col space-y-2 px-1">
                <div className="flex items-center py-2">
                  <span className={`inline-block w-2 h-2 rounded-full mr-1.5 ${connected ? 'bg-green-500' : 'bg-red-500'}`}></span>
                  <span className="text-sm text-gray-600">{connected ? 'Connected' : 'Disconnected'}</span>
                </div>
                
                <button 
                  onClick={refreshArticles}
                  disabled={initializing || !connected}
                  className="flex items-center text-sm text-primary-600 hover:text-primary-800 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors py-2"
                >
                  <FiRefreshCw className="w-4 h-4 mr-1.5" />
                  <span>Refresh News</span>
                </button>
                
                <button 
                  onClick={clearChat}
                  disabled={initializing || !connected || messages.length === 0}
                  className="flex items-center text-sm text-gray-600 hover:text-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors py-2"
                >
                  <FiX className="w-4 h-4 mr-1.5" />
                  <span>Clear Chat</span>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <main className="flex-1 overflow-hidden flex flex-col">
        {/* Chat messages container */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          <AnimatePresence>
            {initializing ? (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center h-full"
              >
                <div className="text-center">
                  <div className="relative w-16 h-16 mx-auto mb-4">
                    <div className="absolute top-0 left-0 w-full h-full border-4 border-primary-200 rounded-full animate-ping opacity-75"></div>
                    <div className="absolute top-0 left-0 w-full h-full border-4 border-t-primary-600 border-primary-200 rounded-full animate-spin"></div>
                  </div>
                  <p className="text-gray-600 font-medium">Initializing chat...</p>
                </div>
              </motion.div>
            ) : messages.length === 0 && showWelcome ? (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="flex items-center justify-center h-full"
              >
                <div className="text-center max-w-xl mx-auto bg-white rounded-xl shadow-soft border border-primary-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-primary-600 to-secondary-600 py-4 px-6">
                    <h2 className="text-2xl font-bold text-white">Welcome to the News RAG Chatbot!</h2>
                  </div>
                  <div className="p-6">
                    <p className="text-gray-600 mb-6">
                      Ask me anything about recent news and I'll try to help you with relevant information.
                    </p>
                    <div className="bg-primary-50 p-5 rounded-lg border border-primary-100">
                      <h3 className="font-semibold text-primary-800 mb-3 flex items-center">
                        <FiInfo className="mr-2" /> Try asking:
                      </h3>
                      <ul className="text-primary-700 space-y-2 text-left">
                        {[
                          "What's happening in India and Pakistan?",
                          "Tell me about Operation Sindoor",
                          "What are the latest developments in Kashmir?"
                        ].map((suggestion, index) => (
                          <motion.li 
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 + index * 0.1 }}
                            className="flex items-start"
                          >
                            <span className="text-primary-400 mr-2">•</span>
                            <button 
                              onClick={() => {
                                setInput(suggestion);
                                if (inputRef.current) inputRef.current.focus();
                              }}
                              className="text-left hover:text-primary-900 hover:underline transition-colors"
                            >
                              {suggestion}
                            </button>
                          </motion.li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="max-w-4xl w-full mx-auto">
                <AnimatePresence>
                  {messages.map((msg, index) => (
                    <ChatMessage key={index} message={msg} />
                  ))}
                </AnimatePresence>
                
                {loading && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-center space-x-3 p-4 bg-white rounded-lg shadow-soft max-w-[80%] ml-12 mt-4"
                  >
                    <div className="flex space-x-1">
                      <div className="loading-dot loading-dot-1"></div>
                      <div className="loading-dot loading-dot-2"></div>
                      <div className="loading-dot loading-dot-3"></div>
                    </div>
                    <span className="text-sm text-gray-500">Thinking...</span>
                  </motion.div>
                )}
                <div ref={endOfMessagesRef} />
              </div>
            )}
          </AnimatePresence>
        </div>
        
        {/* Input area */}
        <div className="input-container">
          <div className="max-w-4xl mx-auto">
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                disabled={initializing || !connected}
                className="input-field"
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={sendMessage}
                disabled={!input.trim() || initializing || !connected}
                className="send-button"
              >
                <FiSend className="w-5 h-5" />
              </motion.button>
            </div>
            
            <AnimatePresence>
              {error && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-3 flex items-center text-red-500 text-sm bg-red-50 p-2 rounded-md border border-red-100"
                >
                  <FiAlertCircle className="w-4 h-4 mr-2" />
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
