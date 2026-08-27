import React, { useEffect, useState } from 'react';
import { 
  ArrowLeft, BookOpen, Folder as FolderIcon, FolderPlus, FileText, Plus, 
  Globe, Lock, Users, ExternalLink, Archive, Check, Copy, FileCode, Video, Image, File 
} from 'lucide-react';
import { api } from '../services/api';
import type { Room, Folder, Resource } from '../types';
import { CreateFolderModal } from '../components/forms/CreateFolderModal';
import { CreateResourceModal } from '../components/forms/CreateResourceModal';

interface RoomDetailProps {
  roomId: number;
  onBack: () => void;
}

export const RoomDetail: React.FC<RoomDetailProps> = ({ roomId, onBack }) => {
  const [room, setRoom] = useState<Room | null>(null);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedCode, setCopiedCode] = useState(false);

  const [isCreateFolderOpen, setIsCreateFolderOpen] = useState(false);
  const [isCreateResourceOpen, setIsCreateResourceOpen] = useState(false);

  const loadData = async () => {
    try {
      const [roomData, foldersData, resourcesData] = await Promise.all([
        api.getRoomDetails(roomId),
        api.getRoomFolders(roomId),
        api.getRoomResources(roomId, selectedFolderId || undefined),
      ]);
      setRoom(roomData);
      setFolders(foldersData);
      setResources(resourcesData);
    } catch (err) {
      console.error('Failed to load room details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [roomId, selectedFolderId]);

  const handleCopyCode = () => {
    if (room?.code) {
      navigator.clipboard.writeText(room.code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const handleArchiveResource = async (resourceId: number) => {
    if (!window.confirm('Archive this learning resource?')) return;
    try {
      await api.archiveResource(roomId, resourceId);
      loadData();
    } catch (err) {
      console.error('Failed to archive resource:', err);
    }
  };

  const handleArchiveFolder = async (folderId: number) => {
    if (!window.confirm('Archive this folder? Resources in this folder will remain active.')) return;
    try {
      await api.archiveFolder(roomId, folderId);
      if (selectedFolderId === folderId) setSelectedFolderId(null);
      loadData();
    } catch (err) {
      console.error('Failed to archive folder:', err);
    }
  };

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'PDF':
      case 'DOC':
        return <FileText className="w-5 h-5 text-indigo-600" />;
      case 'PPT':
        return <FileCode className="w-5 h-5 text-amber-600" />;
      case 'VIDEO':
        return <Video className="w-5 h-5 text-rose-600" />;
      case 'IMAGE':
        return <Image className="w-5 h-5 text-emerald-600" />;
      case 'LINK':
        return <ExternalLink className="w-5 h-5 text-sky-600" />;
      default:
        return <File className="w-5 h-5 text-slate-600" />;
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-50 min-h-[60vh] p-8 flex flex-col items-center justify-center text-slate-500">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-xs font-bold text-indigo-700">Loading Academic Workspace...</p>
      </div>
    );
  }

  if (!room) {
    return (
      <div className="p-8 text-center space-y-4">
        <p className="text-sm font-bold text-slate-700">Room not found or no longer active.</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold"
        >
          Back to Rooms
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header Card */}
      <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <button
            onClick={onBack}
            className="inline-flex items-center space-x-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to All Rooms</span>
          </button>

          <div className="flex items-center space-x-2">
            <span className={`px-2.5 py-1 rounded-lg text-[10px] font-extrabold uppercase tracking-wider flex items-center space-x-1 ${
              room.visibility === 'PUBLIC'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-slate-100 text-slate-700 border border-slate-200'
            }`}>
              {room.visibility === 'PUBLIC' ? <Globe className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
              <span>{room.visibility}</span>
            </span>

            <button
              onClick={handleCopyCode}
              className="inline-flex items-center space-x-1 px-2.5 py-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-xs font-mono font-bold text-slate-700 transition-colors cursor-pointer"
            >
              {copiedCode ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>{room.code}</span>
                </>
              )}
            </button>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-slate-100">
          <div>
            <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight">{room.name}</h1>
            {room.description && (
              <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">{room.description}</p>
            )}
            <div className="flex items-center space-x-3 mt-2 text-xs text-slate-500 font-medium">
              <span className="flex items-center space-x-1">
                <Users className="w-3.5 h-3.5 text-indigo-600" />
                <span>{room.active_members_count} Tracked Learners</span>
              </span>
              <span>•</span>
              <span>{folders.length} Folders</span>
              <span>•</span>
              <span>{resources.length} Resources</span>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={() => setIsCreateFolderOpen(true)}
              className="px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer"
            >
              <FolderPlus className="w-4 h-4 text-indigo-600" />
              <span>New Folder</span>
            </button>
            <button
              onClick={() => setIsCreateResourceOpen(true)}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-all shadow-md flex items-center space-x-1.5 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Add Resource</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Workspace Layout: Folders + Resources */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Folders Sidebar */}
        <div className="bg-white p-5 rounded-3xl border border-slate-100 shadow-xs space-y-3 lg:col-span-1">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">Academic Folders</h3>
            <button
              onClick={() => setIsCreateFolderOpen(true)}
              className="text-indigo-600 hover:text-indigo-800 text-xs font-bold cursor-pointer"
            >
              + New
            </button>
          </div>

          <div className="space-y-1">
            <button
              onClick={() => setSelectedFolderId(null)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                selectedFolderId === null
                  ? 'bg-indigo-50 text-indigo-700 font-bold border border-indigo-200'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center space-x-2">
                <FolderIcon className="w-4 h-4 text-indigo-500" />
                <span>All Resources</span>
              </div>
              <span className="text-[11px] text-slate-400">{resources.length}</span>
            </button>

            {folders.map((f) => (
              <div
                key={f.id}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs transition-all ${
                  selectedFolderId === f.id
                    ? 'bg-indigo-50 text-indigo-700 font-bold border border-indigo-200'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <button
                  onClick={() => setSelectedFolderId(f.id)}
                  className="flex-1 flex items-center space-x-2 text-left truncate cursor-pointer"
                >
                  <FolderIcon className="w-4 h-4 text-amber-500 shrink-0" />
                  <span className="truncate">{f.name}</span>
                </button>
                <button
                  onClick={() => handleArchiveFolder(f.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-600 transition-opacity cursor-pointer"
                  title="Archive folder"
                >
                  <Archive className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Resources Grid */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-sm font-bold text-slate-800">
              {selectedFolderId
                ? `Folder: ${folders.find(f => f.id === selectedFolderId)?.name || 'Selected'}`
                : 'All Learning Resources'}
            </h2>
            <span className="text-xs text-slate-400 font-medium">{resources.length} items</span>
          </div>

          {resources.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-100 p-10 text-center space-y-3">
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto">
                <FileText className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-800">No resources in this folder yet</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  Upload syllabus documents, lecture notes, video links, or study guides for your learners.
                </p>
              </div>
              <button
                onClick={() => setIsCreateResourceOpen(true)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md inline-flex items-center space-x-1.5 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Add Resource</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {resources.map((res) => (
                <div
                  key={res.id}
                  className="bg-white rounded-3xl border border-slate-100 shadow-xs hover:shadow-md transition-all p-5 space-y-3 flex flex-col justify-between"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <div className="w-9 h-9 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center">
                          {getResourceIcon(res.resource_type)}
                        </div>
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                          {res.resource_type}
                        </span>
                      </div>

                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase tracking-wider flex items-center space-x-1 ${
                        res.visibility === 'PUBLIC'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                      }`}>
                        {res.visibility === 'PUBLIC' ? <Globe className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
                        <span>{res.visibility === 'PUBLIC' ? 'Public' : 'Room Only'}</span>
                      </span>
                    </div>

                    <div>
                      <h4 className="font-bold text-sm text-slate-900">{res.title}</h4>
                      {res.description && (
                        <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                          {res.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                    {res.folder_name ? (
                      <span className="inline-flex items-center space-x-1 text-[11px] text-amber-600 font-medium truncate max-w-[140px]">
                        <FolderIcon className="w-3 h-3" />
                        <span className="truncate">{res.folder_name}</span>
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400">Root Directory</span>
                    )}

                    <div className="flex items-center space-x-1.5">
                      {res.file_url && (
                        <a
                          href={res.file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-bold inline-flex items-center space-x-1 transition-colors"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>Open</span>
                        </a>
                      )}
                      <button
                        onClick={() => handleArchiveResource(res.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                        title="Archive resource"
                      >
                        <Archive className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <CreateFolderModal
        isOpen={isCreateFolderOpen}
        roomId={roomId}
        onClose={() => setIsCreateFolderOpen(false)}
        onSuccess={loadData}
      />

      <CreateResourceModal
        isOpen={isCreateResourceOpen}
        roomId={roomId}
        folders={folders}
        initialFolderId={selectedFolderId}
        onClose={() => setIsCreateResourceOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
};
