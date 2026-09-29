import React, { useEffect, useState } from 'react';
import { X, Star, Check, Calendar} from 'lucide-react';
import { useMovieStore } from '../store/useMovieStore';
import { apiClient } from '../api/client';
import type { Movie } from '../types/movie';


export const MovieDetailModal: React.FC = () => {
    const {selectedMovieId, closeMovieDetails, statusMap, setStatus, removeStatus} = useMovieStore();
    const [movie, setMovie] = useState<Movie | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    const status = selectedMovieId ? statusMap[selectedMovieId] : undefined;

    useEffect(() => {
        if (!selectedMovieId) {
            setMovie(null);
            return;
        }

        const fetchDetails = async () => {
            setLoading(true);
            try {
                const res = await apiClient.get(`/api/movies/${selectedMovieId}`);
                setMovie(res.data);
            } catch (err) {
                console.error("Ошибка загрузки деталей фильма:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchDetails();
    }, [selectedMovieId]);

    if (!selectedMovieId) return null;

    const handleToggleWatched = async () => {
        if (!selectedMovieId) return;
        try {
            if (status?.is_watched) {
                await apiClient.delete(`/api/user-movies/${selectedMovieId}`);
                removeStatus(selectedMovieId);
            } else {
                await apiClient.post('/api/user-movies', {
                    tmdb_movied_id: selectedMovieId,
                    is_watched: true,
                });
                setStatus(selectedMovieId, true);
            }
        } catch (err) {
            console.error("Ошибка изменения статуса:", err);
        }
    };

    const backdropUrl = movie?.backdrop_path 
        ? `https://image.tmdb.org/t/p/w780${movie.backdrop_path}`
        : null;

    
    return (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm transition-opacity">
            <div className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-t-3xl bg-tg-secondaryBg p-5 shadow-2xl border-t border-white/10 no-scrollbar">
                <button 
                    onClick={closeMovieDetails}
                    className="absolute right-4 top-4 z-10 p-2 rounded-full bg-black/50 text-tg-hint hover:text-white">
                        <X size={20}/>
                </button>
                {loading || !movie ? (
                    <div className="py-20 text-center text-sm text-tg-hint"> Загрузка информации о фильме...</div>
                ) : (
                    <div className="space-y-4">
                        {backdropUrl && (
                            <div className="-mx-5 -mt-5 h-48 overflow-hidden rounded-t-3xl relative">
                                <img src={backdropUrl} alt={movie.title} className="w-full h-full object-cover"/>
                                <div className="absolute inset-0 bg-gradient-to-t from-tg-secondaryBg via-transparent to-transparent"/>
                            </div>
                        )}

                        <div>
                            <h2 className="text-xl font-bold text-tg-text">{movie.title}</h2>
                            {movie.original_title && movie.original_title !== movie.title && (
                                <p className="text-xs test-tg-hint mt-0.5">{movie.original_title}</p>
                            )}
                        </div>

                        <div className="flex items-center gap-4 text-xs text-tg-hint">
                            {movie.release_date && (
                                <div className="flex items-center gap-1">
                                    <Calendar size={14}/>
                                    <span>{new Date(movie.release_date).getFullYear()}</span>
                                </div>
                            )}
                            {movie.vote_average !== undefined && (
                                <div className="flex items-center gap-1 font-semibold text-amber-400">
                                    <Star size={14} className="fill-amber-400"/>
                                    <span>{movie.vote_average.toFixed(1)}</span>
                                </div>
                            )}
                        </div>

                        {movie.overview && (
                            <p className="text-sm leading-relaxed text-tg-hint">{movie.overview}</p>
                        )}

                        <div className="pt-2 flex gap-3">
                            <button
                                onClick={handleToggleWatched}
                                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-medium text-sm transition-colors ${
                                status?.is_watched
                                ? 'bg-emerald-600 text-white'
                                : 'bg-tg-button text-tg-buttonText hover:opacity-90'}"
                                >
                                    <Check size={18}/>
                                    <span>{status?.is_watched ? 'Просмотрено' : 'Отметить просмотренным'}</span>
                            </button>
                        </div>
                    </div>
                )}
            </div>

        </div>
    )
}