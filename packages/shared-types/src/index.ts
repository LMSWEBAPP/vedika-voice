/**
 * Veyra Voice Shared Domain Types & Contracts
 */

export type CallStatus =
  | 'QUEUED'
  | 'INITIATING'
  | 'RINGING'
  | 'CONNECTED'
  | 'AI_GREETING'
  | 'IN_PROGRESS'
  | 'PAUSED'
  | 'COMPLETED'
  | 'FAILED'
  | 'NO_ANSWER'
  | 'BUSY'
  | 'CANCELLED';

export type LeadStatus =
  | 'NEW'
  | 'QUEUED'
  | 'CALLING'
  | 'CONTACTED'
  | 'INTERESTED'
  | 'NOT_INTERESTED'
  | 'CALLBACK'
  | 'NO_ANSWER'
  | 'INVALID'
  | 'DO_NOT_CALL';

export type CampaignStatus =
  | 'DRAFT'
  | 'SCHEDULED'
  | 'ACTIVE'
  | 'PAUSED'
  | 'COMPLETED'
  | 'CANCELLED';

export type QuestionType =
  | 'text'
  | 'number'
  | 'boolean'
  | 'single_choice'
  | 'multiple_choice'
  | 'date'
  | 'time'
  | 'phone'
  | 'email'
  | 'rating';

export interface QuestionCondition {
  depends_on_question_id: string;
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'in';
  expected_value: any;
}

export interface ScriptQuestion {
  id: string;
  text: string;
  type: QuestionType;
  required: boolean;
  options?: string[]; // For single_choice and multiple_choice
  validation?: {
    min?: number;
    max?: number;
    regex?: string;
  };
  condition?: QuestionCondition;
  description?: string;
}

export interface CampaignScript {
  opening: string;
  objective: string;
  questions: ScriptQuestion[];
  closing: string;
  fallback_response?: string;
  ai_disclosure?: string;
}

export interface TranscriptTurn {
  id?: string;
  speaker: 'ai' | 'user' | 'system';
  text: string;
  timestamp: string;
  language: string;
  confidence?: number;
  metadata?: Record<string, any>;
}

export interface ExtractedAnswer {
  question_id: string;
  question_text: string;
  raw_answer: string;
  extracted_value: any;
  is_valid: boolean;
  confidence: number;
}

export interface DashboardMetrics {
  total_leads: number;
  calls_made: number;
  answered_calls: number;
  completed_calls: number;
  interested_leads: number;
  not_interested_leads: number;
  no_answer_calls: number;
  average_duration_seconds: number;
  completion_rate: number;
  conversion_rate: number;
}
