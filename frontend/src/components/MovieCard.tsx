import React from 'react';
import { Star, Check } from 'lucide-react';
import type { Movie } from '../types/movie';
import { useMovieStore } from '../store/useMovieStore';

interface MovieCardProps {
  movie: Movie;
}

export const MovieCard: React.FC<MovieCardProps> = ({ movie }) => {
  const { statusMap, openMovieDetails } = useMovieStore();
  const status = statusMap[movie.id];

  const posterUrl = movie.poster_path
    ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
    : null;

  const year = movie.release_date
    ? new Date(movie.release_date).getFullYear()
    : null;

  return (
    <div
      onClick={() => openMovieDetails(movie.id)}
      className="group relative flex flex-col cursor-pointer transition-transform active:scale-95"
    >
      <div className="relative aspect-[2/3] w-full rounded-xl overflow-hidden bg-tg-secondaryBg shadow-md">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={movie.title}
            loading="lazy"
            className="w-full h-full object-cover transition-opacity duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center p-2 text-center text-xs text-tg-hint bg-slate-800">
            Нет постера
          </div>
        )}

        {/* Бейдж рейтинга */}
        {movie.vote_average !== undefined && movie.vote_average > 0 && (
          <div className="absolute top-2 left-2 flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-black/70 backdrop-blur-sm text-[11px] font-semibold text-amber-400">
            <Star size={11} className="fill-amber-400" />
            <span>{movie.vote_average.toFixed(1)}</span>
          </div>
        )}

        {/* Бейдж просмотрено / оценка */}
        {status?.is_watched && (
          <div className="absolute top-2 right-2 flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-emerald-600/90 text-white text-[11px] font-medium backdrop-blur-sm">
            <Check size={12} strokeWidth={2.5} />
            {status.rating ? <span>{status.rating}/10</span> : <span>В архиве</span>}
          </div>
        )}
      </div>

      <div className="mt-2 flex flex-col">
        <h3 className="text-xs font-semibold line-clamp-1 text-tg-text">
          {movie.title}
        </h3>
        {year && (
          <span className="text-[11px] text-tg-hint">
            {year}
          </span>
        )}
      </div>
    </div>
  );
};