import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import type { BrandlyPosterAPI, CreatePosterParams, MasterPromptResult, ProjectManifest, PostMessagePayload, PostMessageResponse } from '../types';

interface BrandlyPosterContextType extends BrandlyPosterAPI {
  currentPoster: MasterPromptResult | null;
  currentProject: ProjectManifest | null;
  referenceImageUrl: string | null;
  isLoading: boolean;
  error: string | null;
}

const BrandlyPosterContext = createContext<BrandlyPosterContextType | null>(null);

export function BrandlyPosterProvider({ children }: { children: ReactNode }) {
  const [currentPoster, setCurrentPoster] = useState<MasterPromptResult | null>(null);
  const [currentProject, setCurrentProject] = useState<ProjectManifest | null>(null);
  const [referenceImageUrl, setReferenceImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updateCallbacks, setUpdateCallbacks] = useState<Set<(poster: MasterPromptResult) => void>>(new Set());

  // MCP Server base URL - in production would be configurable
  const MCP_BASE_URL = import.meta.env.VITE_MCP_BASE_URL || 'http://localhost:8000';

  // Handle postMessage from MCP server iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Verify origin in production
      if (event.data?.type === 'MCP_POSTER_UPDATE') {
        const poster = event.data.payload as MasterPromptResult;
        setCurrentPoster(poster);
        updateCallbacks.forEach(cb => cb(poster));
      }
      if (event.data?.type === 'MCP_PROJECT_LOADED') {
        const project = event.data.payload as ProjectManifest;
        setCurrentProject(project);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [updateCallbacks]);

  const createPoster = useCallback(async (params: CreatePosterParams): Promise<MasterPromptResult> => {
    setIsLoading(true);
    setError(null);

    try {
      // Call MCP server via postMessage to iframe or direct API
      const iframe = document.getElementById('mcp-iframe') as HTMLIFrameElement | null;
      
      if (iframe?.contentWindow) {
        // Send via postMessage to MCP iframe
        const requestId = crypto.randomUUID();
        const payload: PostMessagePayload = {
          type: 'CREATE_POSTER',
          payload: params,
          requestId,
        };
        iframe.contentWindow.postMessage(payload, '*');

        // Wait for response
        return new Promise((resolve, reject) => {
          const handleResponse = (event: MessageEvent) => {
            if (event.data?.type === 'RESPONSE' && event.data.requestId === requestId) {
              window.removeEventListener('message', handleResponse);
              const response = event.data as PostMessageResponse;
              if (response.success && response.data) {
                const poster = response.data as MasterPromptResult;
                setCurrentPoster(poster);
                updateCallbacks.forEach(cb => cb(poster));
                resolve(poster);
              } else {
                reject(new Error(response.error || 'Failed to create poster'));
              }
            }
          };
          window.addEventListener('message', handleResponse);
          
          // Timeout after 30 seconds
          setTimeout(() => {
            window.removeEventListener('message', handleResponse);
            reject(new Error('Request timeout'));
          }, 30000);
        });
      } else {
        // Fallback: direct fetch to MCP server (if running as HTTP)
        const response = await fetch(`${MCP_BASE_URL}/mcp/brandly_create_poster`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params),
        });
        
        if (!response.ok) throw new Error(`MCP server error: ${response.status}`);
        const data = await response.json();
        const poster = data as MasterPromptResult;
        setCurrentPoster(poster);
        updateCallbacks.forEach(cb => cb(poster));
        return poster;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [MCP_BASE_URL, updateCallbacks]);

  const getPrompt = useCallback((): string | null => {
    return currentPoster?.master_prompt || null;
  }, [currentPoster]);

  const exportPoster = useCallback(async (format: string): Promise<{ success: boolean; path?: string; error?: string }> => {
    if (!currentProject) {
      return { success: false, error: 'No project loaded' };
    }

    try {
      const iframe = document.getElementById('mcp-iframe') as HTMLIFrameElement | null;
      
      if (iframe?.contentWindow) {
        const requestId = crypto.randomUUID();
        const payload: PostMessagePayload = {
          type: 'EXPORT',
          payload: { projectId: currentProject.project_id, format },
          requestId,
        };
        iframe.contentWindow.postMessage(payload, '*');

        return new Promise((resolve) => {
          const handleResponse = (event: MessageEvent) => {
            if (event.data?.type === 'RESPONSE' && event.data.requestId === requestId) {
              window.removeEventListener('message', handleResponse);
              const response = event.data as PostMessageResponse;
              resolve(response.success ? { success: true, path: response.data as string } : { success: false, error: response.error });
            }
          };
          window.addEventListener('message', handleResponse);
          
          setTimeout(() => {
            window.removeEventListener('message', handleResponse);
            resolve({ success: false, error: 'Export timeout' });
          }, 60000);
        });
      }
      
      return { success: false, error: 'MCP iframe not available' };
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : 'Export failed' };
    }
  }, [currentProject]);

  const loadProject = useCallback(async (projectId: string): Promise<ProjectManifest | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const iframe = document.getElementById('mcp-iframe') as HTMLIFrameElement | null;
      
      if (iframe?.contentWindow) {
        const requestId = crypto.randomUUID();
        const payload: PostMessagePayload = {
          type: 'LOAD_PROJECT',
          payload: { projectId },
          requestId,
        };
        iframe.contentWindow.postMessage(payload, '*');

        return new Promise((resolve, reject) => {
          const handleResponse = (event: MessageEvent) => {
            if (event.data?.type === 'RESPONSE' && event.data.requestId === requestId) {
              window.removeEventListener('message', handleResponse);
              const response = event.data as PostMessageResponse;
              if (response.success && response.data) {
                const project = response.data as ProjectManifest;
                setCurrentProject(project);
                resolve(project);
              } else {
                reject(new Error(response.error || 'Failed to load project'));
              }
            }
          };
          window.addEventListener('message', handleResponse);
          
          setTimeout(() => {
            window.removeEventListener('message', handleResponse);
            reject(new Error('Load timeout'));
          }, 15000);
        });
      }
      
      return null;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const setReferenceImage = useCallback((imageUrl: string) => {
    setReferenceImageUrl(imageUrl);
    
    // Notify MCP iframe
    const iframe = document.getElementById('mcp-iframe') as HTMLIFrameElement | null;
    if (iframe?.contentWindow) {
      iframe.contentWindow.postMessage({
        type: 'SET_REFERENCE',
        payload: { imageUrl },
        requestId: crypto.randomUUID(),
      }, '*');
    }
  }, []);

  const onPosterUpdate = useCallback((callback: (poster: MasterPromptResult) => void) => {
    setUpdateCallbacks(prev => new Set([...prev, callback]));
    return () => {
      setUpdateCallbacks(prev => {
        const next = new Set(prev);
        next.delete(callback);
        return next;
      });
    };
  }, []);

  const value: BrandlyPosterContextType = {
    currentPoster,
    currentProject,
    referenceImageUrl,
    isLoading,
    error,
    createPoster,
    getPrompt,
    export: exportPoster,
    loadProject,
    setReferenceImage,
    onPosterUpdate,
  };

  return (
    <BrandlyPosterContext.Provider value={value}>
      {children}
      {/* Hidden iframe for MCP communication */}
      <iframe
        id="mcp-iframe"
        src={import.meta.env.VITE_MCP_IFRAME_URL || ''}
        style={{ display: 'none' }}
        title="MCP Server Communication"
      />
    </BrandlyPosterContext.Provider>
  );
}

export function useBrandlyPoster() {
  const context = useContext(BrandlyPosterContext);
  if (!context) {
    throw new Error('useBrandlyPoster must be used within BrandlyPosterProvider');
  }
  return context;
}