import React, { useEffect, useState } from 'react';
import { BookOpen, Plus, Users, Copy, Check, Lock, Globe, Archive, ChevronRight, Compass, IndianRupee, Clock } from 'lucide-react';
import { api } from '../services/api';
import type { Room, RoomMembership } from '../types';
import { CreateRoomModal } from '../components/forms/CreateRoomModal';
import { RoomDetail } from './RoomDetail';

interface RoomsProps {
  onNavigateToDiscover?: () => void;
}

export const Rooms: React.FC<RoomsProps> = ({ onNavigateToDiscover }) => {
  const [activeTab, setActiveTab] = useState<'OWNED' | 'JOINED'>('OWNED');
  const [ownedRooms, setOwnedRooms] = useState<Room[]>([]);
  const [memberships, setMemberships] = useState<RoomMembership[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [roomsData, membershipsData] = await Promise.all([
        api.getRooms().catch(() => []),
        api.getMyMemberships().catch(() => []),
      ]);
      setOwnedRooms(roomsData);
      setMemberships(membershipsData);
    } catch (err) {
      console.error('Failed to load rooms:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleArchive = async (roomId: number) => {
    if (!window.confirm('Are you sure you want to archive this room?')) return;
    try {
      await api.archiveRoom(roomId);
      fetchData();
    } catch (err) {
      console.error('Failed to archive room:', err);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-50 min-h-[60vh] p-8 flex flex-col items-center justify-center text-slate-500">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-xs font-bold text-indigo-700">Loading Academic Spaces...</p>
      </div>
    );
  }

  if (selectedRoomId !== null) {
    return (
      <RoomDetail
        roomId={selectedRoomId}
        onBack={() => {
          setSelectedRoomId(null);
          fetchData();
        }}
      />
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-100 shadow-xs">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/30">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black text-slate-900 tracking-tight">Knowledge Rooms</h1>
            <p className="text-xs text-slate-500 font-medium">Manage your teaching spaces &amp; access your learning circles</p>
          </div>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center justify-center space-x-1.5 cursor-pointer shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Create Room</span>
        </button>
      </div>

      {/* Dual Context Tabs (Teaching vs Learning) */}
      <div className="flex items-center space-x-3 border-b border-slate-200 pb-3">
        <button
          onClick={() => setActiveTab('OWNED')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 ${
            activeTab === 'OWNED'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <span>Rooms I Own (Teaching)</span>
          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono ${
            activeTab === 'OWNED' ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'
          }`}>
            {ownedRooms.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('JOINED')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-2 ${
            activeTab === 'JOINED'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <span>Rooms I Joined (Learning)</span>
          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono ${
            activeTab === 'JOINED' ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'
          }`}>
            {memberships.length}
          </span>
        </button>
      </div>

      {/* TAB 1: Rooms I Own */}
      {activeTab === 'OWNED' && (
        <>
          {ownedRooms.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-100 p-12 text-center space-y-4 max-w-lg mx-auto shadow-xs">
              <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                <BookOpen className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-800">No rooms created yet</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  As a Guru, create your first knowledge room to share lectures, materials, host activities, and build your Shishya network.
                </p>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="inline-flex items-center space-x-1.5 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition-all cursor-pointer shadow-md"
              >
                <Plus className="w-4 h-4" />
                <span>Create Knowledge Room</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {ownedRooms.map((room) => (
                <div
                  key={room.id}
                  className="bg-white rounded-3xl border border-slate-100 p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-5"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider flex items-center space-x-1 ${
                          room.access_type === 'PUBLIC_FREE' || room.visibility === 'PUBLIC'
                            ? 'bg-emerald-50 text-emerald-700'
                            : room.access_type === 'PRIVATE_PAID'
                            ? 'bg-purple-50 text-purple-700'
                            : 'bg-indigo-50 text-indigo-700'
                        }`}
                      >
                        {room.access_type === 'PUBLIC_FREE' || room.visibility === 'PUBLIC' ? (
                          <>
                            <Globe className="w-3 h-3" />
                            <span>Free Public</span>
                          </>
                        ) : room.access_type === 'PRIVATE_PAID' ? (
                          <>
                            <IndianRupee className="w-3 h-3" />
                            <span>Paid (₹{room.price})</span>
                          </>
                        ) : (
                          <>
                            <Lock className="w-3 h-3" />
                            <span>Free Private</span>
                          </>
                        )}
                      </span>

                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => handleCopyCode(room.code)}
                          title="Copy Room Code"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors cursor-pointer"
                        >
                          {copiedCode === room.code ? (
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <button
                          onClick={() => handleArchive(room.id)}
                          title="Archive Room"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                        >
                          <Archive className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-slate-900 leading-snug line-clamp-1">{room.name}</h3>
                      <p className="text-xs text-slate-500 font-mono mt-0.5 font-bold">CODE: {room.code}</p>
                    </div>

                    {room.description && (
                      <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{room.description}</p>
                    )}
                  </div>

                  <div className="space-y-3 pt-3 border-t border-slate-100">
                    <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                      <div className="flex items-center space-x-1.5">
                        <Users className="w-4 h-4 text-indigo-600" />
                        <span>{room.active_members_count} Active Members</span>
                      </div>
                      <span className="text-[10px] bg-slate-100 px-2 py-0.5 rounded-md font-bold text-slate-700">
                        OWNER
                      </span>
                    </div>

                    <button
                      onClick={() => setSelectedRoomId(room.id)}
                      className="w-full py-2.5 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-1 cursor-pointer"
                    >
                      <span>Manage Workspace</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* TAB 2: Rooms I Joined */}
      {activeTab === 'JOINED' && (
        <>
          {memberships.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-100 p-12 text-center space-y-4 max-w-lg mx-auto shadow-xs">
              <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                <Compass className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-800">Not enrolled in any rooms yet</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  Explore universal knowledge rooms to learn from Gurus across topics and request admission.
                </p>
              </div>
              {onNavigateToDiscover && (
                <button
                  onClick={onNavigateToDiscover}
                  className="inline-flex items-center space-x-1.5 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition-all cursor-pointer shadow-md"
                >
                  <Compass className="w-4 h-4" />
                  <span>Discover Knowledge Rooms</span>
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {memberships.map((m) => {
                const r = m.room;
                if (!r) return null;
                const isPending = m.status === 'PENDING';
                return (
                  <div
                    key={m.id}
                    className="bg-white rounded-3xl border border-slate-100 p-6 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-5"
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider flex items-center space-x-1 ${
                            isPending
                              ? 'bg-amber-50 text-amber-700'
                              : 'bg-emerald-50 text-emerald-700'
                          }`}
                        >
                          {isPending ? (
                            <>
                              <Clock className="w-3 h-3" />
                              <span>Request Pending</span>
                            </>
                          ) : (
                            <>
                              <Check className="w-3 h-3" />
                              <span>Active Member</span>
                            </>
                          )}
                        </span>

                        <span className="text-[11px] font-mono text-slate-400 font-bold">{r.code}</span>
                      </div>

                      <div>
                        <h3 className="text-base font-bold text-slate-900 leading-snug line-clamp-1">{r.name}</h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Guru: <span className="font-bold text-slate-700">{r.owner_name || 'Room Owner'}</span>
                          {r.owner_guru_id && (
                            <span className="text-[10px] font-mono font-bold text-indigo-600 ml-1">
                              ({r.owner_guru_id})
                            </span>
                          )}
                        </p>
                      </div>

                      {r.description && (
                        <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{r.description}</p>
                      )}
                    </div>

                    <div className="pt-3 border-t border-slate-100">
                      {isPending ? (
                        <div className="p-2.5 bg-amber-50/70 border border-amber-200 rounded-xl text-center text-[11px] font-medium text-amber-800">
                          Awaiting Guru approval. Content will unlock once accepted.
                        </div>
                      ) : (
                        <button
                          onClick={() => setSelectedRoomId(r.id)}
                          className="w-full py-2.5 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-1 cursor-pointer"
                        >
                          <span>Enter Learning Room</span>
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      <CreateRoomModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
};
