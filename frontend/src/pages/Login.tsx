import React, { useState } from 'react';
import { GraduationCap, Mail, Lock, User, Sparkles, AlertCircle, ArrowRight, CheckCircle2, AtSign } from 'lucide-react';
import { api, setAuthToken } from '../services/api';

interface LoginProps {
  onAuthSuccess: (token: string, user: any) => void;
}

export const Login: React.FC<LoginProps> = ({ onAuthSuccess }) => {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sign In Form
  const [signInIdentifier, setSignInIdentifier] = useState('');
  const [signInPassword, setSignInPassword] = useState('');

  // Sign Up Form (Universal Member)
  const [signUpFullName, setSignUpFullName] = useState('');
  const [signUpEmail, setSignUpEmail] = useState('');
  const [signUpUsername, setSignUpUsername] = useState('');
  const [signUpPassword, setSignUpPassword] = useState('');
  const [signUpConfirmPassword, setSignUpConfirmPassword] = useState('');
  const [signUpBio, setSignUpBio] = useState('');
  const [signUpSkills, setSignUpSkills] = useState('');

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login({
        login: signInIdentifier.trim(),
        password: signInPassword,
      });
      if (res.access_token) {
        setAuthToken(res.access_token);
        onAuthSuccess(res.access_token, res.user);
      } else {
        setError('Login failed: Token not returned.');
      }
    } catch (err: any) {
      setError(err.message || 'Invalid email, username, Guru ID, or password');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (signUpPassword !== signUpConfirmPassword) {
      setError('Passwords do not match. Please verify your confirm password.');
      return;
    }

    if (signUpPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    const cleanUsername = signUpUsername.trim().replace(/^@+/, '').toLowerCase();
    if (cleanUsername && !/^[a-z0-9_-]{3,30}$/.test(cleanUsername)) {
      setError('Username must be 3-30 characters with letters, numbers, hyphens or underscores only.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        full_name: signUpFullName.trim(),
        email: signUpEmail.trim().toLowerCase(),
        username: cleanUsername || undefined,
        password: signUpPassword,
        role: 'MEMBER',
        bio: signUpBio.trim() || undefined,
        skills: signUpSkills.trim() || undefined,
      };

      const res = await api.signup(payload);
      if (res.access_token) {
        setAuthToken(res.access_token);
        onAuthSuccess(res.access_token, res.user);
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please check your details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 sm:p-6 relative overflow-hidden">
      {/* Ambient background glow elements */}
      <div className="absolute -top-32 -left-32 w-96 h-96 bg-indigo-600/25 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-purple-600/25 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-100 relative z-10">
        {/* Header section */}
        <div className="bg-gradient-to-r from-indigo-700 via-indigo-600 to-purple-700 p-8 text-center text-white relative">
          <div className="w-16 h-16 bg-white/10 rounded-2xl mx-auto flex items-center justify-center backdrop-blur-md mb-3 border border-white/20 shadow-lg">
            <GraduationCap className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-2xl font-black tracking-tight">Guru Yuktha</h1>
          <p className="text-xs text-indigo-100 mt-1 font-medium flex items-center justify-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Connect • Learn • Teach • Grow • Earn</span>
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex bg-slate-100 p-1.5 m-6 mb-2 rounded-2xl">
          <button
            onClick={() => { setMode('signin'); setError(null); }}
            className={`flex-1 py-2.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
              mode === 'signin'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => { setMode('signup'); setError(null); }}
            className={`flex-1 py-2.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
              mode === 'signup'
                ? 'bg-white text-indigo-700 shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Universal Member Notice */}
        <div className="mx-6 mt-3 p-3 bg-indigo-50/80 border border-indigo-100 rounded-2xl flex items-center space-x-2.5 text-indigo-900">
          <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0" />
          <p className="text-[11px] font-medium leading-tight">
            <strong className="font-bold">Universal Member:</strong> Every member can teach, learn, own rooms, and join rooms.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mx-6 mt-3 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center space-x-2 text-rose-700 text-xs font-medium">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Sign In View */}
        {mode === 'signin' ? (
          <form onSubmit={handleSignIn} className="p-6 pt-4 space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Email, Username (@username), or Guru ID
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={signInIdentifier}
                  onChange={(e) => setSignInIdentifier(e.target.value)}
                  placeholder="name@mail.com, @username, or GY-XXXXXXXX"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Sign in using your email, unique @username, or permanent Guru ID.
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-bold text-slate-700">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => alert('Password reset is available through academic support or account email verification.')}
                  className="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer"
                >
                  Forgot Password?
                </button>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={signInPassword}
                  onChange={(e) => setSignInPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm rounded-xl transition-colors shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50 mt-4 cursor-pointer"
            >
              {loading ? (
                <span>Signing In...</span>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Link to Create Account */}
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => { setMode('signup'); setError(null); }}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold hover:underline cursor-pointer"
              >
                New to Guru Yuktha? Create a Member Account
              </button>
            </div>
          </form>
        ) : (
          /* Sign Up View (Universal Member) */
          <form onSubmit={handleSignUp} className="p-6 pt-4 space-y-3 max-h-[65vh] overflow-y-auto pr-2">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Full Name *
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={signUpFullName}
                  onChange={(e) => setSignUpFullName(e.target.value)}
                  placeholder="e.g. Ravi Teja or Dr. Rajesh Sharma"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Email Address *
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  required
                  value={signUpEmail}
                  onChange={(e) => setSignUpEmail(e.target.value)}
                  placeholder="you@domain.com"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Username / Unique Profile Handle *
              </label>
              <div className="relative">
                <AtSign className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={signUpUsername}
                  onChange={(e) => setSignUpUsername(e.target.value)}
                  placeholder="e.g. ravi or ravi_teja"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Your unique identity across Guru Yuktha (e.g. @{signUpUsername.replace(/^@+/, '') || 'username'}).
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Password *
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={signUpPassword}
                    onChange={(e) => setSignUpPassword(e.target.value)}
                    placeholder="Min 6 chars"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Confirm Password *
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={signUpConfirmPassword}
                    onChange={(e) => setSignUpConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Bio / About You (Optional)
              </label>
              <textarea
                rows={2}
                value={signUpBio}
                onChange={(e) => setSignUpBio(e.target.value)}
                placeholder="What topics do you want to teach or learn?"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Skills &amp; Knowledge Topics (Optional)
              </label>
              <input
                type="text"
                value={signUpSkills}
                onChange={(e) => setSignUpSkills(e.target.value)}
                placeholder="e.g. Python, Machine Learning, Mathematics, English"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold text-sm rounded-xl transition-all shadow-md flex items-center justify-center space-x-2 disabled:opacity-50 mt-3 cursor-pointer"
            >
              {loading ? (
                <span>Creating Member Account...</span>
              ) : (
                <>
                  <span>Create Account</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Link to Sign In */}
            <div className="text-center pt-1 pb-1">
              <button
                type="button"
                onClick={() => { setMode('signin'); setError(null); }}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold hover:underline cursor-pointer"
              >
                Already have an account? Sign In
              </button>
            </div>
          </form>
        )}

        {/* Footer */}
        <div className="p-3.5 bg-slate-50 text-center border-t border-slate-100">
          <p className="text-[11px] text-slate-400 font-medium">
            Guru Yuktha • Universal Knowledge &amp; Learning Platform
          </p>
        </div>
      </div>
    </div>
  );
};
