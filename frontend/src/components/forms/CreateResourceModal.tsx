import React, { useState } from 'react';
import { X, Plus, FileText, Globe, Lock, Link as LinkIcon, FileCheck } from 'lucide-react';
import { api } from '../../services/api';
import type { Folder } from '../../types';

interface CreateResourceModalProps {
  isOpen: boolean;
  roomId: number;
  folders: Folder[];
  initialFolderId?: number | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateResourceModal: React.FC<CreateResourceModalProps> = ({
  isOpen,
  roomId,
  folders,
  initialFolderId,
  onClose,
  onSuccess,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [folderId, setFolderId] = useState<number | ''>(initialFolderId || '');
  const [resourceType, setResourceType] = useState<'PDF' | 'PPT' | 'DOC' | 'VIDEO' | 'LINK' | 'IMAGE' | 'OTHER'>('PDF');
  const [fileUrl, setFileUrl] = useState('');
  const [visibility, setVisibility] = useState<'PUBLIC' | 'ROOM_ONLY'>('ROOM_ONLY');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setError(null);
    setLoading(true);

    try {
      await api.createResource(roomId, {
        title: title.trim(),
        description: description.trim() || undefined,
        folder_id: folderId ? Number(folderId) : undefined,
        resource_type: resourceType,
        file_url: fileUrl.trim() || undefined,
        visibility,
      });
      setTitle('');
      setDescription('');
      setFileUrl('');
      setVisibility('ROOM_ONLY');
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to add resource');
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
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-base">Add Learning Resource</h3>
              <p className="text-[11px] text-indigo-100 font-medium">Publish notes, lectures, slides, and links</p>
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
              Resource Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Unit 2 — Complete Lecture Notes &amp; Slides"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Resource Type
              </label>
              <select
                value={resourceType}
                onChange={(e) => setResourceType(e.target.value as any)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
              >
                <option value="PDF">PDF Document</option>
                <option value="PPT">Presentation (PPT)</option>
                <option value="DOC">Document (DOC)</option>
                <option value="VIDEO">Video Lecture</option>
                <option value="LINK">External Link</option>
                <option value="IMAGE">Infographic / Image</option>
                <option value="OTHER">Other Material</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Assign to Folder
              </label>
              <select
                value={folderId}
                onChange={(e) => setFolderId(e.target.value ? Number(e.target.value) : '')}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
              >
                <option value="">No Folder (Root)</option>
                {folders.map((f) => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Resource URL / File Reference
            </label>
            <input
              type="text"
              value={fileUrl}
              onChange={(e) => setFileUrl(e.target.value)}
              placeholder="https://drive.google.com/... or https://youtube.com/..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
              placeholder="Summary of topics covered, references, or instructions..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5">
              Resource Visibility
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => setVisibility('ROOM_ONLY')}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  visibility === 'ROOM_ONLY'
                    ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center space-x-1.5 text-indigo-700 font-bold text-xs">
                  <Lock className="w-3.5 h-3.5" />
                  <span>Room Members Only</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1 leading-tight">
                  Only enrolled room members and the teacher can access this resource.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setVisibility('PUBLIC')}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  visibility === 'PUBLIC'
                    ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center space-x-1.5 text-indigo-700 font-bold text-xs">
                  <Globe className="w-3.5 h-3.5" />
                  <span>Public Learning</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1 leading-tight">
                  Discoverable by any learner without automatically creating a tracking relationship.
                </p>
              </button>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-end space-x-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !title.trim()}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-colors shadow-md flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>{loading ? 'Adding...' : 'Add Resource'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
