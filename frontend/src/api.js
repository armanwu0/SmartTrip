import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export const getRecommendations = async (tripData) => {
  const response = await api.post('/recommendations/', tripData);
  return response.data;
};

export const getDestinationDetail = async (recommendationId) => {
  const response = await api.get(`/destination/${recommendationId}/`);
  return response.data;
};

export const getLocationSuggestions = async (query) => {
  const response = await api.get(`/autocomplete/?q=${encodeURIComponent(query)}`);
  return response.data.suggestions;
};

export default api;
