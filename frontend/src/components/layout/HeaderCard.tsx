import React, { useState } from 'react';
import { Bell, Menu, Copy, Check, Sparkles } from 'lucide-react';

interface HeaderCardProps {
  teacherName?: string;
  designation?: string;
  collegeName?: string;
  avatarUrl?: string;
  unreadCount?: number;
  guruId?: string;
  username?: string;
  onOpenProfile?: () => void;
}

export const HeaderCard: React.FC<HeaderCardProps> = ({
  teacherName = "Universal Member",
  designation = "Universal Member",
  collegeName = "Guru Yuktha Network",
  avatarUrl = "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
  unreadCount = 0,
  guruId,
  username,
  onOpenProfile,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyGuruId = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!guruId) return;
    navigator.clipboard.writeText(guruId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-gradient-to-r from-indigo-700 via-indigo-600 to-purple-700 text-white p-5 rounded-2xl md:rounded-3xl shadow-lg relative">
      <div className="flex items-center justify-between mb-4 md:mb-6">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center md:hidden">
            <Menu className="w-5 h-5 text-white" />
          </div>
          <span className="text-xs md:text-sm font-semibold text-indigo-100 uppercase tracking-wider flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Guru Yuktha • Universal Member Workspace</span>
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <div className="relative">
            <button className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors relative">
              <Bell className="w-5 h-5 text-white" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center border border-indigo-700">
                  {unreadCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4 md:space-x-6">
        <div className="relative cursor-pointer group" onClick={onOpenProfile}>
          <img
            src={avatarUrl}
            alt={teacherName}
            className="w-14 h-14 md:w-20 md:h-20 rounded-2xl md:rounded-3xl border-2 border-white/80 object-cover shadow-md group-hover:scale-105 transition-transform"
          />
          <span className="absolute -bottom-1 -right-1 bg-white text-indigo-700 p-1 rounded-full text-[10px] font-bold shadow-xs group-hover:bg-indigo-50">
            ✏️
          </span>
        </div>

        <div className="cursor-pointer" onClick={onOpenProfile}>
          <span className="text-xs uppercase tracking-wider text-indigo-200 font-medium">Welcome back,</span>
          <h1 className="text-lg md:text-2xl font-extrabold text-white leading-tight hover:underline">{teacherName}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-1">
            {username && (
              <span className="text-xs font-semibold text-indigo-200 bg-white/10 px-2 py-0.5 rounded-md">
                @{username}
              </span>
            )}
            {guruId && (
              <button
                type="button"
                onClick={handleCopyGuruId}
                className="inline-flex items-center space-x-1.5 text-xs font-mono font-bold text-emerald-300 bg-indigo-950/70 hover:bg-indigo-950 px-2.5 py-0.5 rounded-md border border-indigo-500/40 transition-colors cursor-pointer"
                title="Click to copy Guru ID"
              >
                <span>ID: {guruId}</span>
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-indigo-300" />}
              </button>
            )}
          </div>
          <p className="text-xs text-indigo-200/90 font-medium mt-1">{collegeName}</p>
        </div>
      </div>
    </div>
  );
};
