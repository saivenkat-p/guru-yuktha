import React from 'react';
import { Home, Users, Plus, BookOpen, BarChart3 } from 'lucide-react';

interface BottomNavProps {
  activeTab: 'dashboard' | 'rooms' | 'students' | 'materials' | 'reports';
  onSelectTab: (tab: 'dashboard' | 'rooms' | 'students' | 'materials' | 'reports') => void;
  onOpenQuickAdd: () => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  activeTab,
  onSelectTab,
  onOpenQuickAdd,
}) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'rooms', label: 'Rooms', icon: BookOpen },
    { id: 'students', label: 'Students', icon: Users },
    { id: 'reports', label: 'Reports', icon: BarChart3 },
  ];

  return (
    <div className="sticky bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-4 py-2 flex items-center justify-between z-30 shadow-lg max-w-[480px] mx-auto w-full">
      {/* Left 2 tabs */}
      <div className="flex items-center space-x-6">
        {tabs.slice(0, 2).map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id as any)}
              className={`flex flex-col items-center justify-center space-y-1 transition-colors ${
                isActive ? 'text-indigo-600 font-semibold' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] tracking-tight">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Floating Center Plus Button */}
      <div className="relative -top-5">
        <button
          onClick={onOpenQuickAdd}
          className="w-14 h-14 rounded-full bg-gradient-to-tr from-indigo-700 via-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-lg shadow-indigo-500/30 hover:scale-105 active:scale-95 transition-all border-4 border-slate-100"
          aria-label="Quick Add Activity"
        >
          <Plus className="w-7 h-7 text-white stroke-[2.5]" />
        </button>
      </div>

      {/* Right 2 tabs */}
      <div className="flex items-center space-x-6">
        {tabs.slice(2, 4).map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id as any)}
              className={`flex flex-col items-center justify-center space-y-1 transition-colors ${
                isActive ? 'text-indigo-600 font-semibold' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] tracking-tight">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
