import React, { useState } from 'react';
import { Home, Users, BookOpen, BarChart3, Plus, GraduationCap, FileText, User, Compass, Copy, Check } from 'lucide-react';

interface DesktopSidebarProps {
  activeTab: 'dashboard' | 'rooms' | 'discover' | 'students' | 'materials' | 'reports';
  teacherName?: string;
  designation?: string;
  guruId?: string;
  username?: string;
  avatarUrl?: string;
  onSelectTab: (tab: 'dashboard' | 'rooms' | 'discover' | 'students' | 'materials' | 'reports') => void;
  onOpenQuickAdd: () => void;
  onOpenProfile?: () => void;
}

export const DesktopSidebar: React.FC<DesktopSidebarProps> = ({
  activeTab,
  teacherName = "Md. Shahazadi Begum",
  designation = "Universal Member",
  guruId,
  username,
  avatarUrl = "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
  onSelectTab,
  onOpenQuickAdd,
  onOpenProfile,
}) => {
  const [copied, setCopied] = useState(false);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'discover', label: 'Discover & Network', icon: Compass },
    { id: 'rooms', label: 'Universal Rooms', icon: BookOpen },
    { id: 'students', label: 'Tracked Students', icon: Users },
    { id: 'materials', label: 'Materials', icon: FileText },
    { id: 'reports', label: 'Reports', icon: BarChart3 },
  ];

  const handleCopyGuruId = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!guruId) return;
    navigator.clipboard.writeText(guruId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <aside className="hidden md:flex flex-col w-64 bg-indigo-900 text-white border-r border-indigo-800/80 min-h-screen p-5 shrink-0 justify-between">
      <div>
        {/* Logo */}
        <div className="flex items-center space-x-3 mb-8 px-2">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
            <GraduationCap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight leading-none">Guru Yuktha</h1>
            <p className="text-[10px] text-indigo-300 font-medium tracking-wide mt-1 uppercase">Universal Academic</p>
          </div>
        </div>

        {/* Quick Add Button */}
        <button
          onClick={onOpenQuickAdd}
          className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white py-3 px-4 rounded-2xl font-bold shadow-lg shadow-indigo-500/25 flex items-center justify-center space-x-2 transition-all active:scale-95 mb-8"
        >
          <Plus className="w-5 h-5" />
          <span className="text-xs">Quick Add Activity</span>
        </button>

        {/* Nav Links */}
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id as any)}
                className={`w-full flex items-center space-x-3.5 px-4 py-3 rounded-2xl font-semibold text-xs transition-all ${
                  isActive
                    ? 'bg-white/15 text-white shadow-xs font-bold border-l-4 border-indigo-400'
                    : 'text-indigo-200 hover:bg-white/10 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Member Profile Footer with Guru ID */}
      <div
        onClick={onOpenProfile}
        className="bg-indigo-950/60 p-3.5 rounded-2xl border border-indigo-800/50 flex flex-col space-y-2 cursor-pointer hover:bg-indigo-950 transition-colors group"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 min-w-0">
            <img
              src={avatarUrl}
              alt={teacherName}
              className="w-9 h-9 rounded-full border border-indigo-400 object-cover shrink-0 group-hover:scale-105 transition-transform"
            />
            <div className="min-w-0">
              <h4 className="text-xs font-bold text-white truncate group-hover:underline">{teacherName}</h4>
              <p className="text-[10px] text-indigo-300 truncate">{username ? `@${username}` : designation}</p>
            </div>
          </div>
          <User className="w-4 h-4 text-indigo-300 group-hover:text-white shrink-0" />
        </div>

        {/* Guru ID Badge with Copy */}
        {guruId && (
          <div
            onClick={handleCopyGuruId}
            className="flex items-center justify-between bg-indigo-900/90 hover:bg-indigo-800/90 px-2.5 py-1.5 rounded-xl border border-indigo-700/60 transition-colors"
            title="Click to copy your Universal Guru ID"
          >
            <div className="flex items-center space-x-1.5">
              <span className="text-[9px] uppercase tracking-wider text-indigo-300 font-bold">ID:</span>
              <span className="text-[10px] font-mono font-bold text-emerald-300 tracking-wide">{guruId}</span>
            </div>
            <div className="text-indigo-300 hover:text-white">
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
