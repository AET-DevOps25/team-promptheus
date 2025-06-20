/**
 * This file was auto-generated by openapi-typescript.
 * Do not make direct changes to the file.
 */

export type paths = {
	"/api/repositories/{usercode}/selection": {
		/** tell the AI service which items should be included into the summary */
		post: operations["createCommitSelectionForSummary"];
	};
	"/api/repositories/{usercode}/question": {
		/** create a question to be answered asynchronously by the ai service */
		post: operations["createQuestion"];
	};
	"/api/repositories/PAT": {
		/** Provide the personal access token to retrieve the secure maintainer and developer links */
		post: operations["createFromPAT"];
	};
	"/api/repositories/{usercode}": {
		/**
		 * Get the git repository information
		 * @description Auth is handled via the provided UUID
		 */
		get: operations["getGitRepository"];
	};
	"/api/repositories/{usercode}/search": {
		/** allows searching the repository's content */
		get: operations["search"];
	};
};

export type webhooks = Record<string, never>;

export type components = {
	schemas: {
		readonly SelectionSubmission: {
			readonly selection?: readonly string[];
		};
		readonly QuestionSubmission: {
			readonly question?: string;
		};
		readonly PATConstruct: {
			readonly repolink?: string;
			readonly pat?: string;
		};
		readonly LinkConstruct: {
			readonly developerview: string;
			readonly stakeholderview: string;
		};
		readonly ContentConstruct: {
			readonly id?: string;
			readonly type?: string;
			readonly user?: string;
			readonly summary?: string;
			/** Format: date-time */
			readonly createdAt?: string;
		};
		readonly GitRepoInformationConstruct: {
			readonly repoLink?: string;
			readonly isMaintainer?: boolean;
			/** Format: date-time */
			readonly createdAt?: string;
			readonly questions?: readonly components["schemas"]["QuestionConstruct"][];
			readonly summaries?: readonly components["schemas"]["SummaryConstruct"][];
			readonly contents?: readonly components["schemas"]["ContentConstruct"][];
		};
		readonly QuestionAnswerConstruct: {
			readonly answer?: string;
			/** Format: date-time */
			readonly createdAt?: string;
		};
		readonly QuestionConstruct: {
			readonly question?: string;
			/** Format: date-time */
			readonly createdAt?: string;
			readonly answers?: readonly components["schemas"]["QuestionAnswerConstruct"][];
		};
		readonly SummaryConstruct: {
			/** Format: int64 */
			readonly id?: number;
			readonly summary?: string;
			/** Format: date-time */
			readonly createdAt?: string;
		};
		readonly FacetRating: {
			/** Format: double */
			readonly min?: number;
			/** Format: double */
			readonly max?: number;
		};
		readonly SearchResult: {
			readonly hits?: readonly {
				[key: string]: unknown;
			}[];
			readonly facetDistribution?: unknown;
			readonly facetStats?: {
				[key: string]: components["schemas"]["FacetRating"];
			};
			/** Format: int32 */
			readonly processingTimeMs?: number;
			readonly query?: string;
			/** Format: int32 */
			readonly offset?: number;
			/** Format: int32 */
			readonly limit?: number;
			/** Format: int32 */
			readonly estimatedTotalHits?: number;
		};
	};
	responses: never;
	parameters: never;
	requestBodies: never;
	headers: never;
	pathItems: never;
};

export type $defs = Record<string, never>;

export type external = Record<string, never>;

export type operations = {
	/** tell the AI service which items should be included into the summary */
	createCommitSelectionForSummary: {
		parameters: {
			path: {
				usercode: string;
			};
		};
		readonly requestBody: {
			readonly content: {
				readonly "application/json": components["schemas"]["SelectionSubmission"];
			};
		};
		responses: {
			/** @description Items were included in the summary */
			200: {
				content: {
					readonly "text/plain": string;
				};
			};
			/** @description Invalid input provided - please make sure that all selected content exists */
			400: {
				content: {
					readonly "text/plain": string;
				};
			};
			/** @description Forbidden - Requested code does not exist */
			403: {
				content: {
					readonly "text/plain": string;
				};
			};
		};
	};
	/** create a question to be answered asynchronously by the ai service */
	createQuestion: {
		parameters: {
			path: {
				usercode: string;
			};
		};
		/** @description Question to create */
		readonly requestBody: {
			readonly content: {
				/**
				 * @example {
				 *   "question": "Why are these developer raving about 42?"
				 * }
				 */
				readonly "application/json": components["schemas"]["QuestionSubmission"];
			};
		};
		responses: {
			/** @description Items were included in the summary */
			200: {
				content: {
					readonly "text/plain": string;
				};
			};
			/** @description Forbidden - Requested code does not exist */
			403: {
				content: {
					readonly "*/*": string;
				};
			};
		};
	};
	/** Provide the personal access token to retrieve the secure maintainer and developer links */
	createFromPAT: {
		readonly requestBody: {
			readonly content: {
				readonly "application/json": components["schemas"]["PATConstruct"];
			};
		};
		responses: {
			/** @description secure maintainer and developer links */
			200: {
				content: {
					readonly "application/json": components["schemas"]["LinkConstruct"];
				};
			};
			/** @description Forbidden - Requested code does not exist */
			403: {
				content: {
					readonly "*/*": components["schemas"]["LinkConstruct"];
				};
			};
		};
	};
	/**
	 * Get the git repository information
	 * @description Auth is handled via the provided UUID
	 */
	getGitRepository: {
		parameters: {
			path: {
				usercode: string;
			};
		};
		responses: {
			/** @description get repository-content */
			200: {
				content: {
					readonly "application/json": components["schemas"]["GitRepoInformationConstruct"];
				};
			};
			/** @description Forbidden - Requested code does not exist */
			403: {
				content: {
					readonly "text/plain": string;
				};
			};
		};
	};
	/** allows searching the repository's content */
	search: {
		parameters: {
			query: {
				query: string;
			};
			path: {
				usercode: string;
			};
		};
		responses: {
			/** @description searched repository-content */
			200: {
				content: {
					readonly "application/json": components["schemas"]["SearchResult"];
				};
			};
			/** @description Forbidden - Requested code does not exist */
			403: {
				content: {
					readonly "text/plain": string;
				};
			};
		};
	};
};
