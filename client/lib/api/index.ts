/**
 * API services index - exports all API hooks and utilities
 */

// Re-export commonly used TanStack Query utilities
export {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

// Export search functionality
export { useSearch } from "./search";

// Export summary functionality
export { useSummaries, useGenerateSummary } from "./summary";

// Export server functionality
export { 
  useGitRepoInformation, 
  useCreateQuestion, 
  useCreateFromPAT,
  useQuestionsAndAnswers,
  type GitRepoInformation,
  type QuestionSubmission,
  type QuestionAnswerConstruct,
  type PATConstruct,
  type LinkConstruct,
} from "./server";

// Export contributions functionality
export { useContributions, useUpdateContributions, useTriggerContributionFetch } from "./contributions";
