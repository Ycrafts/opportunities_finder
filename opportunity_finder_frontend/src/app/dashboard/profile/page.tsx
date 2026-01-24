"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Users,
  Bell,
  Settings,
  Target,
  Edit,
  Save,
  X,
  Download,
  GraduationCap,
  Code,
  Heart,
  Languages,
  User,
  Upload,
  Loader2,
  Sliders,
  Crown,
} from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { profileApi, type UserProfile, type UpdateProfileRequest, type LanguageEntry } from "@/lib/api/profile";
import { cvExtractionApi, type CVExtractionSession } from "@/lib/api/cv-extraction";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { FadeIn } from "@/components/animations/fade-in";
import { CVUploadSection } from "@/components/profile/cv-upload-section";

const navItems = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Opportunities", href: "/dashboard/opportunities", icon: Briefcase },
  { title: "Matches", href: "/dashboard/matches", icon: Target },
  { title: "Profile", href: "/dashboard/profile", icon: Users },
  { title: "Preferences", href: "/dashboard/preferences", icon: Sliders },
  { title: "Notifications", href: "/dashboard/notifications", icon: Bell, badge: 0 },
  { title: "Settings", href: "/dashboard/settings", icon: Settings },
  { title: "Upgrade", href: "/dashboard/upgrade", icon: Crown },
];

// Helper function to check if profile is empty
function isProfileEmpty(profile: UserProfile | undefined): boolean {
  if (!profile) return true;
  
  const hasName = profile.full_name && profile.full_name.trim().length > 0;
  const hasSkills = profile.skills && profile.skills.length > 0;
  const hasAcademicInfo = profile.academic_info && (
    (profile.academic_info.degrees && profile.academic_info.degrees.length > 0) ||
    profile.academic_info.degree ||
    profile.academic_info.university
  );
  const hasLanguages = profile.languages && profile.languages.length > 0;
  const hasInterests = profile.interests && profile.interests.length > 0;
  const hasCvText = profile.cv_text && profile.cv_text.trim().length > 0;
  
  return !hasName && !hasSkills && !hasAcademicInfo && !hasLanguages && !hasInterests && !hasCvText;
}

export default function ProfilePage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [pendingSession, setPendingSession] = useState<CVExtractionSession | null>(null);

  // Fetch profile
  const {
    data: profile,
    isLoading: profileLoading,
    error: profileError,
  } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.getProfile(),
    enabled: isAuthenticated,
  });

  // Fetch CV extraction sessions to find completed ones that haven't been applied
  const { data: cvSessions } = useQuery({
    queryKey: ["cv-sessions"],
    queryFn: () => cvExtractionApi.getSessions(),
    enabled: isAuthenticated,
  });

  // Find the most recent completed session that hasn't been applied
  useEffect(() => {
    if (cvSessions && cvSessions.length > 0) {
      // Find completed sessions, sorted by most recent
      const completedSessions = cvSessions
        .filter(s => s.status === "COMPLETED")
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      
      if (completedSessions.length > 0) {
        // Check if profile is empty - if so, this session is pending application
        if (profile && isProfileEmpty(profile)) {
          setPendingSession(completedSessions[0]);
        } else {
          setPendingSession(null);
        }
      } else {
        setPendingSession(null);
      }
    } else {
      setPendingSession(null);
    }
  }, [cvSessions, profile]);

  // Update profile mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdateProfileRequest) => profileApi.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["cv-sessions"] });
      toast.success("Profile updated successfully");
      setIsEditing(false);
      setCvFile(null);
      setPendingSession(null);
    },
    onError: (error) => {
      const apiError = profileApi.extractError(error);
      const errorMessage =
        apiError.detail ||
        Object.values(apiError)
          .flat()
          .filter(Boolean)
          .join(", ") ||
        "Failed to update profile";
      toast.error(errorMessage);
    },
  });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || profileLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (profileError) {
    return (
      <DashboardLayout navItems={navItems} >
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              Failed to load profile. Please try again.
            </div>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  const profileEmpty = isProfileEmpty(profile);

  return (
    <DashboardLayout navItems={navItems}>
      <div className="space-y-6">
        {profileEmpty && !pendingSession ? (
          // No profile yet - show upload only
          <FadeIn>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Get Started with Your Profile
                </CardTitle>
                <CardDescription>
                  Upload your CV to automatically fill out your profile information
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CVUploadSection
                  onApplied={() => {
                    queryClient.invalidateQueries({ queryKey: ["profile"] });
                    queryClient.invalidateQueries({ queryKey: ["cv-sessions"] });
                  }}
                />
              </CardContent>
            </Card>
          </FadeIn>
        ) : pendingSession ? (
          // CV uploaded but not applied - show review section
          <FadeIn>
            <div className="space-y-4">
              <div>
                <h2 className="text-2xl font-semibold tracking-tight">Review Your CV Extraction</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Review and approve the extracted information from your CV
                </p>
              </div>
              <CVUploadSection
                initialSession={pendingSession}
                onApplied={() => {
                  queryClient.invalidateQueries({ queryKey: ["profile"] });
                  queryClient.invalidateQueries({ queryKey: ["cv-sessions"] });
                  setPendingSession(null);
                }}
              />
            </div>
          </FadeIn>
        ) : (
          // Profile exists - show normal view/edit
          <>
            <FadeIn>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <h2 className="text-2xl font-semibold tracking-tight">My Profile</h2>
                  <p className="text-sm text-muted-foreground">
                    Manage your profile information and preferences
                  </p>
                </div>
                {!isEditing && (
                  <Button 
                   variant="default"
                    onClick={() => setIsEditing(true)} 
                    className="bg-[#0f9b57] hover:bg-[#0d8a4e] text-white"
                  >
                    <Edit className="mr-2 h-4 w-4 " />
                    Edit Profile
                  </Button>
                )}
              </div>
            </FadeIn>

            {isEditing ? (
              <div className="space-y-6">
                <ProfileEditForm
                  profile={profile!}
                  cvFile={cvFile}
                  setCvFile={setCvFile}
                  onSave={(data) => {
                    updateMutation.mutate(data);
                  }}
                  onCancel={() => {
                    setIsEditing(false);
                    setCvFile(null);
                  }}
                  isSaving={updateMutation.isPending}
                />
              </div>
            ) : (
              <ProfileView profile={profile!} />
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}

const parseStringArrayPayload = (value: string): unknown => {
  try {
    return JSON.parse(value);
  } catch {
    const normalized = value
      .replace(/'/g, '"')
      .replace(/\bNone\b/g, "null")
      .replace(/\bTrue\b/g, "true")
      .replace(/\bFalse\b/g, "false");
    try {
      return JSON.parse(normalized);
    } catch {
      return null;
    }
  }
};

const normalizeStringArray = (value: unknown): string[] => {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.flatMap((entry) => {
      if (typeof entry === "string") {
        const parsed = parseStringArrayPayload(entry);
        if (Array.isArray(parsed)) {
          return parsed.map((item) => (typeof item === "string" ? item : JSON.stringify(item)));
        }
        return [entry];
      }
      return [JSON.stringify(entry)];
    });
  }
  if (typeof value === "string") {
    const parsed = parseStringArrayPayload(value);
    if (Array.isArray(parsed)) {
      return parsed.map((entry) => (typeof entry === "string" ? entry : JSON.stringify(entry)));
    }
    return [value];
  }
  return [];
};


const normalizeLanguageEntries = (value: unknown): LanguageEntry[] => {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.flatMap((entry) => {
      if (typeof entry === "string") {
        const parsed = parseStringArrayPayload(entry);
        if (Array.isArray(parsed)) {
          return parsed.map((item) => {
            if (typeof item === "string") {
              const nestedParsed = parseStringArrayPayload(item);
              if (nestedParsed && typeof nestedParsed === "object" && !Array.isArray(nestedParsed)) {
                return nestedParsed as LanguageEntry;
              }
              return { language: item };
            }
            return item as LanguageEntry;
          });
        }
        if (parsed && typeof parsed === "object") {
          return [parsed as LanguageEntry];
        }
        return [{ language: entry }];
      }
      return [entry as LanguageEntry];
    });
  }
  if (typeof value === "string") {
    const parsed = parseStringArrayPayload(value);
    if (Array.isArray(parsed)) {
      return parsed.map((entry) => {
        if (typeof entry === "string") {
          const nestedParsed = parseStringArrayPayload(entry);
          if (nestedParsed && typeof nestedParsed === "object" && !Array.isArray(nestedParsed)) {
            return nestedParsed as LanguageEntry;
          }
          return { language: entry };
        }
        return entry as LanguageEntry;
      });
    }
    if (parsed && typeof parsed === "object") {
      return [parsed as LanguageEntry];
    }
    return [{ language: value }];
  }
  return [];
};

function ProfileView({ profile }: { profile: UserProfile }) {
  const academicInfo = profile.academic_info || {};
  const degrees = academicInfo.degrees || [];
  const simpleDegree = academicInfo.degree || academicInfo.university;
  const languages = normalizeLanguageEntries(profile.languages);
  const skills = normalizeStringArray(profile.skills);
  const interests = normalizeStringArray(profile.interests);

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <FadeIn>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-muted-foreground">Full Name</Label>
              <p className="mt-1 text-sm font-medium">
                {profile.full_name || "Not set"}
              </p>
            </div>
            {profile.telegram_id && (
              <div>
                <Label className="text-muted-foreground">Telegram ID</Label>
                <p className="mt-1 text-sm font-medium">{profile.telegram_id}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </FadeIn>

      {/* Education */}
      {(degrees.length > 0 || simpleDegree) && (
        <FadeIn delay={0.1}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GraduationCap className="h-5 w-5" />
                Education
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {degrees.length > 0 ? (
                degrees.map((degree, idx) => (
                  <div key={idx} className="space-y-1">
                    <p className="text-sm font-medium">{degree.degree}</p>
                    <p className="text-sm text-muted-foreground">
                      {degree.institution}
                      {degree.year && ` • ${degree.year}`}
                      {degree.gpa && ` • GPA: ${degree.gpa}`}
                    </p>
                  </div>
                ))
              ) : (
                <div className="space-y-1">
                  <p className="text-sm font-medium">
                    {academicInfo.degree || "Not specified"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {academicInfo.university || academicInfo.institution}
                    {academicInfo.graduation_year && ` • ${academicInfo.graduation_year}`}
                  </p>
                </div>
              )}
              {academicInfo.certifications && academicInfo.certifications.length > 0 && (
                <div className="mt-4">
                  <Label className="text-muted-foreground">Certifications</Label>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {academicInfo.certifications.map((cert, idx) => (
                      <Badge key={idx} variant="secondary">
                        {cert}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </FadeIn>
      )}

      {/* Skills */}
      {skills.length > 0 && (
        <FadeIn delay={0.2}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Skills
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {skills.map((skill, idx) => (
                  <Badge key={idx} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </FadeIn>
      )}

      {/* Languages */}
      {languages.length > 0 && (
        <FadeIn delay={0.3}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Languages className="h-5 w-5" />
                Languages
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {languages.map((lang, idx) => (
                  <Badge key={idx} variant="secondary">
                    {lang.language}
                    {lang.proficiency && ` (${lang.proficiency})`}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </FadeIn>
      )}

      {/* Interests */}
      {interests.length > 0 && (
        <FadeIn delay={0.4}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="h-5 w-5" />
                Interests
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {interests.map((interest, idx) => (
                  <Badge key={idx} variant="secondary">
                    {interest}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </FadeIn>
      )}

      {/* CV */}
      <FadeIn delay={0.5}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              CV / Resume
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {profile.cv_file ? (
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-sm font-medium">CV File</p>
                  <p className="text-sm text-muted-foreground">
                    {profile.cv_file.split("/").pop()}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  asChild
                >
                  <a href={profile.cv_file} target="_blank" rel="noopener noreferrer">
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </a>
                </Button>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No CV uploaded</p>
            )}
            {profile.cv_text && (
              <div>
                <Label className="text-muted-foreground">CV Text</Label>
                <div className="mt-2 max-h-48 overflow-y-auto rounded-md border border-border/60 bg-muted/30 p-3 text-sm">
                  <pre className="whitespace-pre-wrap font-sans">
                    {profile.cv_text.substring(0, 500)}
                    {profile.cv_text.length > 500 && "..."}
                  </pre>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </FadeIn>
    </div>
  );
}

interface ProfileEditFormProps {
  profile: UserProfile;
  cvFile: File | null;
  setCvFile: (file: File | null) => void;
  onSave: (data: UpdateProfileRequest) => void;
  onCancel: () => void;
  isSaving: boolean;
}

function ProfileEditForm({
  profile,
  cvFile,
  setCvFile,
  onSave,
  onCancel,
  isSaving,
}: ProfileEditFormProps) {
  const initialLanguages: LanguageEntry[] = normalizeLanguageEntries(profile.languages);
  const initialSkills = normalizeStringArray(profile.skills);
  const initialInterests = normalizeStringArray(profile.interests);
  const [formData, setFormData] = useState<UpdateProfileRequest>({
    full_name: profile.full_name || "",
    telegram_id: profile.telegram_id || null,
    cv_text: profile.cv_text || "",
    academic_info: profile.academic_info || {},
    skills: initialSkills,
    interests: initialInterests,
    languages: initialLanguages,
  });

  const [skillInput, setSkillInput] = useState("");
  const [interestInput, setInterestInput] = useState("");
  const [languageInput, setLanguageInput] = useState("");
  const [proficiencyInput, setProficiencyInput] = useState("");

  const academicInfo = formData.academic_info || {};
  // Check for both simple format (degree, university) and complex format (degrees array)
  const degrees = academicInfo.degrees || [];
  const firstDegree = degrees.length > 0 ? degrees[0] : null;
  
  const [academicData, setAcademicData] = useState({
    degree: academicInfo.degree || firstDegree?.degree || "",
    university: academicInfo.university || academicInfo.institution || firstDegree?.institution || "",
    graduation_year: academicInfo.graduation_year 
      ? String(academicInfo.graduation_year) 
      : (firstDegree?.year ? String(firstDegree.year) : ""),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Preserve degrees array if it exists, otherwise use simple format
    const updatedAcademicInfo: typeof academicInfo = {
      ...academicInfo,
      degree: academicData.degree,
      university: academicData.university,
      institution: academicData.university,
      graduation_year: academicData.graduation_year
        ? parseInt(academicData.graduation_year)
        : undefined,
    };

    // If we have degrees array, update the first degree with the form data
    if (degrees.length > 0) {
      updatedAcademicInfo.degrees = [
        {
          ...degrees[0],
          degree: academicData.degree || degrees[0].degree,
          institution: academicData.university || degrees[0].institution,
          year: academicData.graduation_year 
            ? parseInt(academicData.graduation_year) 
            : degrees[0].year,
        },
        ...degrees.slice(1), // Keep other degrees if any
      ];
    }
    
    const updateData: UpdateProfileRequest = {
      ...formData,
      cv_file: cvFile,
      academic_info: updatedAcademicInfo,
    };

    onSave(updateData);
  };

  const addSkill = () => {
    if (skillInput.trim() && !formData.skills?.includes(skillInput.trim())) {
      setFormData({
        ...formData,
        skills: [...(formData.skills || []), skillInput.trim()],
      });
      setSkillInput("");
    }
  };

  const removeSkill = (skill: string) => {
    setFormData({
      ...formData,
      skills: formData.skills?.filter((s) => s !== skill) || [],
    });
  };

  const addInterest = () => {
    if (interestInput.trim() && !formData.interests?.includes(interestInput.trim())) {
      setFormData({
        ...formData,
        interests: [...(formData.interests || []), interestInput.trim()],
      });
      setInterestInput("");
    }
  };

  const removeInterest = (interest: string) => {
    setFormData({
      ...formData,
      interests: formData.interests?.filter((i) => i !== interest) || [],
    });
  };

  const addLanguage = () => {
    const language = languageInput.trim();
    const proficiency = proficiencyInput.trim();
    if (!language) return;
    const nextEntry: LanguageEntry = {
      language,
      proficiency: proficiency || undefined,
    };
    const existing = (formData.languages || []) as LanguageEntry[];
    if (existing.some((entry) => entry.language.toLowerCase() === language.toLowerCase())) {
      return;
    }
    setFormData({
      ...formData,
      languages: [...existing, nextEntry],
    });
    setLanguageInput("");
    setProficiencyInput("");
  };

  const removeLanguage = (language: string) => {
    const existing = (formData.languages || []) as LanguageEntry[];
    setFormData({
      ...formData,
      languages: existing.filter((entry) => entry.language !== language),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <FadeIn>
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) =>
                  setFormData({ ...formData, full_name: e.target.value })
                }
                placeholder="Enter your full name"
                maxLength={150}
              />
            </div>
            <div>
              <Label htmlFor="telegram_id">Telegram ID (optional)</Label>
              <Input
                id="telegram_id"
                type="number"
                value={formData.telegram_id || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    telegram_id: e.target.value ? parseInt(e.target.value) : null,
                  })
                }
                placeholder="Enter your Telegram ID"
              />
            </div>
          </CardContent>
        </Card>
      </FadeIn>

      {/* Education */}
      <FadeIn delay={0.1}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5" />
              Education
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="degree">Degree</Label>
              <Input
                id="degree"
                value={academicData.degree}
                onChange={(e) =>
                  setAcademicData({ ...academicData, degree: e.target.value })
                }
                placeholder="e.g., BSc Computer Science"
              />
            </div>
            <div>
              <Label htmlFor="university">University / Institution</Label>
              <Input
                id="university"
                value={academicData.university}
                onChange={(e) =>
                  setAcademicData({ ...academicData, university: e.target.value })
                }
                placeholder="e.g., Addis Ababa University"
              />
            </div>
            <div>
              <Label htmlFor="graduation_year">Graduation Year</Label>
              <Input
                id="graduation_year"
                type="number"
                value={academicData.graduation_year}
                onChange={(e) =>
                  setAcademicData({ ...academicData, graduation_year: e.target.value })
                }
                placeholder="e.g., 2024"
                min="1900"
                max="2100"
              />
            </div>
          </CardContent>
        </Card>
      </FadeIn>

      {/* Skills */}
      <FadeIn delay={0.2}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="h-5 w-5" />
              Skills
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
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
              />
              <Button type="button" onClick={addSkill} variant="outline">
                Add
              </Button>
            </div>
            {formData.skills && formData.skills.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.skills.map((skill, idx) => (
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
          </CardContent>
        </Card>
      </FadeIn>

      {/* Languages */}
      <FadeIn delay={0.3}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Languages className="h-5 w-5" />
              Languages
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                value={languageInput}
                onChange={(e) => setLanguageInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addLanguage();
                  }
                }}
                placeholder="Language"
              />
              <Input
                value={proficiencyInput}
                onChange={(e) => setProficiencyInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addLanguage();
                  }
                }}
                placeholder="Proficiency (optional)"
              />
              <Button type="button" onClick={addLanguage} variant="outline">
                Add
              </Button>
            </div>
            {formData.languages && formData.languages.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {(formData.languages as LanguageEntry[]).map((lang, idx) => (
                  <Badge key={idx} variant="secondary" className="gap-1">
                    {lang.language}
                    {lang.proficiency && ` (${lang.proficiency})`}
                    <button
                      type="button"
                      onClick={() => removeLanguage(lang.language)}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </FadeIn>

      {/* Interests */}
      <FadeIn delay={0.4}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Heart className="h-5 w-5" />
              Interests
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
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
              />
              <Button type="button" onClick={addInterest} variant="outline">
                Add
              </Button>
            </div>
            {formData.interests && formData.interests.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.interests.map((interest, idx) => (
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
          </CardContent>
        </Card>
      </FadeIn>

      {/* CV */}
      <FadeIn delay={0.5}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              CV / Resume
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="cv_file">Upload CV (PDF or DOCX)</Label>
              <Input
                id="cv_file"
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => {
                  const file = e.target.files?.[0] || null;
                  setCvFile(file);
                }}
                className="mt-2"
              />
              {cvFile && (
                <p className="mt-2 text-sm text-muted-foreground">
                  Selected: {cvFile.name}
                </p>
              )}
              {profile.cv_file && !cvFile && (
                <p className="mt-2 text-sm text-muted-foreground">
                  Current: {profile.cv_file.split("/").pop()}
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="cv_text">CV Text (extracted or manual entry)</Label>
              <Textarea
                id="cv_text"
                value={formData.cv_text}
                onChange={(e) =>
                  setFormData({ ...formData, cv_text: e.target.value })
                }
                placeholder="Paste or type your CV content here"
                rows={8}
              />
            </div>
          </CardContent>
        </Card>
      </FadeIn>

      {/* Actions */}
      <FadeIn delay={0.6}>
        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSaving}>
            {isSaving ? (
              <>
                <span className="mr-2">Saving...</span>
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </FadeIn>
    </form>
  );
}

