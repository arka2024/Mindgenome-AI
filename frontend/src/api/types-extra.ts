export type UploadAccepted = {
  document_id: string;
  job_id: string;
  status: "queued";
};

export type DocumentRecord = {
  id: string;
  filename: string;
  status: "uploaded" | "processing" | "ready" | "failed" | "rejected";
  created_at: string;
  page_count?: number | null;
  job_id?: string;
  is_low_text?: boolean;
  low_text_warning?: string | null;
  chapters?: Array<{ id: string; title: string; page_start: number; page_end: number }>;
};
