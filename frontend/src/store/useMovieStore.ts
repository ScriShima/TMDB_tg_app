import { create } from 'zustand';
import { apiClient } from '../api/client';

export interface MovieStatus {
  tmdb_movie_id: number;
  is_watched: boolean;
  rating?: number | null;
}

interface MovieStoreState {
  statusMap: Record<number, MovieStatus>;
  activeTab: 'discover' | 'random' | 'library' | 'profile';
  selectedMovieId: number | null;
  fetchStatuses: () => Promise<void>;
  setStatus: (movieId: number, isWatched: boolean, rating?: number | null) => void;
  removeStatus: (movieId: number) => void;
  setActiveTab: (tab: 'discover' | 'random' | 'library' | 'profile') => void;
  openMovieDetails: (movieId: number) => void;
  closeMovieDetails: () => void;
}

export const useMovieStore = create<MovieStoreState>((set) => ({
  statusMap: {},
  activeTab: 'discover',
  selectedMovieId: null,

  fetchStatuses: async () => {
    try {
      const response = await apiClient.get('/api/user-movies/statuses');
      const map: Record<number, MovieStatus> = {};
      const items: MovieStatus[] = response.data.items || [];
      items.forEach((item) => {
        map[item.tmdb_movie_id] = item;
      });
      set({ statusMap: map });
    } catch (err) {
      console.error('Ошибка загрузки статусов фильмов:', err);
    }
  },

  setStatus: (movieId, isWatched, rating = null) =>
    set((state) => ({
      statusMap: {
        ...state.statusMap,
        [movieId]: { tmdb_movie_id: movieId, is_watched: isWatched, rating },
      },
    })),

  removeStatus: (movieId) =>
    set((state) => {
      const updated = { ...state.statusMap };
      delete updated[movieId];
      return { statusMap: updated };
    }),

  setActiveTab: (tab) => set({ activeTab: tab }),
  openMovieDetails: (movieId) => set({ selectedMovieId: movieId }),
  closeMovieDetails: () => set({ selectedMovieId: null }),
}));