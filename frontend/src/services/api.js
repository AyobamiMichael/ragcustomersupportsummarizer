/**
 * API client for RAG Summarizer backend
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://ragcustomersupportsummarizer.onrender.com/';
const API_PREFIX = '/api/v1';

const api = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});


/**
 * Summarize text
 * @param {Object} params - Summarization parameters
 * @param {string} params.text - Text to summarize
 * @param {string} params.mode - Pipeline mode (extractive, semantic, abstractive)
 * @param {number} params.top_k - Number of sentences to extract
 * @param {boolean} params.include_provenance - Include provenance data
 * @returns {Promise<Object>} Summarization result
 */
export const summarizeText = async ({ text, mode = 'extractive', top_k = 3, include_provenance = true }) => {
  try {
    const response = await api.post('/summarize', {
      text,
      mode,
      top_k,
      include_provenance,
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.detail || 'Summarization failed');
    }
    throw error;
  }
};

/**
 * Health check
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};

export default api;

