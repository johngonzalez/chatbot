import React, { useEffect, useRef } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const ChatMessages = ({ messages, isFetching }) => {
const messageContainerRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    if (messageContainerRef.current && messageContainerRef.current.lastChild) {
      messageContainerRef.current.lastChild.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const filteredMessages = messages.filter(
    (message) =>
      !(message.sender === 'system' | (message.sender !== 'user' && message.text.length === 0)),
  );

  const formatMessage = (text) => {
    const codeBlockRegex = /(```[\w]*[\s\S]+?```)/g;
    const parts = text.split(codeBlockRegex);
  
    return parts.map((part, index) => {
      if (codeBlockRegex.test(part)) {
        const languageRegex = /```(\w*)\n/;
        const languageMatch = part.match(languageRegex);
        const language = languageMatch && languageMatch[1] ? languageMatch[1] : '';
  
        return (
          <SyntaxHighlighter
            key={index}
            language={language}
            style={oneDark}
            customStyle={{ backgroundColor: '#2d2d2d', borderRadius: '0.375rem', padding: '1rem' }}
          >
            {part.replace(languageRegex, '').replace(/```$/, '')}
          </SyntaxHighlighter>
        );
      } else {
        return (
          <span key={index}>
            {part}
          </span>
        );
      }
    });
  };

  return (
    <div className="w-full md:w-1/2 md:max-w-xl" ref={messageContainerRef}>
      {filteredMessages.map((message, index) => (
        <div
          key={index}
          className={`mb-4 p-3 text-lg rounded-lg shadow-md whitespace-pre-wrap border-indigo-500
          ${message.sender === 'user' ? 'bg-gray-100 text-gray-800' : 'bg-indigo-200 text-gray-800'}
          ${((messages.length > 2 && index === messages.length - 2) ||
            (messages.length == 2 && index === 1)) &&
            isFetching ? 'animate-pulse' : ''}
          `}
        >
          {formatMessage(message.text)}
        </div>
      ))}
    </div>
  );
};

export default ChatMessages;