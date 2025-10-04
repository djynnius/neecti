import React, { createContext, useContext, useEffect, useState } from 'react';
import io from 'socket.io-client';
import { useAuth } from './AuthContext';

// Configure Socket.IO URL based on environment
const SOCKET_URL = process.env.REACT_APP_API_URL ||
  (process.env.NODE_ENV === 'production' ? 'http://localhost:5000' : 'http://localhost:5000');

const SocketContext = createContext();

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      // Initialize socket connection
      const newSocket = io(SOCKET_URL, {
        withCredentials: true,
        transports: ['websocket', 'polling']
      });

      newSocket.on('connect', () => {
        console.log('Connected to server');
        setConnected(true);
      });

      newSocket.on('disconnect', () => {
        console.log('Disconnected from server');
        setConnected(false);
      });

      newSocket.on('connected', (data) => {
        console.log('Socket connected:', data);
      });

      newSocket.on('user_online', (data) => {
        setOnlineUsers(prev => new Set([...prev, data.user_id]));
      });

      newSocket.on('user_offline', (data) => {
        setOnlineUsers(prev => {
          const newSet = new Set(prev);
          newSet.delete(data.user_id);
          return newSet;
        });
      });

      newSocket.on('new_post', (data) => {
        // Handle new post in timeline
        window.dispatchEvent(new CustomEvent('newPost', { detail: data.post }));
      });

      newSocket.on('post_updated', (data) => {
        // Handle post updates (likes, shares, etc.)
        window.dispatchEvent(new CustomEvent('postUpdated', { detail: data.post }));
      });

      newSocket.on('post_deleted', (data) => {
        // Handle post deletion
        window.dispatchEvent(new CustomEvent('postDeleted', { detail: data.post_id }));
      });

      newSocket.on('new_notification', (data) => {
        // Handle new notification
        window.dispatchEvent(new CustomEvent('newNotification', { detail: data.notification }));
      });

      newSocket.on('new_message', (data) => {
        // Handle new message
        window.dispatchEvent(new CustomEvent('newMessage', { detail: data }));
      });

      newSocket.on('message_notification', (data) => {
        // Handle message notification
        window.dispatchEvent(new CustomEvent('messageNotification', { detail: data }));
      });

      newSocket.on('user_typing', (data) => {
        // Handle typing indicator
        window.dispatchEvent(new CustomEvent('userTyping', { detail: data }));
      });

      setSocket(newSocket);

      return () => {
        newSocket.close();
        setSocket(null);
        setConnected(false);
      };
    } else {
      // Disconnect socket when user logs out
      if (socket) {
        socket.close();
        setSocket(null);
        setConnected(false);
      }
    }
  }, [user]);

  const joinConversation = (userId) => {
    if (socket) {
      socket.emit('join_conversation', { user_id: userId });
    }
  };

  const leaveConversation = (userId) => {
    if (socket) {
      socket.emit('leave_conversation', { user_id: userId });
    }
  };

  const sendMessage = (recipientId, content) => {
    if (socket) {
      socket.emit('send_message', {
        recipient_id: recipientId,
        content: content
      });
    }
  };

  const startTyping = (userId) => {
    if (socket) {
      socket.emit('typing_start', { user_id: userId });
    }
  };

  const stopTyping = (userId) => {
    if (socket) {
      socket.emit('typing_stop', { user_id: userId });
    }
  };

  const markMessagesRead = (conversationId) => {
    if (socket) {
      socket.emit('mark_messages_read', { conversation_id: conversationId });
    }
  };

  const isUserOnline = (userId) => {
    return onlineUsers.has(userId);
  };

  const value = {
    socket,
    connected,
    onlineUsers,
    joinConversation,
    leaveConversation,
    sendMessage,
    startTyping,
    stopTyping,
    markMessagesRead,
    isUserOnline
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
};
