import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../../contexts/LanguageContext';
import LoadingSpinner from '../Common/LoadingSpinner';

const RightSidebar = () => {
  const [trendingHashtags, setTrendingHashtags] = useState([]);
  const [suggestedUsers, setSuggestedUsers] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const { t } = useLanguage();

  useEffect(() => {
    fetchSidebarData();
  }, []);

  const fetchSidebarData = async () => {
    try {
      // Fetch trending hashtags
      const hashtagsResponse = await axios.get('/api/trending/hashtags');
      setTrendingHashtags(hashtagsResponse.data.trending_hashtags || []);

      // Fetch suggested users
      const usersResponse = await axios.get('/users/suggested');
      setSuggestedUsers(usersResponse.data.suggested_users || []);

      // Fetch platform stats
      const statsResponse = await axios.get('/api/stats');
      setStats(statsResponse.data.stats || {});
    } catch (error) {
      console.error('Error fetching sidebar data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFollow = async (userHandle) => {
    try {
      await axios.post(`/users/@${userHandle}/follow`);
      // Remove user from suggestions after following
      setSuggestedUsers(prev => prev.filter(user => user.handle !== userHandle));
    } catch (error) {
      console.error('Error following user:', error);
    }
  };

  if (loading) {
    return (
      <div className="right-sidebar p-4">
        <div className="flex justify-center py-8">
          <LoadingSpinner size="medium" />
        </div>
      </div>
    );
  }

  return (
    <div className="right-sidebar p-6">
      <div className="space-y-8">
        {/* Trending Hashtags */}
        <div className="card-elevated">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-8 h-8 bg-gradient-to-br from-accent-orange to-warning rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
              </svg>
            </div>
            <h3 className="text-heading-4 text-gray-900 dark:text-white">
              {t('sidebar_right.trending_hashtags')}
            </h3>
          </div>
          <div className="space-y-3">
            {trendingHashtags.length > 0 ? (
              trendingHashtags.slice(0, 5).map((hashtag, index) => (
                <div key={index} className="group flex justify-between items-center p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-all duration-300">
                  <Link
                    to={`/search?q=${encodeURIComponent('#' + hashtag.hashtag)}`}
                    className="text-primary-blue hover:text-primary-blue-light font-medium group-hover:scale-105 transition-all duration-300"
                  >
                    #{hashtag.hashtag}
                  </Link>
                  <div className="flex items-center space-x-2">
                    <span className="text-caption bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full">
                      {hashtag.count} {hashtag.count === 1 ? t('sidebar_right.post') : t('sidebar_right.posts')}
                    </span>
                    <div className="w-2 h-2 bg-primary-green rounded-full animate-pulse"></div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-caption text-center py-4">{t('sidebar_right.no_trending')}</p>
            )}
          </div>
        </div>

        {/* Suggested Users */}
        <div className="card-elevated">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-8 h-8 bg-gradient-to-br from-accent-purple to-primary-blue rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            </div>
            <h3 className="text-heading-4 text-gray-900 dark:text-white">
              {t('sidebar_right.who_to_follow')}
            </h3>
          </div>
          <div className="space-y-3">
            {suggestedUsers.length > 0 ? (
              suggestedUsers.slice(0, 3).map((user) => (
                <SuggestedUserCard
                  key={user.id}
                  user={user}
                  onFollow={() => handleFollow(user.handle)}
                />
              ))
            ) : (
              <p className="text-sm text-gray-500">{t('sidebar_right.no_suggestions')}</p>
            )}
          </div>
          {suggestedUsers.length > 3 && (
            <Link
              to="/search?type=users"
              className="block text-center text-primary-blue hover:underline text-sm mt-3"
            >
              {t('sidebar_right.see_more')}
            </Link>
          )}
        </div>

        {/* Platform Stats */}
        <div className="card-elevated">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-green to-success rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-heading-4 text-gray-900 dark:text-white">
              {t('sidebar_right.platform_stats')}
            </h3>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-gradient-subtle rounded-xl">
              <span className="text-body-small text-gray-600 dark:text-gray-400">{t('sidebar_right.total_users')}</span>
              <span className="font-bold text-primary-blue text-lg">{stats.total_users || 0}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gradient-subtle rounded-xl">
              <span className="text-body-small text-gray-600 dark:text-gray-400">{t('sidebar_right.total_posts')}</span>
              <span className="font-bold text-secondary-blue text-lg">{stats.total_posts || 0}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gradient-subtle rounded-xl">
              <span className="text-body-small text-gray-600 dark:text-gray-400">{t('sidebar_right.active_today')}</span>
              <span className="font-bold text-primary-green text-lg">{stats.active_users_today || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const SuggestedUserCard = ({ user, onFollow }) => {
  const [following, setFollowing] = useState(false);
  const [loading, setLoading] = useState(false);
  const { t } = useLanguage();

  const handleFollow = async () => {
    setLoading(true);
    try {
      await onFollow();
      setFollowing(true);
    } catch (error) {
      console.error('Follow error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="group flex items-center justify-between p-4 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-all duration-300">
      <div className="flex items-center space-x-4">
        <div className="w-12 h-12 bg-gradient-to-br from-primary-blue to-secondary-blue rounded-xl flex items-center justify-center text-white text-sm font-medium shadow-lg group-hover:shadow-xl transition-all duration-300">
          {user.first_name?.[0]}{user.last_name?.[0]}
        </div>
        <div>
          <Link
            to={`/profile/${user.handle}`}
            className="font-semibold text-gray-900 dark:text-white hover:text-primary-blue transition-colors duration-300 group-hover:scale-105 inline-block"
          >
            {user.full_name}
          </Link>
          <p className="text-caption">@{user.handle}</p>
        </div>
      </div>
      <button
        onClick={handleFollow}
        disabled={loading || following}
        className={`text-sm px-4 py-2 rounded-xl font-medium transition-all duration-300 ${
          following
            ? 'bg-gray-200 text-gray-600 cursor-not-allowed'
            : 'btn-outline hover:scale-105'
        } disabled:opacity-50`}
      >
        {loading ? <LoadingSpinner size="small" /> : following ? t('search.following') : t('search.follow')}
      </button>
    </div>
  );
};

export default RightSidebar;
