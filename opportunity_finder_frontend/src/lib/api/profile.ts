import axios, { type AxiosError } from "axios";
import apiClient from "../api-client";

// Academic info can be in two formats:
// 1. Simple: { degree, university, graduation_year }
// 2. Complex: { degrees: [{ degree, institution, year, gpa }], certifications: [] }
export interface AcademicInfo {
  // Simple format
  degree?: string;
  university?: string;
  graduation_year?: number;
  seeking?: string;
  field?: string;
  institution?: string;
  
  // Complex format
  degrees?: Array<{
    degree: string;
    institution: string;
    year?: number;
    gpa?: string;
  }>;
  certifications?: string[];
  
  // Contact info (sometimes stored here)
  contact?: {
    phone?: string;
    address?: string;
  };
  
  [key: string]: any; // Allow additional properties
}

export interface UserProfile {
  full_name: string;
  telegram_id: number | null;
  cv_file: string | null; // URL to CV file
  cv_text: string;
  academic_info: AcademicInfo;
  skills: string[];
  interests: string[];
  languages: string[];
  matching_doc_version: string;
  matching_profile_json: Record<string, any>;
  matching_profile_text: string;
  matching_profile_updated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpdateProfileRequest {
  full_name?: string;
  telegram_id?: number | null;
  cv_file?: File | null;
  cv_text?: string;
  academic_info?: AcademicInfo;
  skills?: string[];
  interests?: string[];
  languages?: string[];
}

export interface ApiError {
  detail?: string;
  full_name?: string[];
  telegram_id?: string[];
  cv_file?: string[];
  cv_text?: string[];
  academic_info?: string[];
  skills?: string[];
  interests?: string[];
  languages?: string[];
  non_field_errors?: string[];
  [key: string]: any;
}

export const profileApi = {
  async getProfile(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>("/profile/me/");
    return response.data;
  },

  async updateProfile(data: UpdateProfileRequest): Promise<UserProfile> {
    // Check if we need to send multipart/form-data (if cv_file is present)
    const hasFile = data.cv_file instanceof File;
    
    let formData: FormData | UpdateProfileRequest;
    let config: { headers?: Record<string, string | undefined> } = {};
    
    if (hasFile) {
      // Use FormData for file upload
      formData = new FormData();
      
      if (data.full_name !== undefined) formData.append("full_name", data.full_name);
      if (data.telegram_id !== undefined && data.telegram_id !== null) {
        formData.append("telegram_id", data.telegram_id.toString());
      }
      if (data.cv_file) formData.append("cv_file", data.cv_file);
      if (data.cv_text !== undefined) formData.append("cv_text", data.cv_text);
      if (data.academic_info !== undefined) {
        formData.append("academic_info", JSON.stringify(data.academic_info));
      }
      if (data.skills !== undefined) {
        formData.append("skills", JSON.stringify(data.skills));
      }
      if (data.interests !== undefined) {
        formData.append("interests", JSON.stringify(data.interests));
      }
      if (data.languages !== undefined) {
        formData.append("languages", JSON.stringify(data.languages));
      }
      
      // Headers will be handled by the request interceptor for FormData
    } else {
      // Use JSON for regular updates
      formData = { ...data };
      // Remove cv_file if it's null (don't send it)
      if (formData.cv_file === null) {
        delete formData.cv_file;
      }
    }
    
    const response = await apiClient.patch<UserProfile>("/profile/me/", formData, config);
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

