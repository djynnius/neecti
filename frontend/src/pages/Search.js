import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../utils/api';
import { renderPostContent } from '../utils/postUtils';
import LoadingSpinner from '../components/Common/LoadingSpinner';

const Search = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [searchType, setSearchType] = useState('all');
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q, searchType);
    }
  }, [searchParams]);

  const performSearch = async (searchQuery, type = 'all') => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await api.get('/api/search', {
        params: { q: searchQuery, type }
      });
      setResults(response.data.results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query });
      performSearch(query, searchType);
    }
  };

  const getSuggestions = async (searchQuery) => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await api.get('/api/search/suggestions', {
        params: { q: searchQuery }
      });
      setSuggestions(response.data.suggestions);
    } catch (error) {
      console.error('Suggestions error:', error);
    }
  };

  const handleQueryChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    getSuggestions(value);
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Search Form */}
      <div className="card mb-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={handleQueryChange}
              placeholder="Search users, posts, hashtags..."
              className="input-field w-full pl-10"
            />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            {/* Search Suggestions */}
            {suggestions.length > 0 && (
              <div className="absolute z-10 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg mt-1 shadow-lg">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setQuery(suggestion.text);
                      setSuggestions([]);
                      setSearchParams({ q: suggestion.text });
                      performSearch(suggestion.text, searchType);
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                  >
                    <span className="text-sm text-gray-500">{suggestion.type}</span>
                    <span>{suggestion.display}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex space-x-4">
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              className="input-field"
            >
              <option value="all">All</option>
              <option value="users">Users</option>
              <option value="posts">Posts</option>
              <option value="hashtags">Hashtags</option>
            </select>
            <button type="submit" className="btn-primary">
              Search
            </button>
          </div>
        </form>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-8">
          <LoadingSpinner size="large" />
        </div>
      )}

      {/* Search Results */}
      {!loading && Object.keys(results).length > 0 && (
        <div className="space-y-6">
          {/* Users */}
          {results.users && results.users.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Users</h2>
              <div className="space-y-3">
                {results.users.map((user) => (
                  <UserCard key={user.id} user={user} />
                ))}
              </div>
            </div>
          )}

          {/* Posts */}
          {results.posts && results.posts.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Posts</h2>
              <div className="space-y-4">
                {results.posts.map((post) => (
                  <PostCard key={post.id} post={post} />
                ))}
              </div>
            </div>
          )}

          {/* Hashtags */}
          {results.hashtags && results.hashtags.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Hashtags</h2>
              <div className="space-y-2">
                {results.hashtags.map((hashtag, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <Link
                      to={`/search?q=${encodeURIComponent('#' + hashtag.hashtag)}`}
                      className="text-primary-blue hover:underline"
                    >
                      #{hashtag.hashtag}
                    </Link>
                    <span className="text-sm text-gray-500">
                      {hashtag.count} posts
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Results */}
      {!loading && Object.keys(results).length > 0 &&
       (!results.users || results.users.length === 0) &&
       (!results.posts || results.posts.length === 0) &&
       (!results.hashtags || results.hashtags.length === 0) && (
        <div className="card text-center py-8">
          <p className="text-gray-500">No results found for "{query}"</p>
        </div>
      )}
    </div>
  );
};

const UserCard = ({ user }) => {
  const [following, setFollowing] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleFollow = async () => {
    setLoading(true);
    try {
      const endpoint = following ? 'unfollow' : 'follow';
      await api.post(`/users/@${user.handle}/${endpoint}`);
      setFollowing(!following);
    } catch (error) {
      console.error('Follow error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
      <div className="flex items-center space-x-3">
        <div className="w-12 h-12 bg-primary-blue rounded-full flex items-center justify-center text-white font-medium">
          {user.first_name[0]}{user.last_name[0]}
        </div>
        <div>
          <Link
            to={`/profile/${user.handle}`}
            className="font-semibold text-gray-900 dark:text-white hover:text-primary-blue"
          >
            {user.full_name}
          </Link>
          <p className="text-sm text-gray-500">@{user.handle}</p>
          {user.bio && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {user.bio}
            </p>
          )}
        </div>
      </div>
      <button
        onClick={handleFollow}
        disabled={loading}
        className={`px-4 py-2 rounded-lg text-sm font-medium ${
          following
            ? 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            : 'bg-primary-blue text-white hover:bg-blue-700'
        } disabled:opacity-50`}
      >
        {loading ? <LoadingSpinner size="small" /> : following ? 'Unfollow' : 'Follow'}
      </button>
    </div>
  );
};

const PostCard = ({ post }) => {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-2">
        <Link
          to={`/profile/${post.author?.handle}`}
          className="font-semibold text-gray-900 dark:text-white hover:text-primary-blue"
        >
          {post.author?.full_name}
        </Link>
        <span className="text-gray-500">@{post.author?.handle}</span>
      </div>
      <div className="text-gray-900 dark:text-white whitespace-pre-wrap">
        {renderPostContent(post.content)}
      </div>
      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
        <span>{post.likes_count} likes</span>
        <span>{post.replies_count} replies</span>
        <span>{post.shares_count} shares</span>
      </div>
    </div>
  );
};

export default Search;
