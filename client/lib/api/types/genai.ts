/**
 * This file was auto-generated by openapi-typescript.
 * Do not make direct changes to the file.
 */

export type paths = {
	readonly "/contributions": {
		readonly parameters: {
			readonly query?: never;
			readonly header?: never;
			readonly path?: never;
			readonly cookie?: never;
		};
		readonly get?: never;
		readonly put?: never;
		/**
		 * Start Contributions Ingestion Task
		 * @description Start an asynchronous ingestion task for GitHub contributions.
		 */
		readonly post: operations["start_contributions_ingestion_task_contributions_post"];
		readonly delete?: never;
		readonly options?: never;
		readonly head?: never;
		readonly patch?: never;
		readonly trace?: never;
	};
	readonly "/ingest/{task_id}": {
		readonly parameters: {
			readonly query?: never;
			readonly header?: never;
			readonly path?: never;
			readonly cookie?: never;
		};
		/**
		 * Get Ingestion Task Status
		 * @description Get the status of a contributions ingestion task.
		 */
		readonly get: operations["get_ingestion_task_status_ingest__task_id__get"];
		readonly put?: never;
		readonly post?: never;
		readonly delete?: never;
		readonly options?: never;
		readonly head?: never;
		readonly patch?: never;
		readonly trace?: never;
	};
	readonly "/users/{username}/weeks/{week_id}/questions": {
		readonly parameters: {
			readonly query?: never;
			readonly header?: never;
			readonly path?: never;
			readonly cookie?: never;
		};
		readonly get?: never;
		readonly put?: never;
		/**
		 * Ask Question About User Contributions
		 * @description Ask a question about a user's contributions for a specific week.
		 */
		readonly post: operations["ask_question_about_user_contributions_users__username__weeks__week_id__questions_post"];
		readonly delete?: never;
		readonly options?: never;
		readonly head?: never;
		readonly patch?: never;
		readonly trace?: never;
	};
};
export type webhooks = Record<string, never>;
export type components = {
	schemas: {
		/**
		 * ContributionMetadata
		 * @description Metadata about a contribution to be fetched.
		 */
		readonly ContributionMetadata: {
			readonly type: components["schemas"]["ContributionType"];
			/** Id */
			readonly id: string;
			/** Selected */
			readonly selected: boolean;
		};
		/**
		 * ContributionType
		 * @description Types of GitHub contributions supported by the system.
		 * @enum {string}
		 */
		readonly ContributionType: "commit" | "pull_request" | "issue" | "release";
		/**
		 * ContributionsIngestRequest
		 * @description Request to ingest contributions for a user's week (metadata only).
		 */
		readonly ContributionsIngestRequest: {
			/** User */
			readonly user: string;
			/** Week */
			readonly week: string;
			/** Repository */
			readonly repository: string;
			/** Contributions */
			readonly contributions: readonly components["schemas"]["ContributionMetadata"][];
			/** Github Pat */
			readonly github_pat: string;
		};
		/** HTTPValidationError */
		readonly HTTPValidationError: {
			/** Detail */
			readonly detail?: readonly components["schemas"]["ValidationError"][];
		};
		/**
		 * IngestTaskResponse
		 * @description Response from starting a contributions ingestion task.
		 */
		readonly IngestTaskResponse: {
			/** Task Id */
			readonly task_id: string;
			/** User */
			readonly user: string;
			/** Week */
			readonly week: string;
			/** Repository */
			readonly repository: string;
			/** @default queued */
			readonly status: components["schemas"]["TaskStatus"];
			/** Total Contributions */
			readonly total_contributions: number;
			/** Summary Id */
			readonly summary_id?: string | null;
			/**
			 * Created At
			 * Format: date-time
			 */
			readonly created_at: string;
		};
		/**
		 * IngestTaskStatus
		 * @description Status of a contributions ingestion task.
		 */
		readonly IngestTaskStatus: {
			/** Task Id */
			readonly task_id: string;
			/** User */
			readonly user: string;
			/** Week */
			readonly week: string;
			/** Repository */
			readonly repository: string;
			readonly status: components["schemas"]["TaskStatus"];
			/** Total Contributions */
			readonly total_contributions: number;
			/** Ingested Count */
			readonly ingested_count: number;
			/** Failed Count */
			readonly failed_count: number;
			/** Embedding Job Id */
			readonly embedding_job_id?: string | null;
			readonly summary?: components["schemas"]["SummaryResponse"] | null;
			/** Error Message */
			readonly error_message?: string | null;
			/**
			 * Created At
			 * Format: date-time
			 */
			readonly created_at: string;
			/** Started At */
			readonly started_at?: string | null;
			/** Completed At */
			readonly completed_at?: string | null;
			/** Processing Time Ms */
			readonly processing_time_ms?: number | null;
		};
		/**
		 * QuestionContext
		 * @description Context configuration for question answering.
		 */
		readonly QuestionContext: {
			/** Focus Areas */
			readonly focus_areas?: readonly string[];
			/**
			 * Include Evidence
			 * @default true
			 */
			readonly include_evidence: boolean;
			/** @default detailed */
			readonly reasoning_depth: components["schemas"]["ReasoningDepth"];
			/**
			 * Max Evidence Items
			 * @default 10
			 */
			readonly max_evidence_items: number;
		};
		/**
		 * QuestionEvidence
		 * @description Evidence supporting a question answer.
		 */
		readonly QuestionEvidence: {
			/** Title */
			readonly title: string;
			/** Contribution Id */
			readonly contribution_id: string;
			readonly contribution_type: components["schemas"]["ContributionType"];
			/** Excerpt */
			readonly excerpt: string;
			/** Relevance Score */
			readonly relevance_score: number;
			/**
			 * Timestamp
			 * Format: date-time
			 */
			readonly timestamp: string;
		};
		/**
		 * QuestionRequest
		 * @description Request to ask a question about a user's week.
		 */
		readonly QuestionRequest: {
			/** Question */
			readonly question: string;
			/** Repository */
			readonly repository: string;
			/** Summary */
			readonly summary?: string | null;
			readonly context?: components["schemas"]["QuestionContext"];
			/** Github Pat */
			readonly github_pat: string;
		};
		/**
		 * QuestionResponse
		 * @description Response to a question about a user's week.
		 */
		readonly QuestionResponse: {
			/** Question Id */
			readonly question_id: string;
			/** User */
			readonly user: string;
			/** Week */
			readonly week: string;
			/** Question */
			readonly question: string;
			/** Answer */
			readonly answer: string;
			/** Confidence */
			readonly confidence: number;
			/** Evidence */
			readonly evidence?: readonly components["schemas"]["QuestionEvidence"][];
			/** Reasoning Steps */
			readonly reasoning_steps?: readonly string[];
			/** Suggested Actions */
			readonly suggested_actions?: readonly string[];
			/**
			 * Asked At
			 * Format: date-time
			 */
			readonly asked_at: string;
			/** Response Time Ms */
			readonly response_time_ms: number;
			/** Conversation Id */
			readonly conversation_id?: string | null;
		};
		/**
		 * ReasoningDepth
		 * @description Depth levels for question answering reasoning.
		 * @enum {string}
		 */
		readonly ReasoningDepth: "quick" | "detailed" | "deep";
		/**
		 * SummaryMetadata
		 * @description Metadata about a generated summary.
		 */
		readonly SummaryMetadata: {
			/** Total Contributions */
			readonly total_contributions: number;
			/** Commits Count */
			readonly commits_count: number;
			/** Pull Requests Count */
			readonly pull_requests_count: number;
			/** Issues Count */
			readonly issues_count: number;
			/** Releases Count */
			readonly releases_count: number;
			/** Repositories */
			readonly repositories: readonly string[];
			/** Time Period */
			readonly time_period: string;
			/**
			 * Generated At
			 * Format: date-time
			 */
			readonly generated_at: string;
		};
		/**
		 * SummaryResponse
		 * @description Complete summary response (non-streaming).
		 */
		readonly SummaryResponse: {
			/** Summary Id */
			readonly summary_id: string;
			/** User */
			readonly user: string;
			/** Week */
			readonly week: string;
			/** Overview */
			readonly overview: string;
			/** Commits Summary */
			readonly commits_summary: string;
			/** Pull Requests Summary */
			readonly pull_requests_summary: string;
			/** Issues Summary */
			readonly issues_summary: string;
			/** Releases Summary */
			readonly releases_summary: string;
			/** Analysis */
			readonly analysis: string;
			/** Key Achievements */
			readonly key_achievements: readonly string[];
			/** Areas For Improvement */
			readonly areas_for_improvement: readonly string[];
			readonly metadata: components["schemas"]["SummaryMetadata"];
			/**
			 * Generated At
			 * Format: date-time
			 */
			readonly generated_at: string;
		};
		/**
		 * TaskStatus
		 * @description Status values for asynchronous tasks.
		 * @enum {string}
		 */
		readonly TaskStatus:
			| "queued"
			| "ingesting"
			| "summarizing"
			| "done"
			| "failed";
		/** ValidationError */
		readonly ValidationError: {
			/** Location */
			readonly loc: readonly (string | number)[];
			/** Message */
			readonly msg: string;
			/** Error Type */
			readonly type: string;
		};
	};
	responses: never;
	parameters: never;
	requestBodies: never;
	headers: never;
	pathItems: never;
};
export type $defs = Record<string, never>;
export interface operations {
	readonly start_contributions_ingestion_task_contributions_post: {
		readonly parameters: {
			readonly query?: never;
			readonly header?: never;
			readonly path?: never;
			readonly cookie?: never;
		};
		readonly requestBody: {
			readonly content: {
				readonly "application/json": components["schemas"]["ContributionsIngestRequest"];
			};
		};
		readonly responses: {
			/** @description Successful Response */
			readonly 200: {
				headers: {
					readonly [name: string]: unknown;
				};
				content: {
					readonly "application/json": components["schemas"]["IngestTaskResponse"];
				};
			};
			/** @description Validation Error */
			readonly 422: {
				headers: {
					readonly [name: string]: unknown;
				};
				content: {
					readonly "application/json": components["schemas"]["HTTPValidationError"];
				};
			};
		};
	};
	readonly get_ingestion_task_status_ingest__task_id__get: {
		readonly parameters: {
			readonly query?: never;
			readonly header?: never;
			readonly path: {
				/** @description Task ID returned from POST /contributions */
				readonly task_id: string;
			};
			readonly cookie?: never;
		};
		readonly requestBody?: never;
		readonly responses: {
			/** @description Successful Response */
			readonly 200: {
				headers: {
					readonly [name: string]: unknown;
				};
				content: {
					readonly "application/json": components["schemas"]["IngestTaskStatus"];
				};
			};
			/** @description Validation Error */
			readonly 422: {
				headers: {
					readonly [name: string]: unknown;
				};
				content: {
					readonly "application/json": components["schemas"]["HTTPValidationError"];
				};
			};
		};
	};
	readonly ask_question_about_user_contributions_users__username__weeks__week_id__questions_post: {
		readonly parameters: {
			readonly query?: never;
			readonly header?: never;
			readonly path: {
				/** @description GitHub username */
				readonly username: string;
				/** @description ISO week format: 2024-W21 */
				readonly week_id: string;
			};
			readonly cookie?: never;
		};
		readonly requestBody: {
			readonly content: {
				readonly "application/json": components["schemas"]["QuestionRequest"];
			};
		};
		readonly responses: {
			/** @description Successful Response */
			readonly 200: {
				headers: {
					readonly [name: string]: unknown;
				};
				content: {
					readonly "application/json": components["schemas"]["QuestionResponse"];
				};
			};
			/** @description Validation Error */
			readonly 422: {
				headers: {
					readonly [name: string]: unknown;
				};
				content: {
					readonly "application/json": components["schemas"]["HTTPValidationError"];
				};
			};
		};
	};
}
