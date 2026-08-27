import React, { useEffect, useState } from 'react';
import { 
  GraduationCap, Sparkles, BookOpen, Compass, CheckCircle2, LogOut, User, Building, 
  Shield, Lock, Globe, Search, FileText, FileCode, Video, Image, File, ExternalLink, Filter 
} from 'lucide-react';
import type { LearnerProfile, User as UserType, RoomMembership, Resource } from '../types';
import { api } from '../services/api';

interface LearnerDashboardProps {
  user: UserType;
  learnerProfile?: LearnerProfile | null;
  onLogout: () => void;
}

export const LearnerDashboard: React.FC<LearnerDashboardProps> = ({
  user,
  learnerProfile,
  onLogout,
}) => {
  const [memberships, setMemberships] = useState<RoomMembership[]>([]);
  const [loadingRooms, setLoadingRooms] = useState(true);

  // Public Resources state
  const [publicResources, setPublicResources] = useState<Resource[]>([]);
  const [loadingResources, setLoadingResources] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('ALL');

  useEffect(() => {
    async function loadMemberships() {
      try {
        const data = await api.getMyMemberships();
        setMemberships(data);
      } catch (err) {
        console.error('Error fetching learner memberships:', err);
      } finally {
        setLoadingRooms(false);
      }
    }
    loadMemberships();
  }, []);

  const loadPublicResources = async () => {
    setLoadingResources(true);
    try {
      const data = await api.getPublicResources({
        search: searchQuery || undefined,
        resource_type: selectedType !== 'ALL' ? selectedType : undefined,
      });
      setPublicResources(data);
    } catch (err) {
      console.error('Error fetching public resources:', err);
    } finally {
      setLoadingResources(false);
    }
  };

  useEffect(() => {
    loadPublicResources();
  }, [searchQuery, selectedType]);

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'PDF':
      case 'DOC':
        return <FileText className="w-5 h-5 text-indigo-400" />;
      case 'PPT':
        return <FileCode className="w-5 h-5 text-amber-400" />;
      case 'VIDEO':
        return <Video className="w-5 h-5 text-rose-400" />;
      case 'IMAGE':
        return <Image className="w-5 h-5 text-emerald-400" />;
      case 'LINK':
        return <ExternalLink className="w-5 h-5 text-sky-400" />;
      default:
        return <File className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-base text-white tracking-tight">Guru Yuktha</span>
              <span className="ml-2 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-md">
                Learner
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-bold text-white">{user.full_name}</span>
              <span className="text-[11px] text-slate-400 font-mono">{learnerProfile?.learner_id || user.email}</span>
            </div>
            <button
              onClick={onLogout}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors flex items-center space-x-1.5 text-xs font-semibold cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 md:py-12 space-y-8">
        {/* Welcome Hero Banner */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900/60 via-purple-900/40 to-slate-900 border border-indigo-500/20 p-6 md:p-10 shadow-2xl">
          <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="relative z-10 max-w-3xl space-y-4">
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-full text-indigo-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Academic Workspace Active</span>
            </div>
            <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight">
              Welcome to Guru Yuktha, {user.full_name}
            </h1>
            <p className="text-sm md:text-base text-slate-300 leading-relaxed">
              Explore public educational resources, organize your study materials, and access your enrolled academic learning rooms.
            </p>
          </div>
        </div>

        {/* Learner Identity Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 space-y-4">
            <div className="flex items-center space-x-2 text-indigo-400">
              <Shield className="w-5 h-5" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">Platform Identity</h2>
            </div>
            <div>
              <span className="text-xs text-slate-400">Unique Learner ID</span>
              <p className="text-lg font-mono font-bold text-white tracking-wide mt-0.5">
                {learnerProfile?.learner_id || 'Generating ID...'}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">
                Share this ID with teachers to receive invitations to tracked learning rooms.
              </p>
            </div>
          </div>

          <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 space-y-4">
            <div className="flex items-center space-x-2 text-purple-400">
              <User className="w-5 h-5" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">Account Details</h2>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Email:</span>
                <span className="text-white font-medium">{user.email}</span>
              </div>
              {learnerProfile?.course && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Program:</span>
                  <span className="text-white font-medium">{learnerProfile.course}</span>
                </div>
              )}
              {learnerProfile?.semester && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Semester:</span>
                  <span className="text-white font-medium">{learnerProfile.semester}</span>
                </div>
              )}
              {learnerProfile?.roll_number && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Roll No:</span>
                  <span className="text-white font-medium">{learnerProfile.roll_number}</span>
                </div>
              )}
            </div>
          </div>

          <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-5 space-y-4">
            <div className="flex items-center space-x-2 text-emerald-400">
              <Building className="w-5 h-5" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">Academic Institution</h2>
            </div>
            <div>
              <span className="text-xs text-slate-400">College / Institution</span>
              <p className="text-sm font-semibold text-white mt-0.5">
                {learnerProfile?.college_name || 'Not specified'}
              </p>
              {learnerProfile?.department && (
                <p className="text-xs text-slate-400 mt-1">
                  Department of {learnerProfile.department}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Public Learning Resources Discovery (Phase 3) */}
        <div className="bg-slate-800/40 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <Globe className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Public Learning Resources</h3>
                <p className="text-xs text-slate-400">
                  Open syllabus notes, lectures, and study guides (Viewing does not create tracking relationships)
                </p>
              </div>
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search resources..."
                className="w-full bg-slate-900/80 border border-slate-700 rounded-xl pl-9 pr-3.5 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-2">
            {['ALL', 'PDF', 'PPT', 'DOC', 'VIDEO', 'LINK', 'IMAGE'].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  selectedType === t
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'bg-slate-800/80 text-slate-400 hover:bg-slate-800 hover:text-white border border-slate-700/60'
                }`}
              >
                {t === 'ALL' ? 'All Types' : t}
              </button>
            ))}
          </div>

          {/* Resources Grid */}
          {loadingResources ? (
            <div className="p-8 text-center text-xs text-slate-400">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Loading open learning resources...
            </div>
          ) : publicResources.length === 0 ? (
            <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-2">
              <p className="text-xs font-bold text-slate-300">No public learning resources yet.</p>
              <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                Open educational resources published by academic mentors will be discoverable here without enrolling you in tracked classes.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {publicResources.map((res) => (
                <div
                  key={res.id}
                  className="p-5 bg-slate-900/70 border border-slate-800 rounded-2xl space-y-3 flex flex-col justify-between hover:border-slate-700 transition-all"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
                          {getResourceIcon(res.resource_type)}
                        </div>
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                          {res.resource_type}
                        </span>
                      </div>

                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
                        <Globe className="w-3 h-3" />
                        <span>Public</span>
                      </span>
                    </div>

                    <div>
                      <h4 className="font-bold text-sm text-white">{res.title}</h4>
                      {res.description && (
                        <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                          {res.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="pt-2.5 border-t border-slate-800 flex items-center justify-between text-[11px]">
                    <div className="truncate max-w-[150px] text-slate-400">
                      {res.room_name && <span>{res.room_name}</span>}
                    </div>

                    {res.file_url && (
                      <a
                        href={res.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2.5 py-1 bg-indigo-600/80 hover:bg-indigo-600 text-white rounded-lg font-bold inline-flex items-center space-x-1 transition-colors"
                      >
                        <ExternalLink className="w-3 h-3" />
                        <span>Access</span>
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* My Enrolled Learning Rooms Section (Phase 2) */}
        <div className="bg-slate-800/40 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">My Enrolled Learning Rooms</h3>
                <p className="text-xs text-slate-400">Tracked academic community spaces</p>
              </div>
            </div>
            <span className="px-3 py-1 bg-slate-700/40 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700/50">
              {memberships.length} {memberships.length === 1 ? 'Room' : 'Rooms'}
            </span>
          </div>

          {loadingRooms ? (
            <div className="p-8 text-center text-xs text-slate-400">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              Loading your rooms...
            </div>
          ) : memberships.length === 0 ? (
            <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-2">
              <p className="text-xs font-bold text-slate-300">No enrolled learning rooms yet.</p>
              <p className="text-[11px] text-slate-400 max-w-md mx-auto">
                You are not currently enrolled or tracked in any private learning rooms. Once teachers invite you with your Learner ID or you join tracked rooms, they will appear here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {memberships.map((m) => (
                <div key={m.id} className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl space-y-3">
                  <div className="flex items-start justify-between">
                    <h4 className="font-bold text-sm text-white">{m.room?.name || 'Room'}</h4>
                    <span className="px-2 py-0.5 bg-indigo-500/20 text-indigo-300 font-mono text-[10px] rounded-md font-bold">
                      {m.room?.code}
                    </span>
                  </div>
                  {m.room?.description && (
                    <p className="text-xs text-slate-400 line-clamp-2">{m.room.description}</p>
                  )}
                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Role: {m.role}</span>
                    <span className="text-emerald-400 font-semibold">{m.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        Guru Yuktha — Academic Navigation &amp; Tracking Platform
      </footer>
    </div>
  );
};
