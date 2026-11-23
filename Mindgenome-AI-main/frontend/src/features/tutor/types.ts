import type { Citation } from "@/api/schemas";

export interface ChatMessage {
  id: string;
  sender: "user" | "tutor";
  text: string;
  timestamp: string;
  grounded?: boolean;
  confidence?: "high" | "medium" | "low";
  citations?: Citation[];
  conceptIds?: string[];
  followups?: string[];
}
