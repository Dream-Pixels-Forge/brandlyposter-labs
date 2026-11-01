import { useState } from 'react';

export function SettingsPanel() {
  const [mcpUrl, setMcpUrl] = useState(import.meta.env.VITE_MCP_BASE_URL || 'http://localhost:8000');
  const [iframeUrl, setIframeUrl] = useState(import.meta.env.VITE_MCP_IFRAME_URL || '');
  const [dataRoot, setDataRoot] = useState(import.meta.env.VITE_DATA_ROOT || '/mnt/data/brandlyposter-labs');
  const [apiBase, setApiBase] = useState(import.meta.env.VITE_API_BASE || '');

  const handleSaveConfig = () => {
    // In a real app, this would persist to localStorage or a config file
    localStorage.setItem('brandly_mcp_url', mcpUrl);
    localStorage.setItem('brandly_iframe_url', iframeUrl);
    localStorage.setItem('brandly_data_root', dataRoot);
    localStorage.setItem('brandly_api_base', apiBase);
    alert('Configuration saved! Reload the app to apply changes.');
  };

  return (
    <div className="max-w-[1440px] mx-auto p-4 space-y-8">
      <h2 className="text-2xl font-bold text-amber-400">Settings</h2>

      {/* MCP Server Configuration */}
      <section className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-gray-200 mb-4">MCP Server Configuration</h3>
        <div className="space-y-4 max-w-2xl">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">MCP Server Base URL</label>
            <input
              type="url"
              value={mcpUrl}
              onChange={(e) => setMcpUrl(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
              placeholder="http://localhost:8000"
            />
            <p className="text-xs text-gray-500 mt-1">Base URL for MCP server HTTP endpoints (fallback if iframe not available)</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">MCP Iframe URL</label>
            <input
              type="url"
              value={iframeUrl}
              onChange={(e) => setIframeUrl(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
              placeholder="http://localhost:8000/mcp/iframe"
            />
            <p className="text-xs text-gray-500 mt-1">URL for MCP server iframe (used for postMessage communication)</p>
          </div>
        </div>
      </section>

      {/* Data Paths */}
      <section className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-gray-200 mb-4">Data Paths</h3>
        <div className="space-y-4 max-w-2xl">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Data Root Directory</label>
            <input
              type="text"
              value={dataRoot}
              onChange={(e) => setDataRoot(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
              placeholder="/mnt/data/brandlyposter-labs"
            />
            <p className="text-xs text-gray-500 mt-1">Root directory for subjects, projects, and exported assets</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">API Base URL</label>
            <input
              type="url"
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400"
              placeholder="http://localhost:3001"
            />
            <p className="text-xs text-gray-500 mt-1">Backend API for project listing and management</p>
          </div>
        </div>
      </section>

      {/* Studio Display */}
      <section className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-gray-200 mb-4">Studio Display</h3>
        <div className="space-y-4 max-w-2xl">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Canvas Size: 1440 × 900 (Deck)</label>
            <div className="aspect-[1440/900] bg-gray-800 rounded-lg border border-gray-700 flex items-center justify-center">
              <span className="text-gray-500 text-sm">Preview area in Studio tab</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-gray-800/50 rounded-lg">
              <p className="text-gray-400">Width</p>
              <p className="text-white font-mono">1440px</p>
            </div>
            <div className="p-3 bg-gray-800/50 rounded-lg">
              <p className="text-gray-400">Height</p>
              <p className="text-white font-mono">900px</p>
            </div>
            <div className="p-3 bg-gray-800/50 rounded-lg">
              <p className="text-gray-400">Aspect Ratio</p>
              <p className="text-white font-mono">1.6:1 (16:10)</p>
            </div>
            <div className="p-3 bg-gray-800/50 rounded-lg">
              <p className="text-gray-400">Color Space</p>
              <p className="text-white font-mono">sRGB</p>
            </div>
          </div>
        </div>
      </section>

      {/* Export Formats Reference */}
      <section className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-gray-200 mb-4">Export Formats Reference</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-gray-400">
                <th className="pb-2 font-medium">Format</th>
                <th className="pb-2 font-medium">Dimensions</th>
                <th className="pb-2 font-medium">DPI</th>
                <th className="pb-2 font-medium">Color</th>
                <th className="pb-2 font-medium">Use Case</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              <tr className="border-b border-gray-800/50">
                <td className="py-2 font-medium text-amber-400">Theatrical</td>
                <td className="py-2">8100 × 12000 (27" × 40")</td>
                <td className="py-2">300</td>
                <td className="py-2">CMYK</td>
                <td className="py-2">Print one-sheet</td>
              </tr>
              <tr className="border-b border-gray-800/50">
                <td className="py-2 font-medium text-blue-400">Deck</td>
                <td className="py-2">1440 × 900</td>
                <td className="py-2">72</td>
                <td className="py-2">sRGB</td>
                <td className="py-2">Studio display</td>
              </tr>
              <tr className="border-b border-gray-800/50">
                <td className="py-2 font-medium text-pink-400">Social</td>
                <td className="py-2">2160 × 3240 (2:3)</td>
                <td className="py-2">72</td>
                <td className="py-2">sRGB</td>
                <td className="py-2">Instagram/Feed</td>
              </tr>
              <tr className="border-b border-gray-800/50">
                <td className="py-2 font-medium text-green-400">Story</td>
                <td className="py-2">1080 × 1920 (9:16)</td>
                <td className="py-2">72</td>
                <td className="py-2">sRGB</td>
                <td className="py-2">Stories/Reels</td>
              </tr>
              <tr>
                <td className="py-2 font-medium text-purple-400">Animated</td>
                <td className="py-2">1080 × 1920</td>
                <td className="py-2">24 fps</td>
                <td className="py-2">sRGB</td>
                <td className="py-2">MP4/GIF/WebM</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* BrandlyPosterAPI Documentation */}
      <section className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
        <h3 className="text-lg font-semibold text-gray-200 mb-4">window.BrandlyPosterAPI</h3>
        <p className="text-gray-400 mb-4">Exposed globally for MCP server iframe communication:</p>
        <pre className="bg-gray-950 p-4 rounded-lg border border-gray-800 text-sm text-gray-300 overflow-x-auto">
{`interface BrandlyPosterAPI {
  createPoster(params: CreatePosterParams): Promise<MasterPromptResult>;
  getPrompt(): string | null;
  export(format: string): Promise<{ success: boolean; path?: string; error?: string }>;
  loadProject(projectId: string): Promise<ProjectManifest | null>;
  setReferenceImage(imageUrl: string): void;
  onPosterUpdate(callback: (poster: MasterPromptResult) => void): () => void;
}`}</pre>
      </section>

      {/* Save Button */}
      <div className="flex justify-end pt-4 border-t border-gray-800">
        <button
          onClick={handleSaveConfig}
          className="px-6 py-3 bg-amber-400 text-gray-950 font-semibold rounded-lg hover:bg-amber-300 transition-colors"
        >
          Save Configuration
        </button>
      </div>

      {/* Version Info */}
      <div className="text-center text-xs text-gray-500">
        <p>BrandlyPoster Studio v0.1.0</p>
        <p>MCP-Controlled Poster Studio — Deck: 1440×900 sRGB</p>
      </div>
    </div>
  );
}