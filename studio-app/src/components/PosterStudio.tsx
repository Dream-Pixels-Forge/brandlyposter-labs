import { useState, useEffect } from 'react';
import { useBrandlyPoster } from './BrandlyPosterProvider';
import type { CreatePosterParams } from '../types';

export function PosterStudio() {
  const { currentPoster, currentProject, referenceImageUrl, isLoading, error, createPoster, export: exportPoster, loadProject, setReferenceImage, onPosterUpdate } = useBrandlyPoster();
  
  const [formData, setFormData] = useState<CreatePosterParams>({
    subjectId: '',
    genre: 'thriller',
    title: "L'ÉTOILE",
    subtitle: 'THE ASCENT',
    tagline: 'She built her own empire',
    story: 'Visionary leader from Kinshasa who built her own empire',
    outfit: 'cream linen blazer, dark wide-leg trousers, brown belt, brown boots',
    fixEarrings: true,
    resolution: '2:3',
  });

  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [showForm, setShowForm] = useState(true);
  const [activeTab, setActiveTab] = useState<'create' | 'preview' | 'qa'>('preview');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPoster(formData);
      setActiveTab('preview');
    } catch (err) {
      console.error('Failed to create poster:', err);
    }
  };

  const handleExport = async (format: string) => {
    const result = await exportPoster(format);
    if (result.success) {
      alert(`Exported ${format}: ${result.path}`);
    } else {
      alert(`Export failed: ${result.error}`);
    }
  };

  const handleLoadProject = async () => {
    if (selectedProjectId) {
      await loadProject(selectedProjectId);
    }
  };

  // Listen for poster updates from MCP
  useEffect(() => {
    const unsubscribe = onPosterUpdate((poster) => {
      console.log('Poster updated from MCP:', poster);
    });
    return unsubscribe;
  }, [onPosterUpdate]);

  const genres = [
    { id: 'thriller', name: 'Prestige Thriller' },
    { id: 'romcom', name: 'Rom-Com' },
    { id: 'scifi', name: 'African Futurism Sci-Fi' },
    { id: 'action', name: 'Spy Action' },
    { id: 'fashion', name: 'Fashion Documentary' },
    { id: 'horror', name: 'Psychological Horror' },
    { id: 'epic', name: 'Historical Epic' },
  ];

  const exportFormats = [
    { id: 'theatrical', name: 'Theatrical (27×40, 300 DPI, CMYK)' },
    { id: 'deck', name: 'Deck (1440×900, 72 DPI, sRGB)' },
    { id: 'social', name: 'Social (2160×3240, 2:3)' },
    { id: 'story', name: 'Story (1080×1920, 9:16)' },
    { id: 'animated', name: 'Animated (MP4/GIF/WebM)' },
  ];

  return (
    <div className="max-w-[1440px] mx-auto p-4">
      {/* Control Panel */}
      <div className="mb-6 bg-gray-900/50 rounded-xl border border-gray-800 p-4">
        <div className="flex gap-4 mb-4 border-b border-gray-800">
          {(['create', 'preview', 'qa'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === tab
                  ? 'bg-amber-400 text-gray-950'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === 'create' && (
          <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Subject ID</label>
                <input
                  type="text"
                  value={formData.subjectId}
                  onChange={(e) => setFormData({ ...formData, subjectId: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                  placeholder="Enter subject ID"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Genre</label>
                <select
                  value={formData.genre}
                  onChange={(e) => setFormData({ ...formData, genre: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                >
                  {genres.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Subtitle</label>
                <input
                  type="text"
                  value={formData.subtitle}
                  onChange={(e) => setFormData({ ...formData, subtitle: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-1">Tagline</label>
                <input
                  type="text"
                  value={formData.tagline}
                  onChange={(e) => setFormData({ ...formData, tagline: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-1">Story</label>
                <textarea
                  value={formData.story}
                  onChange={(e) => setFormData({ ...formData, story: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-1">Outfit</label>
                <textarea
                  value={formData.outfit}
                  onChange={(e) => setFormData({ ...formData, outfit: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="fixEarrings"
                  checked={formData.fixEarrings}
                  onChange={(e) => setFormData({ ...formData, fixEarrings: e.target.checked })}
                  className="w-4 h-4 text-amber-400 border-gray-700 rounded focus:ring-amber-400"
                />
                <label htmlFor="fixEarrings" className="text-sm text-gray-300">Fix earrings (symmetrical gold hoops)</label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Resolution</label>
                <select
                  value={formData.resolution}
                  onChange={(e) => setFormData({ ...formData, resolution: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                >
                  <option value="2:3">2:3 (Theatrical)</option>
                  <option value="9:16">9:16 (Story)</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={isLoading || !formData.subjectId}
                className="px-6 py-3 bg-amber-400 text-gray-950 font-semibold rounded-lg hover:bg-amber-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Creating...' : 'Create Poster'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(!showForm)}
                className="px-6 py-3 bg-gray-700 text-gray-200 font-semibold rounded-lg hover:bg-gray-600 transition-colors"
              >
                {showForm ? 'Hide Form' : 'Show Form'}
              </button>
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
          </form>
        )}

        {activeTab === 'preview' && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <label className="flex items-center gap-2 text-sm text-gray-300">
                <input
                  type="text"
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  placeholder="Project ID to load"
                  className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400 w-64"
                />
                <button
                  onClick={handleLoadProject}
                  disabled={isLoading || !selectedProjectId}
                  className="px-4 py-2 bg-amber-400 text-gray-950 font-semibold rounded-lg hover:bg-amber-300 disabled:opacity-50"
                >
                  Load Project
                </button>
              </label>
              <div className="flex-1" />
              {currentProject && (
                <select
                  onChange={(e) => handleExport(e.target.value)}
                  className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
                  defaultValue=""
                >
                  <option value="">Export format...</option>
                  {exportFormats.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
                </select>
              )}
            </div>

            {/* Poster Preview - 1440x900 */}
            <div className="relative">
              <div className="aspect-[1440/900] bg-gray-900 rounded-lg border border-gray-800 overflow-hidden relative">
                {currentPoster ? (
                  <div className="absolute inset-0 flex items-center justify-center p-8">
                    <div className="max-w-full max-h-full text-center">
                      <h3 className="text-4xl font-bold text-amber-400 mb-2 tracking-wide">{currentPoster.variant_plan?.title || 'Poster'}</h3>
                      <p className="text-xl text-gray-300 mb-4">{currentPoster.variant_plan?.subtitle}</p>
                      <p className="text-lg text-gray-400 mb-8 italic">"{currentPoster.variant_plan?.tagline}"</p>
                      <div className="text-sm text-gray-500 space-y-1">
                        <p>Genre: {currentPoster.genre_config?.name}</p>
                        <p>QA: {currentPoster.qa_checklist?.join(' • ')}</p>
                        <p>Subject: {currentPoster.subject_id}</p>
                      </div>
                      {referenceImageUrl && (
                        <img 
                          src={referenceImageUrl} 
                          alt="Reference" 
                          className="mt-4 max-w-xs mx-auto rounded border border-gray-700"
                        />
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                    <div className="text-center">
                      <svg className="w-16 h-16 mx-auto mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <p className="text-lg">No poster created yet</p>
                      <p className="text-sm">Create a poster or load a project</p>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Dimensions badge */}
              <div className="absolute bottom-2 right-2 bg-gray-950/90 backdrop-blur px-2 py-1 rounded text-xs text-gray-400 font-mono">
                1440 × 900 (Deck)
              </div>
            </div>
          </div>
        )}

        {activeTab === 'qa' && currentPoster && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-amber-400">QA Checklist</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {currentPoster.qa_checklist?.map((check, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                  <div className="w-5 h-5 rounded border-2 border-amber-400 flex items-center justify-center">
                    <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="text-gray-200">{check}</span>
                </div>
              ))}
            </div>
            
            {currentProject && (
              <div className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                <h4 className="font-medium text-gray-300 mb-2">Project QA: {currentProject.qa_score} — {currentProject.qa_passed ? 'PASS' : 'FAIL'}</h4>
                <div className="text-sm text-gray-400 space-y-1">
                  <p>Variants: {currentProject.variants.length}</p>
                  <p>Approved: {currentProject.approved ? 'Yes' : 'No'}</p>
                  {currentProject.approved_version && <p>Version: {currentProject.approved_version}</p>}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Reference Image Upload */}
      <div className="mb-6 bg-gray-900/50 rounded-xl border border-gray-800 p-4">
        <h3 className="text-lg font-semibold text-gray-200 mb-3">Reference Image</h3>
        <div className="flex items-center gap-4">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                const url = URL.createObjectURL(file);
                setReferenceImage(url);
              }
            }}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:bg-gray-700 transition-colors"
          />
          {referenceImageUrl && (
            <img
              src={referenceImageUrl}
              alt="Reference"
              className="w-24 h-24 object-cover rounded-lg border border-gray-700"
            />
          )}
          <span className="text-sm text-gray-400">Upload a reference image for likeness preservation</span>
        </div>
      </div>
    </div>
  );
}