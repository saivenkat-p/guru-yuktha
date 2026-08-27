import React from 'react';
import { GraduationCap, Sparkles, BookOpen, Compass, CheckCircle2, LogOut, User, Building, Shield } from 'lucide-react';
import type { LearnerProfile, User as UserType } from '../types';

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
              <span>Phase 1 Authentication Activated</span>
            </div>
            <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight">
              Welcome to Guru Yuktha, {user.full_name}
            </h1>
            <p className="text-sm md:text-base text-slate-300 leading-relaxed">
              Your independent Learner account is now active. Guru Yuktha connects you with verified academic mentors, structured learning rooms, and activity tracking.
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

        {/* Phase Roadmap Preview */}
        <div className="bg-slate-800/40 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Upcoming Learning Features</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Guru Yuktha is rolling out in structured phases as per the product blueprint.
              </p>
            </div>
            <span className="px-3 py-1 bg-slate-700/50 text-slate-300 text-xs font-bold rounded-lg border border-slate-600/50">
              Phase 1 Completed
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
                <Compass className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-white">Room Discovery</h4>
              <p className="text-[11px] text-slate-400">
                Discover teacher rooms and public learning spaces with open educational resources.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center">
                <BookOpen className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-white">Organized Content</h4>
              <p className="text-[11px] text-slate-400">
                Browse academic folders, notes, study guides, and reference documents by subject.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-white">Tracking &amp; Submissions</h4>
              <p className="text-[11px] text-slate-400">
                Request tracking from teachers, submit seminar &amp; project evidence for verification.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
                <Sparkles className="w-4 h-4" />
              </div>
              <h4 className="text-xs font-bold text-white">Verified Progress</h4>
              <p className="text-[11px] text-slate-400">
                View real-time, explainable verified progress metrics across all your active learning rooms.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        Guru Yuktha — Academic Navigation &amp; Tracking Platform
      </footer>
    </div>
  );
};
