import React, { useState, useEffect } from 'react';
import { Dashboard } from './pages/Dashboard';
import { Students } from './pages/Students';
import { StudentProfile } from './pages/StudentProfile';
import { Materials } from './pages/Materials';
import { Reports } from './pages/Reports';
import { Rooms } from './pages/Rooms';
import { Discover } from './pages/Discover';
import { Login } from './pages/Login';
import { BottomNav } from './components/layout/BottomNav';
import { DesktopSidebar } from './components/layout/DesktopSidebar';
import { QuickAddMenuModal } from './components/forms/QuickAddMenuModal';
import { AddStudentModal } from './components/forms/AddStudentModal';
import { AddActivityModal } from './components/forms/AddActivityModal';
import { MarkAttendanceModal } from './components/forms/MarkAttendanceModal';
import { AccountProfileModal } from './components/profile/AccountProfileModal';
import type { Student, User, LearnerProfile, UserRole } from './types';
import { api, getAuthToken, removeAuthToken } from './services/api';

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return !!getAuthToken();
  });

  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userRole, setUserRole] = useState<UserRole>('MEMBER');
  const [learnerProfile, setLearnerProfile] = useState<LearnerProfile | null>(null);

  const [activeTab, setActiveTab] = useState<'dashboard' | 'rooms' | 'discover' | 'students' | 'materials' | 'reports'>('dashboard');
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loadingAuth, setLoadingAuth] = useState(true);

  // Universal Member Profile state
  const [teacherProfile, setTeacherProfile] = useState({
    name: 'Universal Member',
    designation: 'Member',
    guruId: '',
    username: '',
    department: 'Knowledge Hub',
    collegeName: 'Guru Yuktha Network',
    employeeCode: '',
    email: '',
    avatarUrl: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
  });

  // Modals
  const [isQuickMenuOpen, setIsQuickMenuOpen] = useState(false);
  const [isAddStudentModalOpen, setIsAddStudentModalOpen] = useState(false);
  const [isAddActivityModalOpen, setIsAddActivityModalOpen] = useState(false);
  const [activityModalType, setActivityModalType] = useState<'seminar' | 'assignment' | 'pbl' | 'pgl' | 'activity'>('seminar');
  const [isAttendanceModalOpen, setIsAttendanceModalOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  const loadInitialData = async () => {
    const token = getAuthToken();
    if (!token) {
      setIsAuthenticated(false);
      setLoadingAuth(false);
      return;
    }

    try {
      const meRes = await api.getMe().catch(() => null);
      if (!meRes || !meRes.user) {
        throw new Error('Unable to authenticate user session');
      }

      setCurrentUser(meRes.user);
      const role = (meRes.role || meRes.user.role || 'MEMBER') as UserRole;
      setUserRole(role);

      if (meRes.learner) {
        setLearnerProfile(meRes.learner);
      }

      // Universal Member setup
      const [studentData] = await Promise.all([
        api.getStudents().catch(() => []),
      ]);

      setStudents(studentData);

      const teacherData = meRes.teacher || meRes;
      setTeacherProfile({
        name: meRes.user.full_name || 'Universal Member',
        designation: teacherData.designation || (meRes.user.is_guru_eligible ? 'Guru / Educator' : 'Universal Member'),
        guruId: meRes.user.guru_id || '',
        username: meRes.user.username || '',
        department: teacherData.department || 'Knowledge Department',
        collegeName: teacherData.college_name || 'Guru Yuktha Network',
        employeeCode: teacherData.employee_code || meRes.user.guru_id || `EMP-${meRes.user.id}`,
        email: meRes.user.email,
        avatarUrl: meRes.user.avatar_url || 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
      });

      setIsAuthenticated(true);
    } catch (err) {
      console.error('Auth verification failed:', err);
      removeAuthToken();
      setIsAuthenticated(false);
    } finally {
      setLoadingAuth(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, [isAuthenticated]);

  const handleAuthSuccess = (_token: string, _user: any) => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    removeAuthToken();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setLearnerProfile(null);
    setSelectedStudentId(null);
    setActiveTab('dashboard');
  };

  const handleSelectStudent = (id: number) => {
    setSelectedStudentId(id);
  };

  const handleOpenAction = (action: string) => {
    if (action === 'add_student') {
      setIsAddStudentModalOpen(true);
    } else if (action === 'seminar') {
      setActivityModalType('seminar');
      setIsAddActivityModalOpen(true);
    } else if (action === 'assignment') {
      setActivityModalType('assignment');
      setIsAddActivityModalOpen(true);
    } else if (action === 'pbl') {
      setActivityModalType('pbl');
      setIsAddActivityModalOpen(true);
    } else if (action === 'pgl') {
      setActivityModalType('pgl');
      setIsAddActivityModalOpen(true);
    } else if (action === 'activity') {
      setActivityModalType('activity');
      setIsAddActivityModalOpen(true);
    } else if (action === 'attendance') {
      setIsAttendanceModalOpen(true);
    } else if (action === 'students') {
      setActiveTab('students');
      setSelectedStudentId(null);
    } else if (action === 'reports') {
      setActiveTab('reports');
    } else if (action === 'material') {
      setActiveTab('materials');
    } else {
      setActivityModalType('seminar');
      setIsAddActivityModalOpen(true);
    }
  };

  const handleProfileUpdateSuccess = (updated: any) => {
    if (updated) {
      setTeacherProfile((prev) => ({
        ...prev,
        name: updated.user?.full_name || prev.name,
        designation: updated.designation || prev.designation,
        guruId: updated.user?.guru_id || prev.guruId,
        username: updated.user?.username || prev.username,
        department: updated.department || prev.department,
        collegeName: updated.college_name || prev.collegeName,
        employeeCode: updated.employee_code || prev.employeeCode,
        email: updated.user?.email || prev.email,
        avatarUrl: updated.user?.avatar_url || prev.avatarUrl,
      }));
    }
  };

  // Route Protection
  if (loadingAuth) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white p-4">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-bold text-indigo-300">Initializing Guru Yuktha Application...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onAuthSuccess={handleAuthSuccess} />;
  }

  const renderCurrentView = () => {
    if (selectedStudentId !== null) {
      return (
        <StudentProfile
          studentId={selectedStudentId}
          onBack={() => {
            setSelectedStudentId(null);
            loadInitialData();
          }}
        />
      );
    }

    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard
            onOpenAction={handleOpenAction}
            onSelectStudent={handleSelectStudent}
            onOpenProfile={() => setIsProfileModalOpen(true)}
            onNavigateToTab={(tab) => setActiveTab(tab)}
            avatarUrl={teacherProfile.avatarUrl}
            teacherName={teacherProfile.name}
            designation={teacherProfile.designation}
            collegeName={teacherProfile.collegeName}
            guruId={teacherProfile.guruId}
            username={teacherProfile.username}
          />
        );
      case 'discover':
        return (
          <Discover
            onSelectRoom={(_roomId) => {
              setActiveTab('rooms');
            }}
          />
        );
      case 'rooms':
        return <Rooms onNavigateToDiscover={() => setActiveTab('discover')} />;
      case 'students':
        return (
          <Students
            onSelectStudent={handleSelectStudent}
            onAddStudent={() => setIsAddStudentModalOpen(true)}
          />
        );
      case 'materials':
        return <Materials onUploadClick={() => handleOpenAction('material')} />;
      case 'reports':
        return <Reports />;
      default:
        return (
          <Dashboard
            onOpenAction={handleOpenAction}
            onSelectStudent={handleSelectStudent}
            onOpenProfile={() => setIsProfileModalOpen(true)}
            onNavigateToTab={(tab) => setActiveTab(tab)}
            avatarUrl={teacherProfile.avatarUrl}
            teacherName={teacherProfile.name}
            designation={teacherProfile.designation}
            collegeName={teacherProfile.collegeName}
            guruId={teacherProfile.guruId}
            username={teacherProfile.username}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex w-full">
      {/* Desktop Navigation Sidebar */}
      <DesktopSidebar
        activeTab={activeTab}
        teacherName={teacherProfile.name}
        designation={teacherProfile.designation}
        guruId={teacherProfile.guruId}
        username={teacherProfile.username}
        avatarUrl={teacherProfile.avatarUrl}
        onSelectTab={(tab) => {
          setSelectedStudentId(null);
          setActiveTab(tab);
        }}
        onOpenQuickAdd={() => setIsQuickMenuOpen(true)}
        onOpenProfile={() => setIsProfileModalOpen(true)}
      />

      {/* Main Full-Width Application Content Container */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
          {renderCurrentView()}
        </main>

        {/* Mobile Bottom Navigation */}
        <div className="md:hidden">
          <BottomNav
            activeTab={activeTab}
            onSelectTab={(tab) => {
              setSelectedStudentId(null);
              setActiveTab(tab);
            }}
            onOpenQuickAdd={() => setIsQuickMenuOpen(true)}
          />
        </div>
      </div>

      {/* Quick Action Selection Modal */}
      <QuickAddMenuModal
        isOpen={isQuickMenuOpen}
        onClose={() => setIsQuickMenuOpen(false)}
        onSelectAction={handleOpenAction}
      />

      {/* Add Student Modal */}
      <AddStudentModal
        isOpen={isAddStudentModalOpen}
        onClose={() => setIsAddStudentModalOpen(false)}
        onSuccess={loadInitialData}
      />

      {/* Add Activity Form Modal */}
      <AddActivityModal
        isOpen={isAddActivityModalOpen}
        initialType={activityModalType}
        students={students}
        onClose={() => setIsAddActivityModalOpen(false)}
        onSuccess={loadInitialData}
      />

      {/* Batch Attendance Modal */}
      <MarkAttendanceModal
        isOpen={isAttendanceModalOpen}
        students={students}
        onClose={() => setIsAttendanceModalOpen(false)}
        onSuccess={loadInitialData}
      />

      {/* Account & Profile Modal */}
      <AccountProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        teacherData={teacherProfile}
        onUpdateSuccess={handleProfileUpdateSuccess}
        onLogout={handleLogout}
      />
    </div>
  );
}

export default App;
