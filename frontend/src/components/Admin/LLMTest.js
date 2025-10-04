import React, { useState } from 'react';
import axios from 'axios';
import { useLanguage } from '../../contexts/LanguageContext';
import LoadingSpinner from '../Common/LoadingSpinner';

const LLMTest = () => {
  const { t } = useLanguage();
  const [testResult, setTestResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [customTest, setCustomTest] = useState({
    text: 'Hello, how are you today?',
    sourceLang: 'en',
    targetLang: 'fr'
  });
  const [customResult, setCustomResult] = useState(null);
  const [customLoading, setCustomLoading] = useState(false);

  const testLLMConnection = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/translate/test');
      setTestResult(response.data);
    } catch (error) {
      setTestResult({
        llm_connected: false,
        error: error.response?.data?.error || error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const testCustomTranslation = async () => {
    setCustomLoading(true);
    try {
      const response = await axios.post('/api/translate/text', {
        content: customTest.text,
        source_lang: customTest.sourceLang,
        target_lang: customTest.targetLang
      });
      setCustomResult(response.data);
    } catch (error) {
      setCustomResult({
        success: false,
        error: error.response?.data?.error || error.message
      });
    } finally {
      setCustomLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">LLM Translation Service Test</h1>
      
      {/* Connection Test */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">Connection Test</h2>
        <button
          onClick={testLLMConnection}
          disabled={loading}
          className="btn-primary mb-4"
        >
          {loading ? <LoadingSpinner size="small" /> : 'Test LLM Connection'}
        </button>

        {testResult && (
          <div className="mt-4">
            <div className={`p-4 rounded-lg ${testResult.llm_connected ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <h3 className="font-semibold mb-2">
                {testResult.llm_connected ? '✅ LLM Connected' : '❌ LLM Connection Failed'}
              </h3>
              
              <div className="space-y-2 text-sm">
                <div>
                  <strong>Translation Service:</strong> {testResult.translation_service_available ? '✅ Available' : '❌ Unavailable'}
                </div>
                
                {testResult.ollama_config && (
                  <div>
                    <strong>Ollama Config:</strong>
                    <ul className="ml-4 mt-1">
                      <li>Host: {testResult.ollama_config.host}</li>
                      <li>Port: {testResult.ollama_config.port}</li>
                      <li>Model: {testResult.ollama_config.model}</li>
                    </ul>
                  </div>
                )}
                
                {testResult.supported_languages && (
                  <div>
                    <strong>Supported Languages:</strong> {testResult.supported_languages.join(', ')}
                  </div>
                )}
                
                {testResult.test_translation && (
                  <div>
                    <strong>Test Translation:</strong>
                    <div className="ml-4 mt-1">
                      <div>Input: "Hello, how are you?"</div>
                      <div>Output: "{testResult.test_translation.translated_content}"</div>
                      <div>Success: {testResult.test_translation.success ? '✅' : '❌'}</div>
                      <div>Cached: {testResult.test_translation.cached ? 'Yes' : 'No'}</div>
                    </div>
                  </div>
                )}
                
                {testResult.error && (
                  <div className="text-red-600">
                    <strong>Error:</strong> {testResult.error}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Custom Translation Test */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Custom Translation Test</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Text to Translate:</label>
            <textarea
              value={customTest.text}
              onChange={(e) => setCustomTest({...customTest, text: e.target.value})}
              className="input-field w-full"
              rows="3"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Source Language:</label>
              <select
                value={customTest.sourceLang}
                onChange={(e) => setCustomTest({...customTest, sourceLang: e.target.value})}
                className="input-field w-full"
              >
                <option value="en">{t('languages.en')}</option>
                <option value="fr">{t('languages.fr')}</option>
                <option value="pt">{t('languages.pt')}</option>
                <option value="de">{t('languages.de')}</option>
                <option value="es">{t('languages.es')}</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Target Language:</label>
              <select
                value={customTest.targetLang}
                onChange={(e) => setCustomTest({...customTest, targetLang: e.target.value})}
                className="input-field w-full"
              >
                <option value="en">{t('languages.en')}</option>
                <option value="fr">{t('languages.fr')}</option>
                <option value="pt">{t('languages.pt')}</option>
                <option value="de">{t('languages.de')}</option>
                <option value="es">{t('languages.es')}</option>
              </select>
            </div>
          </div>
          
          <button
            onClick={testCustomTranslation}
            disabled={customLoading || !customTest.text.trim()}
            className="btn-primary"
          >
            {customLoading ? <LoadingSpinner size="small" /> : 'Translate'}
          </button>
        </div>

        {customResult && (
          <div className="mt-4">
            <div className={`p-4 rounded-lg ${customResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <h3 className="font-semibold mb-2">
                {customResult.success ? '✅ Translation Successful' : '❌ Translation Failed'}
              </h3>
              
              <div className="space-y-2 text-sm">
                {customResult.success && (
                  <>
                    <div><strong>Original:</strong> {customTest.text}</div>
                    <div><strong>Translated:</strong> {customResult.translated_content}</div>
                    <div><strong>Cached:</strong> {customResult.cached ? 'Yes (from cache)' : 'No (fresh translation)'}</div>
                  </>
                )}
                
                {customResult.error && (
                  <div className="text-red-600">
                    <strong>Error:</strong> {customResult.error}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LLMTest;
