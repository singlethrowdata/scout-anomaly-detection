/// <reference types="vite/client" />

// [R13] Vite environment variable types
// → provides: env-var-type-safety
interface ImportMetaEnv {
  readonly VITE_GCP_PROJECT_ID: string
  readonly VITE_GCS_CONFIG_BUCKET: string
  readonly VITE_GCS_RESULTS_BUCKET: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}