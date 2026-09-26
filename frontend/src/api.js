import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('smarttrip_access_token') || localStorage.getItem('smarttrip_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login/') &&
      !originalRequest.url?.includes('/auth/token/refresh/')
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('smarttrip_refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE}/auth/token/refresh/`, { refresh: refreshToken });
          if (res.data && res.data.access) {
            const newAccess = res.data.access;
            localStorage.setItem('smarttrip_access_token', newAccess);
            localStorage.setItem('smarttrip_token', newAccess);
            originalRequest.headers.Authorization = `Bearer ${newAccess}`;
            return api(originalRequest);
          }
        } catch (refreshError) {
          localStorage.removeItem('smarttrip_access_token');
          localStorage.removeItem('smarttrip_refresh_token');
          localStorage.removeItem('smarttrip_token');
          window.dispatchEvent(new Event('auth_logout'));
        }
      }
    }
    return Promise.reject(error);
  }
);

// ===================== ORIGINAL APIs (unchanged) =====================
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

export const searchPlaces = async (query, location = '', radius = 5000) => {
  const params = new URLSearchParams({ q: query });
  if (location) params.append('location', location);
  if (radius) params.append('radius', String(radius));
  const response = await api.get(`/search/?${params.toString()}`);
  return response.data;
};

export const getPlaceDetails = async (placeId) => {
  const response = await api.get(`/place-details/?place_id=${encodeURIComponent(placeId)}`);
  return response.data;
};

export const getRouteSummary = async (origin, destination, mode = 'driving') => {
  const params = new URLSearchParams({ origin, destination, mode });
  const response = await api.get(`/route/?${params.toString()}`);
  return response.data;
};

export const getWeatherSummary = async (latitude, longitude) => {
  const params = new URLSearchParams({ latitude, longitude });
  const response = await api.get(`/weather/?${params.toString()}`);
  return response.data;
};

// ===================== AUTH APIs =====================
export const registerUser = async (data) => {
  const response = await api.post('/auth/register/', data);
  return response.data;
};

export const loginUser = async (data) => {
  const response = await api.post('/auth/login/', data);
  return response.data;
};

export const logoutUser = async (data) => {
  const response = await api.post('/auth/logout/', data || {});
  return response.data;
};

export const refreshToken = async (refresh) => {
  const response = await api.post('/auth/token/refresh/', { refresh });
  return response.data;
};

export const getMe = async () => {
  const response = await api.get('/auth/me/');
  return response.data;
};

export const updateProfile = async (data) => {
  const response = await api.put('/auth/profile/', data);
  return response.data;
};

// ===================== TRIPS =====================
export const getTrips = async () => {
  const response = await api.get('/trips/');
  return response.data;
};

export const getTrip = async (id) => {
  const response = await api.get(`/trips/${id}/`);
  return response.data;
};

export const getTripItinerary = async (id) => {
  const response = await api.get(`/trips/${id}/itinerary/`);
  return response.data;
};

export const getTripRoutes = async (id) => {
  const response = await api.get(`/trips/${id}/routes/`);
  return response.data;
};

export const getTripExpenses = async (id) => {
  const response = await api.get(`/trips/${id}/expenses/`);
  return response.data;
};

export const getTripConversations = async () => {
  const response = await api.get('/trips/ai/conversations/');
  return response.data;
};

export const savePersistentTrip = async (tripId) => {
  const response = await api.post('/trips/saved-trips/', { trip_id: tripId });
  return response.data;
};

export const getPersistentSavedTrips = async () => {
  const response = await api.get('/trips/saved-trips/');
  return response.data;
};

export const getTripDashboard = async () => {
  const response = await api.get('/trips/dashboard/');
  return response.data;
};

export const createTrip = async (tripData) => {
  const response = await api.post('/trips/', tripData);
  return response.data;
};

export const updateTrip = async (id, data) => {
  const response = await api.patch(`/trips/${id}/`, data);
  return response.data;
};

export const deleteTrip = async (id) => {
  const response = await api.delete(`/trips/${id}/`);
  return response.data;
};

// ===================== SAVED TRIPS =====================
export const getSavedTrips = async () => {
  const response = await api.get('/auth/saved-trips/');
  return response.data;
};

export const saveTrip = async (tripData) => {
  const response = await api.post('/auth/saved-trips/', tripData);
  return response.data;
};

export const updateSavedTrip = async (id, data) => {
  const response = await api.put(`/auth/saved-trips/${id}/`, data);
  return response.data;
};

export const deleteSavedTrip = async (id) => {
  const response = await api.delete(`/auth/saved-trips/${id}/`);
  return response.data;
};

// ===================== WISHLIST =====================
export const getWishlist = async () => {
  const response = await api.get('/auth/wishlist/');
  return response.data;
};

export const addToWishlist = async (data) => {
  const response = await api.post('/auth/wishlist/', data);
  return response.data;
};

export const removeFromWishlist = async (id) => {
  const response = await api.delete(`/auth/wishlist/${id}/`);
  return response.data;
};

// ===================== COMMUNITY =====================
export const getReviews = async (destinationName, page = 1) => {
  const url = page ? `/community/reviews/${encodeURIComponent(destinationName)}/?page=${page}` : `/community/reviews/${encodeURIComponent(destinationName)}/`;
  const response = await api.get(url);
  return response.data;
};

export const addReview = async (data) => {
  const response = await api.post('/community/reviews/add/', data);
  return response.data;
};

export const voteHelpful = async (reviewId) => {
  const response = await api.post(`/community/reviews/${reviewId}/helpful/`);
  return response.data;
};

export const getBlogs = async (destination, page = 1) => {
  const params = new URLSearchParams();
  if (destination) params.append('destination', destination);
  if (page) params.append('page', page);
  const queryStr = params.toString() ? `?${params.toString()}` : '';
  const response = await api.get(`/community/blogs/${queryStr}`);
  return response.data;
};

export const createBlog = async (data) => {
  const response = await api.post('/community/blogs/create/', data);
  return response.data;
};

export const likeBlog = async (blogId) => {
  const response = await api.post(`/community/blogs/${blogId}/like/`);
  return response.data;
};

export const getTrending = async (page = 1) => {
  const url = page ? `/community/trending/?page=${page}` : '/community/trending/';
  const response = await api.get(url);
  return response.data;
};

// ===================== AI CHATBOT =====================
export const sendChatMessage = async (data) => {
  const response = await api.post('/chat/', data);
  return response.data;
};

// ===================== AI ITINERARY =====================
export const getDayWiseItinerary = async ({ destination_name, num_days, trip_data = {} }) => {
  const response = await api.post('/itinerary/', { destination_name, num_days, trip_data });
  return response.data;
};

export default api;

