import axios, { type AxiosError } from "axios";
import apiClient from "../api-client";

export type CVExtractionStatus = "UPLOADED" | "EXTRACTING" | "COMPLETED" | "FAILED";

export interface LanguageExtracted {
  language: string;
  proficiency: string;
}

export interface DegreeExtracted {
  degree: string;
  institution: string;
  year?: number;
  gpa?: string;
}

export interface AcademicInfoExtracted {
  degrees?: DegreeExtracted[];
  certifications?: string[];
}

export interface ExperienceExtracted {
  title: string;
  company: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface CVExtractionSession {
  id: number;
  file_name: string;
  file_size: number;
  extracted_text: string;
  academic_info: AcademicInfoExtracted;
  skills: string[];
  interests: string[];
  languages: LanguageExtracted[];
  experience: ExperienceExtracted[];
  confidence_score: number | null;
  status: CVExtractionStatus;
  error_message: string;
  created_at: string;
  updated_at: string;
  extracted_at: string | null;
  extracted_profile_data?: {
    academic_info: AcademicInfoExtracted;
    skills: string[];
    interests: string[];
    languages: string[]; // Note: UserProfile expects string[], not LanguageExtracted[]
  };
}

export interface CVExtractionStatusResponse {
  status: CVExtractionStatus;
  is_complete: boolean;
  is_failed: boolean;
  error_message: string | null;
}

export interface ApplyExtractionResponse {
  message: string;
  profile_updated: boolean;
}

export interface ApiError {
  detail?: string;
  cv_file?: string[];
  error?: string;
  [key: string]: any;
}

export const cvExtractionApi = {
  /**
   * Upload CV file and initiate extraction
   * @param file - CV file (PDF or DOCX)
   * @param sync - If true, process synchronously (for development/testing)
   */
  async uploadCV(file: File, sync: boolean = false): Promise<CVExtractionSession> {
    const formData = new FormData();
    formData.append("cv_file", file);

    // Backend endpoint: /api/cv-extraction/upload/
    // Query param: ?sync=true for synchronous processing
    const url = sync 
      ? `/cv-extraction/upload/?sync=true` 
      : `/cv-extraction/upload/`; // async mode - triggers Celery task
    
    console.log("Uploading CV to:", url, "sync:", sync);
    const response = await apiClient.post<CVExtractionSession>(url, formData);
    console.log("Upload response:", response.data);
    return response.data;
  },

  /**
   * Get list of all CV extraction sessions for the current user
   */
  async getSessions(): Promise<CVExtractionSession[]> {
    const response = await apiClient.get<CVExtractionSession[]>("/cv-extraction/sessions/");
    return response.data;
  },

  /**
   * Get a specific CV extraction session with full details
   */
  async getSession(sessionId: number): Promise<CVExtractionSession> {
    const response = await apiClient.get<CVExtractionSession>(
      `/cv-extraction/sessions/${sessionId}/`
    );
    return response.data;
  },

  /**
   * Get extraction status (for polling)
   */
  async getSessionStatus(sessionId: number): Promise<CVExtractionStatusResponse> {
    const response = await apiClient.get<CVExtractionStatusResponse>(
      `/cv-extraction/sessions/${sessionId}/status/`
    );
    return response.data;
  },

  /**
   * Update extracted data before applying to profile
   * Only allowed when status is COMPLETED or FAILED
   */
  async updateSession(
    sessionId: number,
    data: {
      academic_info?: AcademicInfoExtracted;
      skills?: string[];
      interests?: string[];
      languages?: LanguageExtracted[];
      experience?: ExperienceExtracted[];
    }
  ): Promise<CVExtractionSession> {
    const response = await apiClient.patch<CVExtractionSession>(
      `/cv-extraction/sessions/${sessionId}/`,
      data
    );
    return response.data;
  },

  /**
   * Apply extracted CV data to user profile
   * Only works for sessions with status COMPLETED
   */
  async applyToProfile(sessionId: number): Promise<ApplyExtractionResponse> {
    const response = await apiClient.patch<ApplyExtractionResponse>(
      `/cv-extraction/sessions/${sessionId}/apply/`,
      {}
    );
    return response.data;
  },

  extractError(error: unknown): ApiError {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ApiError>;
      const errorData = axiosError.response?.data;

      if (errorData) {
        return errorData;
      }

      if (error.message) {
        return { detail: error.message };
      }

      if (error.code === "ERR_NETWORK") {
        return { detail: "Network error. Please check your connection." };
      }

      return { detail: "An unexpected error occurred" };
    }
    return { detail: "An unexpected error occurred" };
  },
};

