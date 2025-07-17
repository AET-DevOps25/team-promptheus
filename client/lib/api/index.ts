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
// Export contributions functionality
export {
  useContributions,
  useTriggerContributionFetch,
  useUpdateContributions,
} from "./contributions";
// Export search functionality
export { useSearch } from "./search";

// Export server functionality
export {
  type GitRepoInformation,
  type LinkConstruct,
  type PATConstruct,
  type QuestionAnswerConstruct,
  type QuestionSubmission,
  useCreateFromPAT,
  useCreateQuestion,
  useGitRepoInformation,
  useQuestionsAndAnswers,
} from "./server";
// Export summary functionality
export { useGenerateSummary, useSummaries } from "./summary";
