import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

// Import language files
import en from '../locales/en.json';
import fr from '../locales/fr.json';
import pt from '../locales/pt.json';
import es from '../locales/es.json';
import de from '../locales/de.json';

const LanguageContext = createContext();

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

const translations = {
  en,
  fr,
  pt,
  es,
  de
};

export const LanguageProvider = ({ children }) => {
  const { user } = useAuth();
  const [currentLanguage, setCurrentLanguage] = useState('en');

  // Update language when user changes or logs in
  useEffect(() => {
    if (user && user.preferred_language) {
      // Use the user's preferred language from their profile
      setCurrentLanguage(user.preferred_language);
    } else if (!user) {
      // For non-authenticated users, fallback to browser language or English
      const browserLang = navigator.language.split('-')[0];
      if (translations[browserLang]) {
        setCurrentLanguage(browserLang);
      } else {
        setCurrentLanguage('en');
      }
    } else if (user && !user.preferred_language) {
      // User exists but no preferred_language set, default to English
      setCurrentLanguage('en');
    }
  }, [user]);

  // Translation function
  const t = (key, params = {}) => {
    const keys = key.split('.');
    let value = translations[currentLanguage];

    // Navigate through nested keys
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        // Fallback to English if key not found
        value = translations['en'];
        for (const fallbackKey of keys) {
          if (value && typeof value === 'object' && fallbackKey in value) {
            value = value[fallbackKey];
          } else {
            return key; // Return key if not found in any language
          }
        }
        break;
      }
    }

    // Handle string interpolation
    if (typeof value === 'string' && Object.keys(params).length > 0) {
      return value.replace(/\{\{(\w+)\}\}/g, (match, paramKey) => {
        return params[paramKey] || match;
      });
    }

    return value || key;
  };

  // Pluralization helper
  const tp = (key, count, params = {}) => {
    if (count === 1) {
      return t(key, { ...params, count });
    } else {
      return t(key + '_plural', { ...params, count });
    }
  };

  // Note: Language is automatically set from user's profile preference
  // Users can change their language preference in their profile settings

  // Get available languages
  const getAvailableLanguages = () => {
    return Object.keys(translations).map(code => ({
      code,
      name: t(`languages.${code}`)
    }));
  };

  // Format relative time based on language
  const formatRelativeTime = (date) => {
    const now = new Date();
    const diff = now - new Date(date);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return t('home.now');
    if (minutes < 60) return `${minutes}${t('home.minutes')}`;
    if (hours < 24) return `${hours}${t('home.hours')}`;
    return `${days}${t('home.days')}`;
  };

  const value = {
    currentLanguage,
    t,
    tp,
    formatRelativeTime
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};
