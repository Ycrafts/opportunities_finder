"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  Upload,
  Loader2,
  CheckCircle2,
  XCircle,
  Eye,
  Edit,
  Save,
  X,
  AlertCircle,
} from "lucide-react";
import { cvExtractionApi, type CVExtractionSession, type CVExtractionStatus } from "@/lib/api/cv-extraction";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { FadeIn } from "@/components/animations/fade-in";
import { useRouter } from "next/navigation";

interface CVUploadSectionProps {
  onApplied?: () => void;
  initialSession?: CVExtractionSession | null;
}

export function CVUploadSection({ onApplied, initialSession }: CVUploadSectionProps) {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [session, setSession] = useState<CVExtractionSession | null>(initialSession || null);
  const [isReviewing, setIsReviewing] = useState(initialSession?.status === "COMPLETED" || false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Polling function
  const startPolling = (sessionId: number) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const status = await cvExtractionApi.getSessionStatus(sessionId);
        
        if (status.is_complete || status.is_failed) {
          // Stop polling and fetch full session
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          
          const fullSession = await cvExtractionApi.getSession(sessionId);
          setSession(fullSession);
          
          if (status.is_complete) {
            toast.success("CV extraction completed!");
            setIsReviewing(true);
          } else if (status.is_failed) {
            toast.error("CV extraction failed: " + (status.error_message || "Unknown error"));
          }
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
    }, 2000); // Poll every 2 seconds
  };

  // Update session when initialSession changes
  useEffect(() => {
    if (initialSession) {
      setSession(initialSession);
      if (initialSession.status === "COMPLETED") {
        setIsReviewing(true);
      } else if (initialSession.status !== "FAILED") {
        // Start polling if session is still processing
        startPolling(initialSession.id);
      }
    }
  }, [initialSession]);

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => cvExtractionApi.uploadCV(file, false), // async by default
    onSuccess: (data) => {
      setSession(data);
      setFile(null);
      toast.success("CV uploaded successfully. Extraction in progress...");
      
      // Start polling if status is not completed
      if (data.status !== "COMPLETED" && data.status !== "FAILED") {
        startPolling(data.id);
      }
    },
    onError: (error) => {
      const code = (error as any)?.response?.data?.code;
      const upgradeUrl = (error as any)?.response?.data?.upgrade_url;
      const apiError = cvExtractionApi.extractError(error);
      toast.error(apiError.detail || apiError.cv_file?.[0] || "Failed to upload CV");
      if (code === "premium_required" && upgradeUrl) {
        router.push(upgradeUrl);
      }
    },
  });

  // Update session mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      cvExtractionApi.updateSession(id, data),
    onSuccess: (updatedSession) => {
      setSession(updatedSession);
      toast.success("Extracted data updated");
    },
    onError: (error) => {
      const apiError = cvExtractionApi.extractError(error);
      toast.error(apiError.detail || "Failed to update extracted data");
    },
  });

  // Apply to profile mutation
  const applyMutation = useMutation({
    mutationFn: (sessionId: number) => cvExtractionApi.applyToProfile(sessionId),
    onSuccess: () => {
      toast.success("CV data applied to profile successfully!");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      setSession(null);
      setIsReviewing(false);
      if (onApplied) onApplied();
    },
    onError: (error) => {
      const apiError = cvExtractionApi.extractError(error);
      toast.error(apiError.detail || "Failed to apply CV data to profile");
    },
  });

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      const validTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
      const validExtensions = [".pdf", ".docx"];
      const fileExtension = selectedFile.name.toLowerCase().substring(selectedFile.name.lastIndexOf("."));
      
      if (!validTypes.includes(selectedFile.type) && !validExtensions.includes(fileExtension)) {
        toast.error("Only PDF and DOCX files are supported");
        return;
      }

      // Validate file size (10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        toast.error("File size must be less than 10MB");
        return;
      }

      setFile(selectedFile);
    }
  };

  const handleUpload = () => {
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const handleReview = () => {
    if (session) {
      setIsReviewing(true);
    }
  };

  const handleApply = () => {
    if (session) {
      applyMutation.mutate(session.id);
    }
  };

  const getStatusBadge = (status: CVExtractionStatus) => {
    switch (status) {
      case "UPLOADED":
        return <Badge variant="secondary">Uploaded</Badge>;
      case "EXTRACTING":
        return (
          <Badge variant="secondary" className="gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            Extracting...
          </Badge>
        );
      case "COMPLETED":
        return (
          <Badge variant="default" className="bg-green-600 gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Completed
          </Badge>
        );
      case "FAILED":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
    }
  };

  return (
    <FadeIn>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Upload CV for Auto-Fill
          </CardTitle>
          <CardDescription>
            Upload your CV and we'll automatically extract your information to fill your profile
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Upload */}
          {!session && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="cv-upload">CV File (PDF or DOCX, max 10MB)</Label>
                <Input
                  id="cv-upload"
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileSelect}
                  className="mt-2"
                />
                {file && (
                  <p className="mt-2 text-sm text-muted-foreground">
                    Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>
              <Button
                onClick={handleUpload}
                disabled={!file || uploadMutation.isPending}
                className="w-full"
              >
                {uploadMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload CV
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Session Status */}
          {session && !isReviewing && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{session.file_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(session.file_size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                {getStatusBadge(session.status)}
              </div>

              {session.status === "COMPLETED" && (
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <Button onClick={handleReview} variant="outline" className="flex-1">
                      <Eye className="mr-2 h-4 w-4" />
                      Review & Apply
                    </Button>
                    <Button
                      onClick={() => {
                        setSession(null);
                        setIsReviewing(false);
                        if (fileInputRef.current) fileInputRef.current.value = "";
                      }}
                      variant="ghost"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}

              {session.status === "FAILED" && (
                <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/10">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                    <div className="flex-1">
                      <p className="font-medium text-destructive">Extraction Failed</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {session.error_message || "Unknown error occurred"}
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={() => {
                      setSession(null);
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                    variant="outline"
                    size="sm"
                    className="mt-3"
                  >
                    Try Again
                  </Button>
                </div>
              )}

              {session.status === "EXTRACTING" && (
                <div className="p-4 border rounded-lg bg-muted/30">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">
                      AI is extracting information from your CV. This may take a few moments...
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Review Extracted Data */}
          {session && isReviewing && (
            <CVExtractionReview
              session={session}
              onCancel={() => setIsReviewing(false)}
              onApply={handleApply}
              onUpdate={(data) => {
                if (session) {
                  updateMutation.mutate({ id: session.id, data });
                }
              }}
              isApplying={applyMutation.isPending}
              isUpdating={updateMutation.isPending}
            />
          )}
        </CardContent>
      </Card>
    </FadeIn>
  );
}

interface CVExtractionReviewProps {
  session: CVExtractionSession;
  onCancel: () => void;
  onApply: () => void;
  onUpdate: (data: any) => void;
  isApplying: boolean;
  isUpdating: boolean;
}

function CVExtractionReview({
  session,
  onApply,
  onCancel,
  onUpdate,
  isApplying,
  isUpdating,
}: CVExtractionReviewProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState({
    academic_info: session.academic_info || {},
    skills: session.skills || [],
    interests: session.interests || [],
    languages: session.languages || [],
  });

  // Update editedData when session changes (after save)
  useEffect(() => {
    setEditedData({
      academic_info: session.academic_info || {},
      skills: session.skills || [],
      interests: session.interests || [],
      languages: session.languages || [],
    });
  }, [session]);

  const [skillInput, setSkillInput] = useState("");
  const [interestInput, setInterestInput] = useState("");
  const [languageInput, setLanguageInput] = useState("");
  const [proficiencyInput, setProficiencyInput] = useState("");

  const handleSave = () => {
    onUpdate(editedData);
    setIsEditing(false);
  };

  const addSkill = () => {
    if (skillInput.trim() && !editedData.skills.includes(skillInput.trim())) {
      setEditedData({
        ...editedData,
        skills: [...editedData.skills, skillInput.trim()],
      });
      setSkillInput("");
    }
  };

  const removeSkill = (skill: string) => {
    setEditedData({
      ...editedData,
      skills: editedData.skills.filter((s) => s !== skill),
    });
  };

  const addInterest = () => {
    if (interestInput.trim() && !editedData.interests.includes(interestInput.trim())) {
      setEditedData({
        ...editedData,
        interests: [...editedData.interests, interestInput.trim()],
      });
      setInterestInput("");
    }
  };

  const removeInterest = (interest: string) => {
    setEditedData({
      ...editedData,
      interests: editedData.interests.filter((i) => i !== interest),
    });
  };

  const addLanguage = () => {
    if (languageInput.trim()) {
      const newLang = {
        language: languageInput.trim(),
        proficiency: proficiencyInput.trim() || "Fluent",
      };
      setEditedData({
        ...editedData,
        languages: [...editedData.languages, newLang],
      });
      setLanguageInput("");
      setProficiencyInput("");
    }
  };

  const removeLanguage = (index: number) => {
    setEditedData({
      ...editedData,
      languages: editedData.languages.filter((_, i) => i !== index),
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Review & Edit Extracted Data</h3>
        <div className="flex gap-2">
          {!isEditing ? (
            <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={handleSave} disabled={isUpdating}>
              {isUpdating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Changes
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Academic Info */}
      {editedData.academic_info?.degrees && editedData.academic_info.degrees.length > 0 && (
        <div className="p-4 border rounded-lg">
          <Label className="text-sm font-medium mb-2 block">Education</Label>
          <div className="space-y-2">
            {editedData.academic_info.degrees.map((degree, idx) => (
              <div key={idx} className="text-sm">
                <p className="font-medium">{degree.degree}</p>
                <p className="text-muted-foreground">
                  {degree.institution}
                  {degree.year && ` • ${degree.year}`}
                  {degree.gpa && ` • GPA: ${degree.gpa}`}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skills */}
      <div className="p-4 border rounded-lg">
        <Label className="text-sm font-medium mb-2 block">Skills</Label>
        {isEditing ? (
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addSkill();
                  }
                }}
                placeholder="Add a skill"
                className="flex-1"
              />
              <Button type="button" onClick={addSkill} variant="outline" size="sm">
                Add
              </Button>
            </div>
            {editedData.skills.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {editedData.skills.map((skill, idx) => (
                  <Badge key={idx} variant="secondary" className="gap-1">
                    {skill}
                    <button
                      type="button"
                      onClick={() => removeSkill(skill)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ) : (
          editedData.skills.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {editedData.skills.map((skill, idx) => (
                <Badge key={idx} variant="secondary">
                  {skill}
                </Badge>
              ))}
            </div>
          )
        )}
      </div>

      {/* Languages */}
      <div className="p-4 border rounded-lg">
        <Label className="text-sm font-medium mb-2 block">Languages</Label>
        {isEditing ? (
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input
                value={languageInput}
                onChange={(e) => setLanguageInput(e.target.value)}
                placeholder="Language"
                className="flex-1"
              />
              <Input
                value={proficiencyInput}
                onChange={(e) => setProficiencyInput(e.target.value)}
                placeholder="Proficiency (optional)"
                className="flex-1"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addLanguage();
                  }
                }}
              />
              <Button type="button" onClick={addLanguage} variant="outline" size="sm">
                Add
              </Button>
            </div>
            {editedData.languages.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {editedData.languages.map((lang, idx) => (
                  <Badge key={idx} variant="secondary" className="gap-1">
                    {lang.language}
                    {lang.proficiency && ` (${lang.proficiency})`}
                    <button
                      type="button"
                      onClick={() => removeLanguage(idx)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ) : (
          editedData.languages.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {editedData.languages.map((lang, idx) => (
                <Badge key={idx} variant="secondary">
                  {lang.language}
                  {lang.proficiency && ` (${lang.proficiency})`}
                </Badge>
              ))}
            </div>
          )
        )}
      </div>

      {/* Interests */}
      <div className="p-4 border rounded-lg">
        <Label className="text-sm font-medium mb-2 block">Interests</Label>
        {isEditing ? (
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input
                value={interestInput}
                onChange={(e) => setInterestInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addInterest();
                  }
                }}
                placeholder="Add an interest"
                className="flex-1"
              />
              <Button type="button" onClick={addInterest} variant="outline" size="sm">
                Add
              </Button>
            </div>
            {editedData.interests.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {editedData.interests.map((interest, idx) => (
                  <Badge key={idx} variant="secondary" className="gap-1">
                    {interest}
                    <button
                      type="button"
                      onClick={() => removeInterest(interest)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ) : (
          editedData.interests.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {editedData.interests.map((interest, idx) => (
                <Badge key={idx} variant="secondary">
                  {interest}
                </Badge>
              ))}
            </div>
          )
        )}
      </div>

      {/* Experience (for display only, not applied to profile) */}
      {session.experience && session.experience.length > 0 && (
        <div className="p-4 border rounded-lg">
          <Label className="text-sm font-medium mb-2 block">Experience (Preview)</Label>
          <div className="space-y-3">
            {session.experience.slice(0, 3).map((exp, idx) => (
              <div key={idx} className="text-sm">
                <p className="font-medium">{exp.title}</p>
                <p className="text-muted-foreground">
                  {exp.company}
                  {exp.start_date && ` • ${exp.start_date}`}
                  {exp.end_date && ` - ${exp.end_date}`}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        <Button onClick={onCancel} variant="outline" className="flex-1" disabled={isApplying}>
          Cancel
        </Button>
        <Button onClick={onApply} className="flex-1" disabled={isApplying}>
          {isApplying ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Applying...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Apply to Profile
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

