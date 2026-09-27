import axios from "axios";
import WebApp from "@twa-dev/sdk";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
    let token = WebApp.initData;

    if (!token && import.meta.env.DEV) {
        token = 'dev-test';
    }

    if (token) {
        config.headers.Authorization = 'Bearer ${token}';
    }

    return config;
});