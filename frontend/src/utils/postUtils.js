import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Render post content with clickable mentions and hashtags
 * @param {string} content - The post content to render
 * @returns {Array} - Array of React elements with links
 */
export const renderPostContent = (content) => {
  if (!content) return '';
  
  // Split content by mentions (@username) and hashtags (#hashtag)
  const parts = content.split(/(@\w+|#\w+)/g);

  return parts.map((part, index) => {
    if (part.startsWith('@')) {
      // Handle mentions - link to user profile
      const handle = part.substring(1);
      return (
        <Link
          key={index}
          to={`/profile/${handle}`}
          className="text-primary-blue hover:underline"
        >
          {part}
        </Link>
      );
    } else if (part.startsWith('#')) {
      // Handle hashtags - link to search
      return (
        <Link
          key={index}
          to={`/search?q=${encodeURIComponent(part)}`}
          className="text-primary-blue hover:underline"
        >
          {part}
        </Link>
      );
    }
    // Return regular text as-is
    return part;
  });
};

/**
 * Extract mentions from post content
 * @param {string} content - The post content
 * @returns {Array} - Array of mentioned usernames (without @)
 */
export const extractMentions = (content) => {
  if (!content) return [];
  const matches = content.match(/@(\w+)/g);
  return matches ? matches.map(match => match.substring(1)) : [];
};

/**
 * Extract hashtags from post content
 * @param {string} content - The post content
 * @returns {Array} - Array of hashtags (without #)
 */
export const extractHashtags = (content) => {
  if (!content) return [];
  const matches = content.match(/#(\w+)/g);
  return matches ? matches.map(match => match.substring(1)) : [];
};

/**
 * Check if content contains mentions or hashtags
 * @param {string} content - The post content
 * @returns {boolean} - True if content has mentions or hashtags
 */
export const hasLinkedContent = (content) => {
  if (!content) return false;
  return /@\w+|#\w+/.test(content);
};
