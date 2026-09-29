import React, { useState, useEffect } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';
import type { Movie } from '../types/movie';
import { MovieCard } from '../components/MovieCard';

export const DiscoverPage: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);

  // Функция загрузки списка популярных фильмов
  const fetchTrendingMovies = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/api/movies/popular');
      setMovies(response.data.results || []);
    } catch (err) {
      console.error('Ошибка загрузки популярных фильмов:', err);
    } finally {
      setLoading(false);
    }
  };

  // Функция поиска фильмов
  const searchMovies = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      fetchTrendingMovies();
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.get('/api/movies/search', {
        params: { query: searchQuery },
      });
      setMovies(response.data.results || []);
    } catch (err) {
      console.error('Ошибка поиска:', err);
    } finally {
      setLoading(false);
    }
  };

  // Первичная загрузка при открытии экрана
  useEffect(() => {
    fetchTrendingMovies();
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    searchMovies(value);
  };

  return (
    <div className="p-4">
      {/* Поле поиска */}
      <div className="relative mb-6">
        <Search
          size={18}
          className="absolute left-3.5 top-1/2 -translate-y-1/2 text-tg-hint"
        />
        <input
          type="text"
          value={query}
          onChange={handleSearchChange}
          placeholder="Поиск фильмов..."
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-tg-secondaryBg text-tg-text placeholder-tg-hint text-sm outline-none border border-transparent focus:border-tg-button transition-colors"
        />
      </div>

      {/* Заголовок секции */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold">
          {query ? 'Результаты поиска' : 'Популярные фильмы'}
        </h2>
        {loading && <Loader2 size={18} className="animate-spin text-tg-hint" />}
      </div>

      {/* Сетка карточек */}
      {movies.length > 0 ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {movies.map((movie) => (
            <MovieCard key={movie.id} movie={movie} />
          ))}
        </div>
      ) : (
        !loading && (
          <div className="text-center py-12 text-sm text-tg-hint">
            Ничего не найдено
          </div>
        )
      )}
    </div>
  );
};