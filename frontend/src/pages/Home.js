import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../utils/api';
import { useSocket } from '../contexts/SocketContext';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { renderPostContent } from '../utils/postUtils';
import LoadingSpinner from '../components/Common/LoadingSpinner';



const Home = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newPost, setNewPost] = useState('');
  const [posting, setPosting] = useState(false);
  const [newPostsCount, setNewPostsCount] = useState(0);
  const { connected } = useSocket();
  const { user } = useAuth();
  const { t, tp, formatRelativeTime } = useLanguage();

  const getCurrentUserId = () => user?.id;

  useEffect(() => {
    fetchTimeline();
  }, []);

  // Listen for real-time events
  useEffect(() => {
    const handleNewPost = (event) => {
      const newPost = event.detail;
      setPosts(prevPosts => [newPost, ...prevPosts]);

      // Show notification for new posts (except own posts)
      if (newPost.user_id !== getCurrentUserId()) {
        setNewPostsCount(prev => prev + 1);

        // Auto-clear notification after 5 seconds
        setTimeout(() => {
          setNewPostsCount(prev => Math.max(0, prev - 1));
        }, 5000);
      }
    };

    const handlePostUpdate = (event) => {
      const updatedPost = event.detail;
      setPosts(prevPosts =>
        prevPosts.map(post =>
          post.id === updatedPost.id ? { ...post, ...updatedPost } : post
        )
      );
    };

    const handlePostDeleted = (event) => {
      const deletedPostId = event.detail;
      setPosts(prevPosts => prevPosts.filter(post => post.id !== deletedPostId));
    };

    // Add event listeners
    window.addEventListener('newPost', handleNewPost);
    window.addEventListener('postUpdated', handlePostUpdate);
    window.addEventListener('postDeleted', handlePostDeleted);

    // Cleanup
    return () => {
      window.removeEventListener('newPost', handleNewPost);
      window.removeEventListener('postUpdated', handlePostUpdate);
      window.removeEventListener('postDeleted', handlePostDeleted);
    };
  }, []);

  const fetchTimeline = async () => {
    try {
      const response = await api.get('/posts/timeline');
      setPosts(response.data.posts);
    } catch (error) {
      console.error('Error fetching timeline:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!newPost.trim()) return;

    setPosting(true);
    try {
      const response = await api.post('/posts/', {
        content: newPost
      });
      setPosts([response.data.post, ...posts]);
      setNewPost('');
    } catch (error) {
      console.error('Error creating post:', error);
    } finally {
      setPosting(false);
    }
  };

  const handleLike = async (postId) => {
    // Optimistic update
    setPosts(prevPosts =>
      prevPosts.map(post =>
        post.id === postId
          ? {
              ...post,
              likes_count: post.likes_count + (post.is_liked ? -1 : 1),
              is_liked: !post.is_liked
            }
          : post
      )
    );

    try {
      const response = await api.post(`/posts/${postId}/like`);
      // The real-time update will handle the final state via socket
    } catch (error) {
      console.error('Error liking post:', error);
      // Revert optimistic update on error
      setPosts(prevPosts =>
        prevPosts.map(post =>
          post.id === postId
            ? {
                ...post,
                likes_count: post.likes_count + (post.is_liked ? 1 : -1),
                is_liked: !post.is_liked
              }
            : post
        )
      );
    }
  };

  const handleDelete = async (postId) => {
    try {
      await api.delete(`/posts/${postId}`);
      // Remove the post from the local state
      setPosts(prevPosts => prevPosts.filter(post => post.id !== postId));
    } catch (error) {
      console.error('Error deleting post:', error);
      // You could add a toast notification here for error feedback
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Connection Status */}
      {connected && (
        <div className="mb-4 p-2 bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-green-700 dark:text-green-300">
              {t('home.connected')}
            </span>
          </div>
        </div>
      )}

      {/* New Posts Notification */}
      {newPostsCount > 0 && (
        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-blue-700 dark:text-blue-300">
                {newPostsCount} {tp('home.new_posts', newPostsCount)} {t('home.from_following')}
              </span>
            </div>
            <button
              onClick={() => setNewPostsCount(0)}
              className="text-blue-500 hover:text-blue-700 text-sm"
            >
              {t('home.dismiss')}
            </button>
          </div>
        </div>
      )}

      {/* Create Post */}
      <div className="card mb-6">
        <form onSubmit={handleCreatePost}>
          <textarea
            value={newPost}
            onChange={(e) => setNewPost(e.target.value)}
            placeholder={t('home.whats_happening')}
            className="w-full p-3 border-none resize-none focus:outline-none bg-transparent text-gray-900 dark:text-white placeholder-gray-500"
            rows="3"
            maxLength="250"
          />
          <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <span className="text-sm text-gray-500">
              {newPost.length}/250 {t('home.character_count')}
            </span>
            <button
              type="submit"
              disabled={!newPost.trim() || posting}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {posting ? <LoadingSpinner size="small" /> : t('home.post_button')}
            </button>
          </div>
        </form>
      </div>

      {/* Timeline */}
      <div className="space-y-4">
        {posts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400">
              {t('home.no_posts')}
            </p>
          </div>
        ) : (
          posts.map((post) => (
            <PostCard key={post.id} post={post} onLike={handleLike} onDelete={handleDelete} />
          ))
        )}
      </div>
    </div>
  );
};

const PostCard = ({ post, onLike, onDelete }) => {
  const { t, formatRelativeTime } = useLanguage();
  const { user } = useAuth();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = () => {
    setShowDeleteConfirm(true);
  };

  const confirmDelete = () => {
    onDelete(post.id);
    setShowDeleteConfirm(false);
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  const isOwner = user && post.author && user.id === post.author.id;

  return (
    <div className="post-card">
      <div className="flex space-x-3">
        {/* Avatar */}
        <div className="w-12 h-12 bg-primary-blue rounded-full flex items-center justify-center text-white font-medium">
          {post.author?.first_name?.[0]}{post.author?.last_name?.[0]}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center space-x-2">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {post.author?.full_name}
            </h3>
            <span className="text-gray-500">@{post.author?.handle}</span>
            <span className="text-gray-500">·</span>
            <span className="text-gray-500">{formatRelativeTime(post.created_at)}</span>
          </div>

          {/* Post content */}
          <div className="mt-2">
            <div className="text-gray-900 dark:text-white whitespace-pre-wrap">
              {renderPostContent(post.content)}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-6 mt-4">
            {/* Reply */}
            <button className="flex items-center space-x-2 text-gray-500 hover:text-primary-blue">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span className="text-sm">{post.replies_count}</span>
            </button>

            {/* Like */}
            <button
              onClick={() => onLike(post.id)}
              className={`flex items-center space-x-2 ${post.is_liked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'}`}
              title={t('post.like')}
            >
              <svg className={`w-5 h-5 ${post.is_liked ? 'fill-current' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
              <span className="text-sm">{post.likes_count}</span>
            </button>

            {/* Share */}
            <button
              className="flex items-center space-x-2 text-gray-500 hover:text-green-500"
              title={t('post.share')}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
              </svg>
              <span className="text-sm">{post.shares_count}</span>
            </button>

            {/* Delete (only for post owner) */}
            {isOwner && (
              <button
                onClick={handleDelete}
                className="flex items-center space-x-2 text-gray-500 hover:text-red-500"
                title={t('post.delete')}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-sm mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t('post.delete_confirm_title')}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {t('post.delete_confirm_message')}
            </p>
            <div className="flex space-x-3">
              <button
                onClick={cancelDelete}
                className="flex-1 px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 px-4 py-2 text-white bg-red-600 rounded-lg hover:bg-red-700"
              >
                {t('post.delete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;
