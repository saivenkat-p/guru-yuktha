import React, { useState } from 'react';
import { X, BookOpen, Globe, Lock, Plus, IndianRupee } from 'lucide-react';
import { api } from '../../services/api';

interface CreateRoomModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateRoomModal: React.FC<CreateRoomModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [accessType, setAccessType] = useState<'PUBLIC_FREE' | 'PRIVATE_FREE' | 'PRIVATE_PAID'>('PUBLIC_FREE');
  const [price, setPrice] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setError(null);
    setLoading(true);

    const visibility = accessType === 'PUBLIC_FREE' ? 'PUBLIC' : 'PRIVATE';

    try {
      await api.createRoom({
        name: name.trim(),
        description: description.trim() || undefined,
        visibility,
        access_type: accessType,
        price: accessType === 'PRIVATE_PAID' ? Number(price) : 0,
        currency: 'INR',
      });
      setName('');
      setDescription('');
      setAccessType('PUBLIC_FREE');
      setPrice(0);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create room');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
      <div className="bg-white w-full max-w-lg rounded-3xl shadow-2xl border border-slate-100 overflow-hidden">
        {/* Header */}
        <div className="bg-indigo-600 px-6 py-5 flex items-center justify-between text-white">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center backdrop-blur-xs">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-base">Create Knowledge Room</h3>
              <p className="text-[11px] text-indigo-100 font-medium">Establish a learning or teaching space as a Guru</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors text-white cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl font-medium">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Room Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Python Programming Masterclass — 2026"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Description (Optional)
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief summary of syllabus, objectives, or course scope..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Room Access Type Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Room Access Model
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <button
                type="button"
                onClick={() => setAccessType('PUBLIC_FREE')}
                className={`p-3 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                  accessType === 'PUBLIC_FREE'
                    ? 'border-indigo-600 bg-indigo-50/70 ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                }`}
              >
                <div>
                  <div className="flex items-center space-x-1.5 text-emerald-700 font-bold text-xs">
                    <Globe className="w-3.5 h-3.5" />
                    <span>Free Public</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1 leading-tight">
                    Anyone can view and join immediately without approval.
                  </p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setAccessType('PRIVATE_FREE')}
                className={`p-3 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                  accessType === 'PRIVATE_FREE'
                    ? 'border-indigo-600 bg-indigo-50/70 ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                }`}
              >
                <div>
                  <div className="flex items-center space-x-1.5 text-indigo-700 font-bold text-xs">
                    <Lock className="w-3.5 h-3.5" />
                    <span>Free Private</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1 leading-tight">
                    Safe preview allowed. Members must submit a join request.
                  </p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setAccessType('PRIVATE_PAID')}
                className={`p-3 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                  accessType === 'PRIVATE_PAID'
                    ? 'border-indigo-600 bg-indigo-50/70 ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                }`}
              >
                <div>
                  <div className="flex items-center space-x-1.5 text-amber-700 font-bold text-xs">
                    <IndianRupee className="w-3.5 h-3.5" />
                    <span>Paid Private</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1 leading-tight">
                    Paid admission room to monetize your knowledge.
                  </p>
                </div>
              </button>
            </div>
          </div>

          {/* Paid Room Price Input */}
          {accessType === 'PRIVATE_PAID' && (
            <div className="p-3.5 bg-amber-50/60 border border-amber-200 rounded-2xl">
              <label className="block text-xs font-bold text-amber-900 mb-1">
                Admission Fee (INR ₹) *
              </label>
              <div className="relative max-w-[200px]">
                <span className="absolute left-3 top-2.5 text-xs font-bold text-amber-700">₹</span>
                <input
                  type="number"
                  min={1}
                  required
                  value={price || ''}
                  onChange={(e) => setPrice(Math.max(0, Number(e.target.value)))}
                  placeholder="e.g. 499"
                  className="w-full bg-white border border-amber-300 rounded-xl pl-7 pr-3 py-2 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
            </div>
          )}

          <div className="pt-2 flex items-center justify-end space-x-2.5 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-colors shadow-md flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>{loading ? 'Creating...' : 'Create Room'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
