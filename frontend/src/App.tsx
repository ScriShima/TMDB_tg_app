import React, { useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import { useMovieStore } from './store/useMovieStore';
import { BottomNav } from './components/BottomNav';
import { DiscoverPage } from './pages/DiscoverPage';
import { RandomPage } from './pages/RandomPage';
import { LibraryPage } from './pages/LibraryPage';
import { ProfilePage } from './pages/ProfilePage';
import { MovieDetailModal } from './components/MovieDetailModal';

export const App: React.FC = () => {
  const { activeTab, fetchStatuses } = useMovieStore();

  useEffect(() => {
    // Сообщаем клиенту Telegram, что приложение готово и разворачиваем на всю высоту
    try {
      WebApp.ready();
      WebApp.expand();
    } catch {
      // Игнорируем ошибку при запуске в обычном веб-браузере
    }

    // Загружаем сохраненные статусы фильмов пользователя
    fetchStatuses();
  }, [fetchStatuses]);

  const renderCurrentPage = () => {
    switch (activeTab) {
      case 'discover':
        return <DiscoverPage />;
      case 'random':
        return <RandomPage />;
      case 'library':
        return <LibraryPage />;
      case 'profile':
        return <ProfilePage />;
      default:
        return <DiscoverPage />;
    }
  };

  return (
    <div className="min-h-screen bg-tg-bg text-tg-text pb-20">
      <main className="max-w-md mx-auto">
        {renderCurrentPage()}
      </main>
      <BottomNav />
      <MovieDetailModal />
    </div>
  );
};

export default App;