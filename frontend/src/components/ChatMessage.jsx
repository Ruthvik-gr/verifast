import React from 'react';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import { FiUser, FiCpu, FiExternalLink, FiInfo, FiMessageSquare } from 'react-icons/fi';
import { motion } from 'framer-motion';

function ChatMessage({ message }) {
  const { role, content, timestamp, sources } = message;
  const isUser = role === 'user';
  const isSystem = role === 'system';
  
  const formattedTime = timestamp ? format(new Date(timestamp), 'h:mm a') : '';
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`flex max-w-[85%] md:max-w-[75%] ${isSystem ? 'w-full mx-auto max-w-2xl' : ''}`}>
        {!isUser && !isSystem && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="flex-shrink-0 mr-3 self-end"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary-600 to-secondary-600 flex items-center justify-center text-white shadow-soft">
              <FiMessageSquare className="w-5 h-5" />
            </div>
          </motion.div>
        )}
        
        <motion.div 
          whileHover={{ scale: 1.01 }}
          className={`
            rounded-xl p-4 shadow-soft
            ${isUser ? 'bg-gradient-to-r from-primary-600 to-secondary-600 text-white' : ''}
            ${isSystem ? 'bg-amber-50 border border-amber-100 text-amber-800 w-full text-center' : ''}
            ${!isUser && !isSystem ? 'bg-white border border-gray-100' : ''}
          `}
        >
          <div className="flex justify-between items-start mb-1">
            <div className="font-medium text-sm">
              {isUser ? 'You' : isSystem ? 'System' : 'News Assistant'}
            </div>
            {timestamp && <div className="text-xs opacity-70">{formattedTime}</div>}
          </div>
          
          <div className="text-sm break-words">
            {isUser ? (
              <p>{content}</p>
            ) : (
              <ReactMarkdown className="prose prose-sm max-w-none">
                {content}
              </ReactMarkdown>
            )}
          </div>
          
          {sources && sources.length > 0 && (
            <div className="mt-3 pt-2 border-t border-gray-200">
              <div className="flex items-center text-xs text-primary-600 mb-1">
                <FiInfo className="mr-1" /> Sources:
              </div>
              <ul className="space-y-1">
                {sources.map((source, index) => (
                  <li key={index} className="text-xs flex items-start">
                    <FiExternalLink className="mr-1 flex-shrink-0 mt-0.5" />
                    <a 
                      href={source.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-800 hover:underline truncate"
                    >
                      {source.title || source.url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
        
        {isUser && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="flex-shrink-0 ml-3 self-end"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-secondary-500 to-primary-500 flex items-center justify-center text-white shadow-soft">
              <FiUser className="w-5 h-5" />
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

export default ChatMessage;
