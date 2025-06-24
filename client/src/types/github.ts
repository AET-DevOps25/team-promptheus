export interface GitHubUser {
	id: number;
	login: string;
	avatar_url: string;
	html_url: string;
	name?: string;
	email?: string;
	bio?: string;
	public_repos: number;
	followers: number;
	following: number;
}

export interface GitHubContributor {
	id: number;
	login: string;
	avatar_url: string;
	html_url: string;
	contributions: number;
	type: string;
}

export interface GitHubContribution {
	id: string;
	type: "commit" | "issue" | "pull_request" | "review";
	title: string;
	url: string;
	date: string;
	repo: string;
	repoFullName: string;
	description?: string;
	state?: string;
}

export interface GitHubRepository {
	id: number;
	name: string;
	full_name: string;
	html_url: string;
	description?: string;
	private: boolean;
	fork: boolean;
	language?: string;
	stargazers_count: number;
	forks_count: number;
	created_at: string;
	updated_at: string;
}
