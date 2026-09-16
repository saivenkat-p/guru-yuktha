import React, { useState, useEffect } from 'react';
import { Search, Users, BookOpen, FileText, UserPlus, UserCheck, Copy, Check, Lock, Globe, ExternalLink, Sparkles, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import type { UniversalSearchResult } from '../types';

interface DiscoverProps {
  onSelectRoom?: (roomId: number) => void;
}

export const Discover: React.FC<DiscoverProps> = ({ onSelectRoom }) => {
  const [query, setQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'GURUS' | 'ROOMS' | 'RESOURCES'>('ALL');
  const [results, setResults] = useState<UniversalSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [followingMap, setFollowingMap] = useState<Record<string, boolean>>({});

  const performSearch = async (searchTerm: string) => {
    if (!searchTerm.trim()) {
      setResults(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.searchUniversal(searchTerm.trim());
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    performSearch('a');
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  const handleCopyGuruId = (guruId: string) => {
    navigator.clipboard.writeText(guruId);
    setCopiedId(guruId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleToggleFollow = async (identifier: string) => {
    const currentlyFollowing = !!followingMap[identifier];
    try {
      if (currentlyFollowing) {
        await api.unfollowMember(identifier);
        setFollowingMap((prev) => ({ ...prev, [identifier]: false }));
      } else {
        await api.followMember(identifier);
        setFollowingMap((prev) => ({ ...prev, [identifier]: true }));
      }
    } catch (err: any) {
      alert(err.message || 'Failed to update follow status');
    }
  };

  const memberList = results?.members || [];
  const roomList = results?.rooms || [];
  const resourceList = results?.resources || [];

  return (
    <div className="space-y-6 pb-16">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-purple-900 p-6 sm:p-8 rounded-3xl text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-white/10 rounded-full text-xs font-semibold text-indigo-200 backdrop-blur-md mb-3">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Connect • Learn • Teach • Grow</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">Universal Knowledge Discovery</h1>
          <p className="text-xs sm:text-sm text-indigo-100/90 mt-1 font-medium">
            Search for Gurus by name, username, or Guru ID (GY-...), explore open knowledge rooms, and discover learning resources.
          </p>

          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="mt-5 relative flex items-center">
            <Search className="w-5 h-5 text-slate-400 absolute left-4" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search Gurus (@username, GY-...), Rooms, or Topics..."
              className="w-full bg-white text-slate-900 rounded-2xl pl-12 pr-28 py-3.5 text-sm font-medium focus:outline-none focus:ring-4 focus:ring-purple-400/40 shadow-lg"
            />
            <button
              type="submit"
              className="absolute right-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-3 overflow-x-auto">
        <button
          onClick={() => setActiveFilter('ALL')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeFilter === 'ALL'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          All Results
        </button>
        <button
          onClick={() => setActiveFilter('GURUS')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-1.5 ${
            activeFilter === 'GURUS'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Gurus ({memberList.length})</span>
        </button>
        <button
          onClick={() => setActiveFilter('ROOMS')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-1.5 ${
            activeFilter === 'ROOMS'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Rooms ({roomList.length})</span>
        </button>
        <button
          onClick={() => setActiveFilter('RESOURCES')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-1.5 ${
            activeFilter === 'RESOURCES'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Resources ({resourceList.length})</span>
        </button>
      </div>

      {loading && (
        <div className="p-12 text-center text-slate-500">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-bold text-indigo-700">Searching Universal Knowledge Network...</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center space-x-3 text-rose-700 text-xs font-medium">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!loading && results && (
        <div className="space-y-8">
          {/* Gurus Section */}
          {(activeFilter === 'ALL' || activeFilter === 'GURUS') && memberList.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-black text-slate-900 uppercase tracking-wider flex items-center space-x-2">
                  <Users className="w-4 h-4 text-indigo-600" />
                  <span>Gurus &amp; Members</span>
                </h2>
                <span className="text-xs text-slate-500 font-medium">{memberList.length} found</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {memberList.map((m) => {
                  const isFollowing = !!followingMap[m.username || m.guru_id];
                  return (
                    <div
                      key={m.id}
                      className="bg-white p-5 rounded-3xl border border-slate-100 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between space-y-4"
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center space-x-3 min-w-0">
                            <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center font-black text-indigo-700 text-base shrink-0 overflow-hidden">
                              {m.avatar_url ? (
                                <img src={m.avatar_url} alt={m.full_name} className="w-full h-full object-cover" />
                              ) : (
                                m.full_name.charAt(0).toUpperCase()
                              )}
                            </div>
                            <div className="min-w-0">
                              <h3 className="text-sm font-bold text-slate-900 truncate">{m.full_name}</h3>
                              <p className="text-xs text-slate-500 font-medium">@{m.username}</p>
                            </div>
                          </div>

                          <button
                            onClick={() => handleToggleFollow(m.username || m.guru_id)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center space-x-1 cursor-pointer transition-all ${
                              isFollowing
                                ? 'bg-indigo-50 text-indigo-700 hover:bg-rose-50 hover:text-rose-700'
                                : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs'
                            }`}
                          >
                            {isFollowing ? (
                              <>
                                <UserCheck className="w-3.5 h-3.5" />
                                <span>Following</span>
                              </>
                            ) : (
                              <>
                                <UserPlus className="w-3.5 h-3.5" />
                                <span>Follow</span>
                              </>
                            )}
                          </button>
                        </div>

                        {/* Guru ID pill */}
                        <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-[11px] font-mono text-slate-700">
                          <span className="text-slate-400 font-sans text-[10px] font-bold">GURU ID:</span>
                          <span className="font-bold text-indigo-600">{m.guru_id}</span>
                          <button
                            onClick={() => handleCopyGuruId(m.guru_id)}
                            className="text-slate-400 hover:text-slate-700 cursor-pointer ml-1"
                            title="Copy Guru ID"
                          >
                            {copiedId === m.guru_id ? (
                              <Check className="w-3 h-3 text-emerald-600" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>

                        {m.bio && (
                          <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{m.bio}</p>
                        )}
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-3 border-t border-slate-100">
                        <span>{m.followers_count} Shishya/Followers</span>
                        <span>{m.rooms_owned_count} Rooms Owned</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Rooms Section */}
          {(activeFilter === 'ALL' || activeFilter === 'ROOMS') && roomList.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-black text-slate-900 uppercase tracking-wider flex items-center space-x-2">
                  <BookOpen className="w-4 h-4 text-indigo-600" />
                  <span>Knowledge Rooms</span>
                </h2>
                <span className="text-xs text-slate-500 font-medium">{roomList.length} found</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {roomList.map((r) => (
                  <div
                    key={r.id}
                    className="bg-white p-5 rounded-3xl border border-slate-100 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between space-y-4"
                  >
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider flex items-center space-x-1 ${
                            r.access_type === 'PUBLIC_FREE'
                              ? 'bg-emerald-50 text-emerald-700'
                              : 'bg-amber-50 text-amber-700'
                          }`}
                        >
                          {r.access_type === 'PUBLIC_FREE' ? (
                            <>
                              <Globe className="w-3 h-3" />
                              <span>Free Public</span>
                            </>
                          ) : (
                            <>
                              <Lock className="w-3 h-3" />
                              <span>Free Private (Join Request)</span>
                            </>
                          )}
                        </span>
                        <span className="text-[11px] font-mono font-bold text-slate-400">{r.code}</span>
                      </div>

                      <h3 className="text-base font-bold text-slate-900 leading-snug">{r.name}</h3>

                      {r.description && (
                        <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{r.description}</p>
                      )}

                      <div className="text-xs text-slate-600 font-medium">
                        Guru: <span className="font-bold text-slate-800">{r.owner_name}</span>
                        {r.owner_guru_id && (
                          <span className="ml-1 text-[10px] text-indigo-600 font-mono font-bold">
                            ({r.owner_guru_id})
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => onSelectRoom?.(r.id)}
                      className="w-full py-2.5 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white rounded-xl text-xs font-bold transition-colors flex items-center justify-center space-x-1.5 cursor-pointer"
                    >
                      <span>View &amp; Preview Room</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Resources Section */}
          {(activeFilter === 'ALL' || activeFilter === 'RESOURCES') && resourceList.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-black text-slate-900 uppercase tracking-wider flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <span>Public Learning Resources</span>
                </h2>
                <span className="text-xs text-slate-500 font-medium">{resourceList.length} found</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {resourceList.map((res) => (
                  <div
                    key={res.id}
                    className="bg-white p-5 rounded-3xl border border-slate-100 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between space-y-3"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-[10px] text-slate-400 font-bold uppercase">
                        <span>{res.resource_type}</span>
                        <span className="text-indigo-600">{res.room_name}</span>
                      </div>
                      <h3 className="text-sm font-bold text-slate-900 leading-snug">{res.title}</h3>
                      {res.description && (
                        <p className="text-xs text-slate-500 line-clamp-2">{res.description}</p>
                      )}
                    </div>

                    {(res.file_url || res.external_url) && (
                      <a
                        href={res.file_url || res.external_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center justify-center space-x-1 py-2 text-xs font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 rounded-xl transition-colors cursor-pointer"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Open Resource</span>
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {memberList.length === 0 && roomList.length === 0 && resourceList.length === 0 && (
            <div className="p-12 text-center text-slate-400 bg-white rounded-3xl border border-slate-100 max-w-md mx-auto">
              <Search className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="text-sm font-bold text-slate-700">No results found</p>
              <p className="text-xs text-slate-500 mt-1">Try searching for a different name, username, or Guru ID.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
