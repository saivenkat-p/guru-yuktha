import React, { useEffect, useState } from 'react';
import { 
  ArrowLeft, BookOpen, Folder as FolderIcon, FolderPlus, FileText, Plus, 
  Globe, Lock, Users, ExternalLink, Archive, Check, Copy, FileCode, Video, Image, File,
  UserCheck, UserX, Clock, IndianRupee, Sparkles, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import type { Room, Folder, Resource, RoomPreviewOut, JoinRequestOut } from '../types';
import { CreateFolderModal } from '../components/forms/CreateFolderModal';
import { CreateResourceModal } from '../components/forms/CreateResourceModal';

interface RoomDetailProps {
  roomId: number;
  onBack: () => void;
}

export const RoomDetail: React.FC<RoomDetailProps> = ({ roomId, onBack }) => {
  const [room, setRoom] = useState<Room | null>(null);
  const [preview, setPreview] = useState<RoomPreviewOut | null>(null);
  const [isPreviewMode, setIsPreviewMode] = useState(false);

  const [folders, setFolders] = useState<Folder[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [joinRequests, setJoinRequests] = useState<JoinRequestOut[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'CONTENT' | 'REQUESTS'>('CONTENT');

  const [loading, setLoading] = useState(true);
  const [copiedCode, setCopiedCode] = useState(false);
  const [joinMessage, setJoinMessage] = useState('');
  const [submittingJoin, setSubmittingJoin] = useState(false);
  const [joinStatus, setJoinStatus] = useState<string | null>(null);

  const [isCreateFolderOpen, setIsCreateFolderOpen] = useState(false);
  const [isCreateResourceOpen, setIsCreateResourceOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      // First try to load full room details
      const roomData = await api.getRoomDetails(roomId);
      setRoom(roomData);
      setIsPreviewMode(false);

      const [foldersData, resourcesData] = await Promise.all([
        api.getRoomFolders(roomId).catch(() => []),
        api.getRoomResources(roomId, selectedFolderId || undefined).catch(() => []),
      ]);
      setFolders(foldersData);
      setResources(resourcesData);

      // If owner, load join requests
      if (roomData.user_role === 'OWNER') {
        const reqs = await api.getRoomJoinRequests(roomId).catch(() => []);
        setJoinRequests(reqs);
      }
    } catch (err: any) {
      // Access denied / non-member: Load safe room preview
      try {
        const previewData = await api.getRoomPreview(roomId);
        setPreview(previewData);
        setIsPreviewMode(true);
        if (previewData.user_membership_status) {
          setJoinStatus(previewData.user_membership_status);
        }
      } catch (previewErr) {
        console.error('Failed to load room preview:', previewErr);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [roomId, selectedFolderId]);

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
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

  const handleSendJoinRequest = async () => {
    setSubmittingJoin(true);
    try {
      await api.requestToJoinRoom(roomId, { message: joinMessage.trim() });
      setJoinStatus('PENDING');
      alert('Your join request has been sent to the Guru for approval!');
    } catch (err: any) {
      alert(err.message || 'Failed to submit join request');
    } finally {
      setSubmittingJoin(false);
    }
  };

  const handleJoinPublicRoom = async () => {
    setSubmittingJoin(true);
    try {
      await api.joinPublicRoom(roomId);
      alert('Joined room successfully!');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to join room');
    } finally {
      setSubmittingJoin(false);
    }
  };

  const handleProcessRequest = async (membershipId: number, action: 'ACCEPT' | 'REJECT') => {
    try {
      await api.processRoomJoinRequest(roomId, membershipId, action);
      const reqs = await api.getRoomJoinRequests(roomId).catch(() => []);
      setJoinRequests(reqs);
      loadData();
    } catch (err: any) {
      alert(err.message || `Failed to ${action.toLowerCase()} request`);
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

  // SAFE PREVIEW MODE (For non-members visiting a private or public preview room)
  if (isPreviewMode && preview) {
    const isPublic = preview.visibility === 'PUBLIC' || preview.access_type === 'PUBLIC_FREE';
    return (
      <div className="space-y-6 pb-16">
        {/* Back Button */}
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-2 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Rooms</span>
        </button>

        {/* Room Header Card */}
        <div className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span
                  className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider flex items-center space-x-1 ${
                    isPublic ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                  }`}
                >
                  {isPublic ? (
                    <>
                      <Globe className="w-3 h-3" />
                      <span>Free Public Room</span>
                    </>
                  ) : (
                    <>
                      <Lock className="w-3 h-3" />
                      <span>Private Knowledge Circle</span>
                    </>
                  )}
                </span>
                <span className="text-xs font-mono font-bold text-slate-400">CODE: {preview.code}</span>
              </div>
              <h1 className="text-2xl font-black text-slate-900 tracking-tight">{preview.name}</h1>
              {preview.description && (
                <p className="text-xs text-slate-600 max-w-2xl leading-relaxed">{preview.description}</p>
              )}
            </div>

            {/* Admission Action Card */}
            <div className="bg-indigo-50/70 border border-indigo-100 p-5 rounded-2xl sm:min-w-[280px] space-y-3 shrink-0">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Admission:</span>
                <span className="font-bold text-indigo-700">
                  {preview.price > 0 ? `₹${preview.price} INR` : 'Free'}
                </span>
              </div>

              {joinStatus === 'PENDING' ? (
                <div className="p-3 bg-amber-100 border border-amber-200 rounded-xl text-center space-y-1">
                  <div className="flex items-center justify-center space-x-1.5 text-xs font-bold text-amber-800">
                    <Clock className="w-4 h-4" />
                    <span>Join Request Pending</span>
                  </div>
                  <p className="text-[10px] text-amber-700">Awaiting Guru's review and admission approval.</p>
                </div>
              ) : isPublic ? (
                <button
                  onClick={handleJoinPublicRoom}
                  disabled={submittingJoin}
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md cursor-pointer disabled:opacity-50 transition-all"
                >
                  {submittingJoin ? 'Joining...' : 'Join Public Room Instantly'}
                </button>
              ) : (
                <div className="space-y-2">
                  <input
                    type="text"
                    value={joinMessage}
                    onChange={(e) => setJoinMessage(e.target.value)}
                    placeholder="Message to Guru (optional)..."
                    className="w-full bg-white border border-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <button
                    onClick={handleSendJoinRequest}
                    disabled={submittingJoin}
                    className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md cursor-pointer disabled:opacity-50 transition-all"
                  >
                    {submittingJoin ? 'Submitting Request...' : 'Request Admission to Room'}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Guru Owner Card */}
          <div className="p-4 bg-slate-50 border border-slate-100 rounded-2xl flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center text-sm overflow-hidden">
                {preview.owner_avatar_url ? (
                  <img src={preview.owner_avatar_url} alt={preview.owner_name} className="w-full h-full object-cover" />
                ) : (
                  preview.owner_name.charAt(0)
                )}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">{preview.owner_name}</h4>
                <div className="flex items-center space-x-2 text-[11px] text-slate-500">
                  {preview.owner_username && <span>@{preview.owner_username}</span>}
                  <span className="font-mono font-bold text-indigo-600">{preview.owner_guru_id}</span>
                </div>
              </div>
            </div>

            <div className="text-[11px] text-slate-500 font-medium">
              <span>{preview.owner_followers_count} Shishya/Followers</span>
            </div>
          </div>
        </div>

        {/* Safe Preview Folder Outline & Previewable Resources */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Outline Folders */}
          <div className="lg:col-span-1 space-y-3">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Curriculum Outline</h3>
            <div className="bg-white p-3 rounded-2xl border border-slate-100 space-y-1.5 shadow-xs">
              {preview.folders.length === 0 ? (
                <p className="text-xs text-slate-400 p-2 text-center">No folders created yet</p>
              ) : (
                preview.folders.map((f) => (
                  <div key={f.id} className="p-2.5 rounded-xl bg-slate-50 flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-800 truncate">{f.name}</span>
                    <span className="text-[10px] text-slate-400">{f.resources_count} items</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Resources Preview */}
          <div className="lg:col-span-3 space-y-3">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Learning Materials Preview ({preview.preview_resources.length})
            </h3>

            {preview.preview_resources.length === 0 ? (
              <div className="bg-white p-8 rounded-2xl border border-slate-100 text-center text-xs text-slate-400">
                No materials posted yet.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {preview.preview_resources.map((res) => (
                  <div
                    key={res.id}
                    className="p-4 bg-white rounded-2xl border border-slate-100 shadow-xs flex items-center justify-between space-x-3"
                  >
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded">
                          {res.resource_type}
                        </span>
                        {res.is_preview_allowed ? (
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded flex items-center space-x-0.5">
                            <Sparkles className="w-2.5 h-2.5" />
                            <span>Preview Available</span>
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded flex items-center space-x-0.5">
                            <Lock className="w-2.5 h-2.5" />
                            <span>Locked for Members</span>
                          </span>
                        )}
                      </div>
                      <h4 className="text-xs font-bold text-slate-900 truncate">{res.title}</h4>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // FULL ROOM VIEW (For Owner and Active Members)
  if (!room) return null;

  const isOwner = room.user_role === 'OWNER';

  return (
    <div className="space-y-6 pb-16">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="inline-flex items-center space-x-2 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Rooms</span>
      </button>

      {/* Room Header Card */}
      <div className="bg-white rounded-3xl border border-slate-100 p-6 sm:p-8 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2.5">
              <span
                className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider flex items-center space-x-1 ${
                  room.visibility === 'PUBLIC'
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-indigo-50 text-indigo-700'
                }`}
              >
                {room.visibility === 'PUBLIC' ? <Globe className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
                <span>{room.visibility === 'PUBLIC' ? 'Public Room' : 'Private Room'}</span>
              </span>

              <button
                onClick={() => handleCopyCode(room.code)}
                className="px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs font-mono font-bold flex items-center space-x-1.5 transition-colors cursor-pointer border border-slate-200"
              >
                <span>{room.code}</span>
                {copiedCode ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>

            <h1 className="text-2xl font-black text-slate-900 tracking-tight">{room.name}</h1>
            {room.description && (
              <p className="text-xs text-slate-600 max-w-2xl leading-relaxed">{room.description}</p>
            )}
          </div>

          {/* Owner Quick Actions */}
          {isOwner && (
            <div className="flex items-center space-x-2.5 shrink-0">
              <button
                onClick={() => setIsCreateFolderOpen(true)}
                className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer"
              >
                <FolderPlus className="w-4 h-4 text-slate-600" />
                <span>New Folder</span>
              </button>
              <button
                onClick={() => setIsCreateResourceOpen(true)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center space-x-1.5 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Add Resource</span>
              </button>
            </div>
          )}
        </div>

        {/* Stats bar */}
        <div className="flex items-center space-x-6 pt-3 border-t border-slate-100 text-xs text-slate-500">
          <div className="flex items-center space-x-1.5">
            <Users className="w-4 h-4 text-indigo-600" />
            <span>{room.active_members_count} Active Members</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <FolderIcon className="w-4 h-4 text-amber-500" />
            <span>{folders.length} Folders</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <FileText className="w-4 h-4 text-emerald-600" />
            <span>{resources.length} Resources</span>
          </div>
          {isOwner && (
            <span className="text-[10px] px-2 py-0.5 rounded-md font-bold uppercase tracking-wider bg-indigo-100 text-indigo-800">
              You are the Guru / Owner
            </span>
          )}
        </div>
      </div>

      {/* Tabs (Content vs Join Requests for Owner) */}
      {isOwner && (
        <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
          <button
            onClick={() => setActiveTab('CONTENT')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'CONTENT'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            Learning Materials
          </button>
          <button
            onClick={() => setActiveTab('REQUESTS')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-1.5 ${
              activeTab === 'REQUESTS'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            <span>Admission Requests</span>
            {joinRequests.length > 0 && (
              <span className="px-1.5 py-0.2 bg-rose-500 text-white rounded-full text-[10px]">
                {joinRequests.length}
              </span>
            )}
          </button>
        </div>
      )}

      {/* TAB: Join Requests */}
      {isOwner && activeTab === 'REQUESTS' && (
        <div className="bg-white rounded-3xl border border-slate-100 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900">Pending Admission Requests</h2>
            <span className="text-xs text-slate-500">{joinRequests.length} pending review</span>
          </div>

          {joinRequests.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-8">No pending admission requests.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {joinRequests.map((req) => (
                <div key={req.id} className="py-3.5 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <h4 className="text-xs font-bold text-slate-900">{req.user_name}</h4>
                    <div className="flex items-center space-x-2 text-[11px] text-slate-500">
                      {req.user_username && <span>@{req.user_username}</span>}
                      <span className="font-mono font-bold text-indigo-600">{req.user_guru_id}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => handleProcessRequest(req.id, 'ACCEPT')}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all flex items-center space-x-1 cursor-pointer shadow-xs"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      <span>Accept</span>
                    </button>
                    <button
                      onClick={() => handleProcessRequest(req.id, 'REJECT')}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-600 rounded-xl text-xs font-bold transition-all flex items-center space-x-1 cursor-pointer"
                    >
                      <UserX className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB: Content (Folders + Resources) */}
      {(!isOwner || activeTab === 'CONTENT') && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Folders Sidebar */}
          <div className="lg:col-span-1 space-y-3">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Folders</h2>
              {isOwner && (
                <button
                  onClick={() => setIsCreateFolderOpen(true)}
                  className="text-indigo-600 hover:text-indigo-800 text-xs font-bold cursor-pointer inline-flex items-center space-x-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>New</span>
                </button>
              )}
            </div>

            <div className="bg-white rounded-2xl border border-slate-100 p-2 space-y-1 shadow-xs">
              <button
                onClick={() => setSelectedFolderId(null)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  selectedFolderId === null
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <FolderIcon className="w-4 h-4" />
                  <span>All Resources</span>
                </div>
                <span className="text-[10px] opacity-80">{resources.length}</span>
              </button>

              {folders.map((folder) => (
                <div
                  key={folder.id}
                  className={`group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    selectedFolderId === folder.id
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <div
                    onClick={() => setSelectedFolderId(folder.id)}
                    className="flex items-center space-x-2 flex-1 min-w-0"
                  >
                    <FolderIcon className="w-4 h-4 shrink-0" />
                    <span className="truncate">{folder.name}</span>
                  </div>

                  <div className="flex items-center space-x-1.5 shrink-0">
                    <span className="text-[10px] opacity-80">{folder.resources_count}</span>
                    {isOwner && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleArchiveFolder(folder.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-300 transition-opacity"
                        title="Archive folder"
                      >
                        <Archive className="w-3 h-3" />
                      </button>
                    )}
                  </div>
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
                {isOwner && (
                  <button
                    onClick={() => setIsCreateResourceOpen(true)}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md inline-flex items-center space-x-1.5 cursor-pointer"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add Resource</span>
                  </button>
                )}
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
                        {(res.file_url || res.external_url) && (
                          <a
                            href={res.file_url || res.external_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-bold inline-flex items-center space-x-1 transition-colors"
                          >
                            <ExternalLink className="w-3 h-3" />
                            <span>Open</span>
                          </a>
                        )}
                        {isOwner && (
                          <button
                            onClick={() => handleArchiveResource(res.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                            title="Archive resource"
                          >
                            <Archive className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

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
