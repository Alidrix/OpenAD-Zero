export interface Report {
  id: string
  mission_id: string
  status: string
  title: string
  markdown_path?: string | null
  html_path?: string | null
  metadata_path?: string | null
  sections_json?: Record<string, unknown> | null
  generated_at: string
}

export interface ReportPreview {
  format: string
  content: string
  truncated: boolean
}
