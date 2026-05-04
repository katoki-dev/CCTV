import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000', // Update with your Flask backend URL
  withCredentials: true,
});

export default api;
