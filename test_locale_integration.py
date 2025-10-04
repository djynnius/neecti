#!/usr/bin/env python3
"""
Test script to verify locale integration for the profile page.
This script tests that all translation keys used in the Profile component
exist in all 5 supported language files.
"""

import json
import os
import sys
from pathlib import Path

def load_translation_file(lang_code):
    """Load a translation file and return its content."""
    file_path = Path(f"frontend/src/locales/{lang_code}.json")
    if not file_path.exists():
        print(f"❌ Translation file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None

def get_nested_value(data, key_path):
    """Get a nested value from a dictionary using dot notation."""
    keys = key_path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current

def test_locale_integration():
    """Test that all required translation keys exist in all language files."""
    
    # List of supported languages
    languages = ['en', 'fr', 'pt', 'es', 'de']
    
    # Translation keys used in the Profile component
    required_keys = [
        'profile.user_not_found',
        'profile.following_you',
        'profile.no_bio',
        'profile.joined',
        'profile.posts',
        'profile.followers',
        'profile.following',
        'profile.edit_profile',
        'profile.settings',
        'profile.follow',
        'profile.unfollow',
        'profile.change_password',
        'profile.current_password',
        'profile.new_password',
        'profile.confirm_new_password',
        'profile.save_changes',
        'profile.cancel_edit',
        'profile.bio',
        'profile.bio_placeholder',
        'profile.dark_mode',
        'profile.profile_updated',
        'profile.profile_update_error',
        'profile.password_changed',
        'profile.password_change_error',
        'profile.no_posts',
        'auth.first_name',
        'auth.last_name',
        'auth.preferred_language',
        'languages.en',
        'languages.fr',
        'languages.pt',
        'languages.es',
        'languages.de',
        'post.replies',
        'post.likes',
        'post.shares'
    ]
    
    print("🔍 Testing locale integration for Profile page...")
    print(f"📋 Checking {len(required_keys)} translation keys across {len(languages)} languages")
    print()
    
    # Load all translation files
    translations = {}
    for lang in languages:
        translations[lang] = load_translation_file(lang)
        if translations[lang] is None:
            return False
    
    # Test each required key in each language
    missing_keys = {}
    total_tests = 0
    passed_tests = 0
    
    for lang in languages:
        missing_keys[lang] = []
        print(f"🌐 Testing {lang.upper()} translations...")
        
        for key in required_keys:
            total_tests += 1
            value = get_nested_value(translations[lang], key)
            if value is None:
                missing_keys[lang].append(key)
                print(f"  ❌ Missing key: {key}")
            else:
                passed_tests += 1
                print(f"  ✅ {key}: '{value}'")
        
        if not missing_keys[lang]:
            print(f"  🎉 All keys found in {lang.upper()}!")
        print()
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    # Report missing keys
    has_missing_keys = False
    for lang in languages:
        if missing_keys[lang]:
            has_missing_keys = True
            print(f"❌ Missing keys in {lang.upper()}:")
            for key in missing_keys[lang]:
                print(f"   - {key}")
            print()
    
    if not has_missing_keys:
        print("🎉 SUCCESS: All required translation keys are present in all languages!")
        print("✅ Profile page locale integration is complete and working correctly.")
        return True
    else:
        print("❌ FAILURE: Some translation keys are missing.")
        print("🔧 Please add the missing keys to complete the locale integration.")
        return False

if __name__ == "__main__":
    success = test_locale_integration()
    sys.exit(0 if success else 1)
