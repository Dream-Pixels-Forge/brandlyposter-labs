import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useBrandlyPoster } from './BrandlyPosterProvider';
import type { ProjectManifest } from '../types';

async function fetchProjects(): Promise<ProjectManifest[]> {
  try {
    // In production, this would be an API endpoint
    // For now, we'll scan the projects directory via a backend endpoint
    const response = await fetch(`${import.meta.env.VITE_API_BASE || ''}/api/projects`);
    if (response.ok) {
      return response.json();
    }
    return [];
  } catch {
    return [];
  }
}

export function ProjectsList() {
  const { loadProject } = useBrandlyPoster();
  const [selectedProject, setSelectedProject] = useState<ProjectManifest | null>(null);

  const { data: projects = [], isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });

  if (isLoading) {
    return (
      <div className="max-w-[1440px] mx-auto p-8 text-center text-gray-400">
        Loading projects...
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-[1440px] mx-auto p-8 text-center text-red-400">
        Error loading projects: {error.message}
      </div>
    );
  }

  return (
    <div className="max-w-[1440px] mx-auto p-4">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-amber-400">Projects</h2>
        <button className="px-4 py-2 bg-amber-400 text-gray-950 font-semibold rounded-lg hover:bg-amber-300">
          Refresh
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-12 text-center">
          <svg className="w-16 h-16 mx-auto mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <p className="text-gray-400 text-lg">No projects found</p>
          <p className="text-gray-500 mt-2">Projects will appear here after export from MCP server</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map(project => (
            <ProjectCard
              key={project.project_id}
              project={project}
              isSelected={selectedProject?.project_id === project.project_id}
              onSelect={() => setSelectedProject(project)}
              onLoad={() => loadProject(project.project_id)}
            />
          ))}
        </div>
      )}

      {selectedProject && (
        <ProjectDetailModal project={selectedProject} onClose={() => setSelectedProject(null)} />
      )}
    </div>
  );
}

function ProjectCard({ project, isSelected, onSelect, onLoad }: { project: ProjectManifest; isSelected: boolean; onSelect: () => void; onLoad: () => void }) {
  const formatLabels = {
    theatrical: '🎬',
    deck: '🖥️',
    social: '📱',
    story: '📖',
    animated: '🎞️',
  };

  return (
    <div
      onClick={onSelect}
      className={`bg-gray-900/50 rounded-xl border transition-all cursor-pointer ${
        isSelected
          ? 'border-amber-400 ring-2 ring-amber-400/50'
          : 'border-gray-800 hover:border-gray-700'
      }`}
    >
      <div className="aspect-[1440/900] bg-gray-800 rounded-t-xl relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center text-gray-500">
          <span className="text-4xl">{formatLabels[project.variants[0]?.format as keyof typeof formatLabels] || '📄'}</span>
        </div>
        <div className="absolute top-2 right-2">
          <span className={`px-2 py-1 text-xs rounded-full ${
            project.qa_passed ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {project.qa_score}
          </span>
        </div>
        {project.approved && (
          <div className="absolute bottom-2 left-2">
            <span className="px-2 py-1 text-xs bg-amber-400/20 text-amber-400 rounded">Approved</span>
          </div>
        )}
      </div>
      <div className="p-4 space-y-2">
        <h3 className="font-semibold text-white truncate">{project.poster_id || project.project_id}</h3>
        <div className="text-sm text-gray-400 space-y-1">
          <p>Genre: <span className="text-gray-200">{project.genre}</span></p>
          <p>Subject: <span className="text-gray-200">{project.subject_id}</span></p>
          <p>Variants: <span className="text-gray-200">{project.variants.length}</span></p>
          <p className="text-xs text-gray-500">Created: {new Date(project.created_at).toLocaleDateString()}</p>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onLoad(); }}
          className="w-full mt-2 px-3 py-2 bg-amber-400 text-gray-950 font-semibold rounded-lg hover:bg-amber-300 transition-colors"
        >
          Load in Studio
        </button>
      </div>
    </div>
  );
}

function ProjectDetailModal({ project, onClose }: { project: ProjectManifest; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="bg-gray-900 rounded-xl border border-gray-800 max-w-3xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-800 flex items-center justify-between">
          <h3 className="text-xl font-bold">{project.poster_id || project.project_id}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl leading-none">&times;</button>
        </div>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-400">Project ID:</span> <span className="text-gray-200 ml-2 font-mono">{project.project_id}</span></div>
            <div><span className="text-gray-400">Subject:</span> <span className="text-gray-200 ml-2">{project.subject_id}</span></div>
            <div><span className="text-gray-400">Genre:</span> <span className="text-gray-200 ml-2">{project.genre}</span></div>
            <div><span className="text-gray-400">QA Score:</span> <span className={`ml-2 ${project.qa_passed ? 'text-green-400' : 'text-red-400'}`}>{project.qa_score}</span></div>
            <div><span className="text-gray-400">Approved:</span> <span className={`ml-2 ${project.approved ? 'text-green-400' : 'text-gray-400'}`}>{project.approved ? 'Yes' : 'No'}</span></div>
            <div><span className="text-gray-400">Created:</span> <span className="text-gray-200 ml-2">{new Date(project.created_at).toLocaleString()}</span></div>
          </div>

          <div>
            <h4 className="font-semibold mb-3">Variants</h4>
            <div className="space-y-2">
              {project.variants.map((v, i) => (
                <div key={i} className="p-3 bg-gray-800/50 rounded-lg border border-gray-700 flex items-center justify-between">
                  <div>
                    <span className="font-medium text-white">{v.format}</span>
                    <span className="text-gray-400 ml-2 text-sm">{v.specs.size} • {v.specs.color} • {v.specs.dpi} DPI</span>
                  </div>
                  <span className="text-xs text-gray-500 font-mono">{v.file}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-3">Master Prompt</h4>
            <pre className="bg-gray-950 p-4 rounded-lg border border-gray-800 text-sm text-gray-300 overflow-x-auto max-h-64 overflow-y-auto whitespace-pre-wrap">
              {project.master_prompt}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}