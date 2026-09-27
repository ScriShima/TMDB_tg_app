import React from 'react';
import { Compass, Dices, Bookmark, User } from 'lucide-react';
import { useMovieStore } from '../store/useMovieStore';

export const BottomNav: React.FC = () => {
  const { activeTab, setActiveTab } = useMovieStore();

  const navItems = [
    { id: 'discover', label: 'Каталог', icon: Compass },
    { id: 'random', label: 'Рандом', icon: Dices },
    { id: 'library', label: 'Библиотека', icon: Bookmark },
    { id: 'profile', label: 'Профиль', icon: User },
  ] as const;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-tg-secondaryBg/90 backdrop-blur-md border-t border-white/5 pb-[env(safe-area-inset-bottom)]">
      <div className="flex justify-around items-center h-14 max-w-md mx-auto px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center justify-center w-full h-full transition-colors ${
                isActive ? 'text-tg-button font-medium' : 'text-tg-hint hover:text-tg-text'
              }`}
            >
              <Icon size={20} className={isActive ? 'stroke-[2.5]' : 'stroke-[1.75]'} />
              <span className="text-[11px] mt-1">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};