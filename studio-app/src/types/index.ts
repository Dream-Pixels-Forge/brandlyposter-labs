/** BrandlyPoster-Labs Studio App Types */

export interface SubjectProfile {
  subject_id: string;
  name: string;
  reference_images: string[];
  face_embedding?: number[];
  likeness_threshold: number;
  earring_baseline?: {
    left_ear: { x: number; y: number; radius: number };
    right_ear: { x: number; y: number; radius: number };
    gold_hoop: boolean;
  };
  story: string;
  outfit: string;
  created_at: string;
}

export interface ProjectManifest {
  project_id: string;
  subject_id: string;
  poster_id: string;
  genre: string;
  master_prompt: string;
  qa_score: string;
  qa_passed: boolean;
  variants: ProjectVariant[];
  approved: boolean;
  approved_version?: string;
  created_at: string;
}

export interface ProjectVariant {
  format: string;
  file: string;
  specs: ExportSpec;
  path: string;
}

export interface ExportSpec {
  size: string;
  dpi: number;
  color: string;
  pixels?: string;
  fps?: number;
  formats?: string[];
}

export interface GenreConfig {
  name: string;
  backgrounds: string[];
  palette: string[];
  lighting: string;
}

export interface FontFamilies {
  titles: string[];
  subtitles: string[];
  taglines: string[];
  billing: string[];
}

export interface MasterPromptResult {
  master_prompt: string;
  genre_config: GenreConfig;
  subject_id: string;
  qa_checklist: string[];
  variant_plan: {
    title: string;
    subtitle: string;
    tagline: string;
    genre: string;
    resolution: string;
  };
}

export interface QAResult {
  score: string;
  checks: Record<string, { pass: boolean; [key: string]: unknown }>;
  pass: boolean;
}

export interface ScanIssueResult {
  issues: Record<string, { pass?: boolean; issue?: string; severity?: string; fix_suggestion?: string; fix_prompt?: string; [key: string]: unknown }>;
  scan_frames: ScanFrame[];
  annotated_image_path: string;
  summary: {
    total_checks: number;
    passed: number;
    failed: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  fix_prompt: string;
  fix_categories: string[];
  animation_frames?: string[];
}

export interface ScanFrame {
  region: string;
  bbox: [number, number, number, number];
  issue: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'none';
  fix_prompt?: string;
  note?: string;
}

export interface BrandlyPosterAPI {
  createPoster: (params: CreatePosterParams) => Promise<MasterPromptResult>;
  getPrompt: () => string | null;
  export: (format: string) => Promise<{ success: boolean; path?: string; error?: string }>;
  loadProject: (projectId: string) => Promise<ProjectManifest | null>;
  setReferenceImage: (imageUrl: string) => void;
  onPosterUpdate: (callback: (poster: MasterPromptResult) => void) => () => void;
}

export interface CreatePosterParams {
  subjectId: string;
  genre: string;
  title: string;
  subtitle: string;
  tagline: string;
  story?: string;
  outfit?: string;
  fixEarrings?: boolean;
  resolution?: string;
}

export interface PostMessagePayload {
  type: 'CREATE_POSTER' | 'LOAD_PROJECT' | 'EXPORT' | 'SET_REFERENCE' | 'GET_PROMPT';
  payload: unknown;
  requestId: string;
}

export interface PostMessageResponse {
  type: 'RESPONSE';
  requestId: string;
  success: boolean;
  data?: unknown;
  error?: string;
}

// Window augmentation for BrandlyPosterAPI
declare global {
  interface Window {
    BrandlyPosterAPI: BrandlyPosterAPI;
  }
}