import axios from 'axios';
import { API_BASE_URL } from '../utils/constants.js';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('buildtrack_token') || sessionStorage.getItem('buildtrack_access');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const companyId = localStorage.getItem('buildtrack_company');
  if (companyId) config.headers['X-Company-ID'] = companyId;
  return config;
});

export default client;
