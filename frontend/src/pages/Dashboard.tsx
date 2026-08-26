import React, { useEffect, useState } from 'react';
import { 
  Users, Mic, FileText, Lightbulb, Star, AlertTriangle, TrendingUp, ChevronRight 
} from 'lucide-react';
import { HeaderCard } from '../components/layout/HeaderCard';
import { MetricCard } from '../components/dashboard/MetricCard';
import { QuickActionsGrid } from '../components/dashboard/QuickActionsGrid';
import type { DashboardSummary, AttentionStudent, ClassInsights } from '../types';
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
  const [attentionList, setAttentionList] = useState<AttentionStudent[]>([]);
  const [insights, setInsights] = useState<ClassInsights | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [sumRes, attRes, insRes] = await Promise.all([
          api.getDashboardSummary(),
          api.getAttentionStudents(),
          api.getClassInsights(),
        ]);
        setSummary(sumRes);
        setAttentionList(attRes);
        setInsights(insRes);
      } catch (err) {
        console.error('Error loading dashboard:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-50 min-h-screen p-8 flex flex-col items-center justify-center text-slate-500">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-xs font-bold text-indigo-700">Loading Guru Yuktha Overview...</p>
      </div>
    );
  }

  return (
    <div className="pb-10 space-y-6">
      {/* Top Header Card */}
      <HeaderCard
        teacherName={teacherName || summary?.teacher_name}
        designation={designation || summary?.designation}
        collegeName={collegeName || summary?.college_name}
        avatarUrl={avatarUrl}
        unreadCount={summary?.unread_notifications_count || 3}
        onOpenProfile={onOpenProfile}
      />

      <div className="space-y-6">
        {/* Title Bar */}
        <div className="flex items-center justify-between px-1">
          <div>
            <h2 className="text-lg md:text-xl font-extrabold text-slate-900">Dashboard Overview</h2>
            <p className="text-xs text-slate-500 font-medium">Class activity status and academic monitoring</p>
          </div>
          <span className="text-xs font-bold text-slate-500 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-xs">
            {summary?.date_str || 'Today, 13 May 2025'}
          </span>
        </div>

        {/* 6 Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 md:gap-4">
          <MetricCard
            title="Total Students"
            count={summary?.total_students || 48}
            statusLabel="View all"
            icon={Users}
            bgColor="bg-purple-100/70"
            iconBgColor="bg-purple-600"
            onClick={() => onOpenAction('students')}
          />
          <MetricCard
            title="Seminars"
            count={`${summary?.seminars_completed || 32} / ${summary?.seminars_total || 48}`}
            statusLabel="Completed"
            icon={Mic}
            bgColor="bg-emerald-100/70"
            iconBgColor="bg-emerald-600"
            onClick={() => onOpenAction('seminar')}
          />
          <MetricCard
            title="Assignments"
            count={`${summary?.assignments_completed || 38} / ${summary?.assignments_total || 48}`}
            statusLabel="Completed"
            icon={FileText}
            bgColor="bg-amber-100/70"
            iconBgColor="bg-amber-600"
            onClick={() => onOpenAction('assignment')}
          />
          <MetricCard
            title="PBL Projects"
            count={`${summary?.pbl_completed || 25} / ${summary?.pbl_total || 48}`}
            statusLabel="In Progress"
            icon={Lightbulb}
            bgColor="bg-sky-100/70"
            iconBgColor="bg-sky-600"
            onClick={() => onOpenAction('pbl')}
          />
          <MetricCard
            title="PGL Activities"
            count={`${summary?.pgl_completed || 30} / ${summary?.pgl_total || 48}`}
            statusLabel="Completed"
            icon={Users}
            bgColor="bg-rose-100/70"
            iconBgColor="bg-rose-600"
            onClick={() => onOpenAction('pgl')}
          />
          <MetricCard
            title="Other Activities"
            count={`${summary?.other_completed || 22} / ${summary?.other_total || 48}`}
            statusLabel="Completed"
            icon={Star}
            bgColor="bg-indigo-100/70"
            iconBgColor="bg-indigo-600"
            onClick={() => onOpenAction('activity')}
          />
        </div>

        {/* Quick Actions Grid */}
        <QuickActionsGrid onOpenAction={onOpenAction} />

        {/* 2-Column Grid on Desktop */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Students Needing Attention */}
          <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-100 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <h3 className="text-base font-bold text-slate-800">Students Needing Attention</h3>
                </div>
                <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full">
                  {attentionList.length} Flagged
                </span>
              </div>

              <div className="space-y-2.5">
                {attentionList.map((st) => (
                  <div
                    key={st.id}
                    onClick={() => onSelectStudent(st.id)}
                    className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 hover:bg-indigo-50/50 border border-slate-100 hover:border-indigo-200 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center space-x-3.5">
                      <div className={`w-10 h-10 rounded-full ${st.avatar_color} font-bold text-xs flex items-center justify-center shadow-xs`}>
                        {st.avatar_initials}
                      </div>
                      <div>
                        <h4 className="text-xs md:text-sm font-bold text-slate-800 group-hover:text-indigo-700 transition-colors">
                          {st.name}
                        </h4>
                        <p className="text-[11px] text-slate-500 font-medium">
                          Roll: {st.roll_number} • {st.pending_reason}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                        st.status === 'CRITICAL' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {st.progress_percentage}%
                      </span>
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Class Progress Insights */}
          <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-100 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                  <h3 className="text-base font-bold text-slate-800">Class Progress Insights</h3>
                </div>
                <span className="text-sm font-extrabold text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
                  {insights?.overall_progress || 76}% Overall
                </span>
              </div>

              <div className="space-y-4">
                {[
                  { label: 'Attendance Rate', pct: insights?.attendance_rate || 82, color: 'bg-emerald-500' },
                  { label: 'Assignments Submitted', pct: insights?.assignments_rate || 84, color: 'bg-amber-500' },
                  { label: 'Seminars Completed', pct: insights?.seminars_rate || 71, color: 'bg-purple-500' },
                  { label: 'PBL Projects Active', pct: insights?.pbl_rate || 62, color: 'bg-sky-500' },
                  { label: 'PGL Participation', pct: insights?.pgl_rate || 79, color: 'bg-rose-500' },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between text-xs font-bold text-slate-700 mb-1.5">
                      <span>{item.label}</span>
                      <span>{item.pct}%</span>
                    </div>
                    <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${item.color} rounded-full transition-all duration-500`}
                        style={{ width: `${item.pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
