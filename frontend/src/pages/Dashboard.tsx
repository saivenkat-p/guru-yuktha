import React, { useEffect, useState } from 'react';
import { 
  Users, Sparkles, FileText, BookOpen, Plus, Calendar, Award, ChevronRight, CheckCircle2, Clock
} from 'lucide-react';
import { HeaderCard } from '../components/layout/HeaderCard';
import { CreateRoomModal } from '../components/forms/CreateRoomModal';
import { AddActivityModal } from '../components/forms/AddActivityModal';
import type { DashboardSummary, AttentionStudent, ClassInsights, Room, Activity } from '../types';
import { api } from '../services/api';

interface DashboardProps {
  onOpenAction: (action: string) => void;
  onSelectStudent: (studentId: number) => void;
  onOpenProfile?: () => void;
  avatarUrl?: string;
  teacherName?: string;
  designation?: string;
  collegeName?: string;
}

export const Dashboard: React.FC<DashboardProps> = ({
  onOpenAction,
  onSelectStudent,
  onOpenProfile,
  avatarUrl,
  teacherName,
  designation,
  collegeName,
}) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [isCreateRoomOpen, setIsCreateRoomOpen] = useState(false);
  const [isAddActivityOpen, setIsAddActivityOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [sumRes, actRes, roomsRes] = await Promise.all([
        api.getDashboardSummary().catch(() => null),
        api.getActivities().catch(() => []),
        api.getRooms().catch(() => []),
      ]);
      setSummary(sumRes);
      setActivities(actRes);
      setRooms(roomsRes);
    } catch (err) {
      console.error('Error loading dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getActivityTypeBadge = (type: string) => {
    const t = type?.toUpperCase() || 'ACTIVITY';
    switch (t) {
      case 'ASSIGNMENT':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'SEMINAR':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'PROJECT':
      case 'PBL':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      case 'ASSESSMENT':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-50 min-h-[60vh] p-8 flex flex-col items-center justify-center text-slate-500">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-xs font-bold text-indigo-700">Loading Guru Yuktha Overview...</p>
      </div>
    );
  }

  return (
    <div className="pb-12 space-y-6">
      {/* Top Header Card */}
      <HeaderCard
        teacherName={teacherName || summary?.teacher_name || 'Faculty Member'}
        designation={designation || summary?.designation || 'Faculty'}
        collegeName={collegeName || summary?.college_name || 'Academic Institution'}
        avatarUrl={avatarUrl}
        unreadCount={summary?.unread_notifications_count || 0}
        onOpenProfile={onOpenProfile}
      />

      <div className="space-y-6">
        {/* Title Bar */}
        <div className="flex items-center justify-between px-1">
          <div>
            <h2 className="text-lg md:text-xl font-extrabold text-slate-900">Academic Workspace</h2>
            <p className="text-xs text-slate-500 font-medium">Manage learning activities, assignments, and tracked rooms</p>
          </div>
          <span className="text-xs font-bold text-slate-500 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-xs">
            {summary?.date_str || `Today, ${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}`}
          </span>
        </div>

        {/* Real Teacher Activities Section (Phase 4) */}
        <div className="bg-white p-6 rounded-3xl shadow-xs border border-slate-100 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-800">Academic Activities</h3>
                <p className="text-xs text-slate-500 font-medium">Assignments, seminars, projects, and assessments</p>
              </div>
            </div>

            <button
              onClick={() => setIsAddActivityOpen(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center space-x-1.5 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Add Activity</span>
            </button>
          </div>

          {activities.length === 0 ? (
            <div className="py-10 px-4 bg-slate-50 rounded-2xl border border-slate-100 text-center space-y-3 max-w-lg mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-indigo-100/60 text-indigo-600 flex items-center justify-center mx-auto">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-800">No activities yet</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto leading-relaxed">
                  Create assignments, seminars, projects, or assessments to track student learning and progress.
                </p>
              </div>
              <button
                onClick={() => setIsAddActivityOpen(true)}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md inline-flex items-center space-x-1.5 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Create Your First Activity</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
              {activities.map((act) => (
                <div
                  key={act.id}
                  className="p-5 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:border-indigo-200 transition-all space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-extrabold uppercase tracking-wider border ${getActivityTypeBadge(act.type)}`}>
                        {act.type}
                      </span>
                      {act.status === 'COMPLETED' ? (
                        <span className="flex items-center space-x-1 text-[11px] text-emerald-600 font-bold">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Completed</span>
                        </span>
                      ) : (
                        <span className="flex items-center space-x-1 text-[11px] text-amber-600 font-bold">
                          <Clock className="w-3.5 h-3.5" />
                          <span>In Progress</span>
                        </span>
                      )}
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-slate-900 line-clamp-1">{act.title}</h4>
                      {act.description && (
                        <p className="text-xs text-slate-500 mt-0.5 line-clamp-2 leading-relaxed">
                          {act.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    {act.room_name ? (
                      <span className="inline-flex items-center space-x-1 text-indigo-600 font-semibold truncate max-w-[130px]">
                        <BookOpen className="w-3 h-3" />
                        <span className="truncate">{act.room_name}</span>
                      </span>
                    ) : (
                      <span>General</span>
                    )}

                    {act.due_date && (
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        <span>Due: {act.due_date}</span>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* My Learning Rooms (Phase 2) */}
        <div className="bg-white p-6 rounded-3xl shadow-xs border border-slate-100 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-800">My Learning Rooms</h3>
                <p className="text-xs text-slate-500 font-medium">Structured academic spaces and tracked learners</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsCreateRoomOpen(true)}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center space-x-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Room</span>
              </button>
              <button
                onClick={() => onOpenAction('rooms')}
                className="px-3 py-1.5 text-xs font-bold text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors cursor-pointer"
              >
                View all
              </button>
            </div>
          </div>

          {rooms.length === 0 ? (
            <div className="p-6 bg-slate-50 rounded-2xl border border-slate-100 text-center space-y-2 max-w-lg mx-auto">
              <p className="text-xs font-semibold text-slate-700">No rooms yet.</p>
              <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                Create learning rooms to organize your folders, materials, and tracked students.
              </p>
              <button
                onClick={() => setIsCreateRoomOpen(true)}
                className="mt-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all inline-flex items-center space-x-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create Room</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {rooms.slice(0, 3).map((r) => (
                <div key={r.id} className="p-4 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:border-indigo-200 transition-all space-y-2">
                  <div className="flex items-start justify-between">
                    <h4 className="text-xs font-bold text-slate-800 line-clamp-1">{r.name}</h4>
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                      {r.code}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium pt-1">
                    <span className="flex items-center space-x-1">
                      <Users className="w-3 h-3 text-indigo-500" />
                      <span>{r.active_members_count} Tracked</span>
                    </span>
                    <span className="capitalize text-slate-400">{r.visibility.toLowerCase()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <CreateRoomModal
        isOpen={isCreateRoomOpen}
        onClose={() => setIsCreateRoomOpen(false)}
        onSuccess={loadData}
      />

      <AddActivityModal
        isOpen={isAddActivityOpen}
        onClose={() => setIsAddActivityOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
};
