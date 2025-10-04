import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { renderPostContent } from '../utils/postUtils';
import api from '../utils/api';
import LoadingSpinner from '../components/Common/LoadingSpinner';

const Profile = () => {
  const { handle } = useParams();
  const { user: currentUser, updateProfile, changePassword } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [profileUser, setProfileUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showPasswordChange, setShowPasswordChange] = useState(false);

  // Form states
  const [editForm, setEditForm] = useState({
    first_name: '',
    last_name: '',
    bio: '',
    preferred_language: '',
    dark_mode: false
  });

  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_new_password: ''
  });

  const [formErrors, setFormErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState('');

  const isOwnProfile = currentUser && currentUser.handle === handle;

  useEffect(() => {
    fetchUserProfile();
  }, [handle]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/users/@${handle}`);
      setProfileUser(response.data.user);
      setPosts(response.data.user.posts || []);

      if (isOwnProfile) {
        setEditForm({
          first_name: response.data.user.first_name,
          last_name: response.data.user.last_name,
          bio: response.data.user.bio || '',
          preferred_language: response.data.user.preferred_language,
          dark_mode: response.data.user.dark_mode
        });
      }
    } catch (error) {
      setError(error.response?.data?.error || t('profile.user_not_found'));
    } finally {
      setLoading(false);
    }
  };

  const handleFollow = async () => {
    try {
      await api.post(`/users/@${handle}/follow`);
      setProfileUser(prev => ({
        ...prev,
        is_following: true,
        followers_count: prev.followers_count + 1
      }));
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to follow user');
    }
  };

  const handleUnfollow = async () => {
    try {
      await api.post(`/users/@${handle}/unfollow`);
      setProfileUser(prev => ({
        ...prev,
        is_following: false,
        followers_count: prev.followers_count - 1
      }));
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to unfollow user');
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setFormErrors({});
    setSuccessMessage('');

    try {
      const result = await updateProfile(editForm);
      if (result.success) {
        setProfileUser(result.user);
        setIsEditing(false);
        setSuccessMessage(t('profile.profile_updated'));
      } else {
        setFormErrors({ general: result.error });
      }
    } catch (error) {
      setFormErrors({ general: t('profile.profile_update_error') });
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setFormErrors({});
    setSuccessMessage('');

    if (passwordForm.new_password !== passwordForm.confirm_new_password) {
      setFormErrors({ confirm_new_password: 'Passwords do not match' });
      return;
    }

    try {
      const result = await changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      });

      if (result.success) {
        setPasswordForm({ current_password: '', new_password: '', confirm_new_password: '' });
        setShowPasswordChange(false);
        setSuccessMessage(t('profile.password_changed'));
      } else {
        setFormErrors({ general: result.error });
      }
    } catch (error) {
      setFormErrors({ general: t('profile.password_change_error') });
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const handleDeletePost = async (postId) => {
    if (!window.confirm(t('post.delete_confirm_message'))) {
      return;
    }

    try {
      await api.delete(`/posts/${postId}`);
      // Remove the post from the local state
      setPosts(prevPosts => prevPosts.filter(post => post.id !== postId));
    } catch (error) {
      console.error('Error deleting post:', error);
      setError(error.response?.data?.error || 'Failed to delete post');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="text-center py-8">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!profileUser) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card">
          <div className="text-center py-8">
            <p className="text-gray-600 dark:text-gray-400">{t('profile.user_not_found')}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Success Message */}
      {successMessage && (
        <div className="bg-green-100 dark:bg-green-900 border border-green-400 text-green-700 dark:text-green-300 px-4 py-3 rounded">
          {successMessage}
        </div>
      )}

      {/* Profile Header */}
      <div className="card">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between">
          <div className="flex items-start space-x-4">
            {/* Profile Picture */}
            <div className="w-24 h-24 bg-primary-blue rounded-full flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
              {profileUser.first_name[0]}{profileUser.last_name[0]}
            </div>

            {/* User Info */}
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {profileUser.full_name}
              </h1>
              <p className="text-gray-600 dark:text-gray-400">@{profileUser.handle}</p>

              {profileUser.is_followed_by && (
                <span className="inline-block bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs px-2 py-1 rounded mt-1">
                  {t('profile.following_you')}
                </span>
              )}

              <div className="mt-3">
                {profileUser.bio ? (
                  <p className="text-gray-700 dark:text-gray-300">{profileUser.bio}</p>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400 italic">{t('profile.no_bio')}</p>
                )}
              </div>

              <div className="flex items-center space-x-4 mt-3 text-sm text-gray-600 dark:text-gray-400">
                <span>{t('profile.joined')} {formatDate(profileUser.created_at)}</span>
              </div>

              {/* Stats */}
              <div className="flex items-center space-x-6 mt-4">
                <div className="text-center">
                  <div className="font-bold text-gray-900 dark:text-white">{profileUser.posts_count}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{t('profile.posts')}</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-gray-900 dark:text-white">{profileUser.followers_count}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{t('profile.followers')}</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-gray-900 dark:text-white">{profileUser.following_count}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{t('profile.following')}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-4 md:mt-0 flex space-x-2">
            {isOwnProfile ? (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-secondary"
                >
                  {t('profile.edit_profile')}
                </button>
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="btn-secondary"
                >
                  {t('profile.settings')}
                </button>
              </>
            ) : (
              currentUser && (
                <button
                  onClick={profileUser.is_following ? handleUnfollow : handleFollow}
                  className={profileUser.is_following ? 'btn-secondary' : 'btn-primary'}
                >
                  {profileUser.is_following ? t('profile.unfollow') : t('profile.follow')}
                </button>
              )
            )}
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {isOwnProfile && showSettings && (
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            {t('profile.settings')}
          </h2>

          <div className="space-y-4">
            <button
              onClick={() => setShowPasswordChange(!showPasswordChange)}
              className="btn-secondary w-full md:w-auto"
            >
              {t('profile.change_password')}
            </button>
          </div>
        </div>
      )}

      {/* Password Change Form */}
      {isOwnProfile && showPasswordChange && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {t('profile.change_password')}
          </h3>

          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            {formErrors.general && (
              <div className="text-red-600 dark:text-red-400 text-sm">
                {formErrors.general}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('profile.current_password')}
              </label>
              <input
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, current_password: e.target.value }))}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('profile.new_password')}
              </label>
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, new_password: e.target.value }))}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('profile.confirm_new_password')}
              </label>
              <input
                type="password"
                value={passwordForm.confirm_new_password}
                onChange={(e) => setPasswordForm(prev => ({ ...prev, confirm_new_password: e.target.value }))}
                className="input-field"
                required
              />
              {formErrors.confirm_new_password && (
                <p className="text-red-600 dark:text-red-400 text-sm mt-1">
                  {formErrors.confirm_new_password}
                </p>
              )}
            </div>

            <div className="flex space-x-2">
              <button type="submit" className="btn-primary">
                {t('profile.save_changes')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowPasswordChange(false);
                  setPasswordForm({ current_password: '', new_password: '', confirm_new_password: '' });
                  setFormErrors({});
                }}
                className="btn-secondary"
              >
                {t('profile.cancel_edit')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Profile Form */}
      {isOwnProfile && isEditing && (
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            {t('profile.edit_profile')}
          </h2>

          <form onSubmit={handleEditSubmit} className="space-y-4">
            {formErrors.general && (
              <div className="text-red-600 dark:text-red-400 text-sm">
                {formErrors.general}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('auth.first_name')}
                </label>
                <input
                  type="text"
                  value={editForm.first_name}
                  onChange={(e) => setEditForm(prev => ({ ...prev, first_name: e.target.value }))}
                  className="input-field"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('auth.last_name')}
                </label>
                <input
                  type="text"
                  value={editForm.last_name}
                  onChange={(e) => setEditForm(prev => ({ ...prev, last_name: e.target.value }))}
                  className="input-field"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('profile.bio')}
              </label>
              <textarea
                value={editForm.bio}
                onChange={(e) => setEditForm(prev => ({ ...prev, bio: e.target.value }))}
                placeholder={t('profile.bio_placeholder')}
                className="input-field"
                rows="3"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {t('auth.preferred_language')}
              </label>
              <select
                value={editForm.preferred_language}
                onChange={(e) => setEditForm(prev => ({ ...prev, preferred_language: e.target.value }))}
                className="input-field"
              >
                <option value="en">{t('languages.en')}</option>
                <option value="fr">{t('languages.fr')}</option>
                <option value="pt">{t('languages.pt')}</option>
                <option value="de">{t('languages.de')}</option>
                <option value="es">{t('languages.es')}</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="dark_mode"
                checked={editForm.dark_mode}
                onChange={(e) => setEditForm(prev => ({ ...prev, dark_mode: e.target.checked }))}
                className="mr-2"
              />
              <label htmlFor="dark_mode" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {t('profile.dark_mode')}
              </label>
            </div>

            <div className="flex space-x-2">
              <button type="submit" className="btn-primary">
                {t('profile.save_changes')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsEditing(false);
                  setFormErrors({});
                }}
                className="btn-secondary"
              >
                {t('profile.cancel_edit')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Posts Section */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          {t('profile.posts')}
        </h2>

        {posts.length > 0 ? (
          <div className="space-y-4">
            {posts.map((post) => (
              <div key={post.id} className="border-b border-gray-200 dark:border-gray-700 pb-4 last:border-b-0">
                <div className="flex items-start space-x-3">
                  <div className="w-10 h-10 bg-primary-blue rounded-full flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                    {profileUser.first_name[0]}{profileUser.last_name[0]}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {profileUser.full_name}
                      </span>
                      <span className="text-gray-500 dark:text-gray-400">
                        @{profileUser.handle}
                      </span>
                      <span className="text-gray-500 dark:text-gray-400">·</span>
                      <span className="text-gray-500 dark:text-gray-400">
                        {formatDate(post.created_at)}
                      </span>
                    </div>

                    <div className="mt-1">
                      <div className="text-gray-900 dark:text-white whitespace-pre-wrap">
                        {renderPostContent(post.content)}
                      </div>
                    </div>

                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                        <span>{post.replies_count || 0} {t('post.replies')}</span>
                        <span>{post.likes_count || 0} {t('post.likes')}</span>
                        <span>{post.shares_count || 0} {t('post.shares')}</span>
                      </div>

                      {/* Delete button for own posts */}
                      {isOwnProfile && (
                        <button
                          onClick={() => handleDeletePost(post.id)}
                          className="text-gray-400 hover:text-red-500 p-1"
                          title={t('post.delete')}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-600 dark:text-gray-400">{t('profile.no_posts')}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;
