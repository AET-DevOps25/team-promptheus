"""
Langchain tools for interacting with the GitHub API.

This module provides a set of tools that can be used by a Langchain agent
to search and retrieve information from GitHub repositories.

The tools are built on top of the GitHubContentService.
"""

import json
from typing import Optional

from langchain.tools import tool
from .contributions import GitHubContentService

# Create a single instance of the service to reuse the session
github_service = GitHubContentService()


@tool
async def search_github_code(repository: str, query: str) -> str:
    """
    Searches for code in a GitHub repository - perfect for finding implementations!
    Use this when users ask about how something is coded, what functions exist, or to find specific code patterns.
    This tool provides real-time access to the actual codebase and returns precise code locations.
    Essential for questions about implementation details, code structure, or finding specific functionality.
    """
    results = await github_service.search_code(repository, query)
    if not results:
        return "No code results found."
    # Return a subset of fields to avoid being too verbose.
    filtered_results = [{"path": r["path"], "url": r["html_url"]} for r in results]
    return json.dumps(filtered_results, indent=2)


@tool
async def search_github_issues(
    repository: str, query: str, is_open: Optional[bool] = None
) -> str:
    """
    Searches for issues in a GitHub repository - excellent for finding bug reports and feature requests!
    Perfect when users ask about problems, bugs, feature requests, or project discussions.
    Can filter by state (open, closed, or all) to find exactly what you need.
    Great for understanding project context, user feedback, and development priorities.
    """
    results = await github_service.search_issues_and_prs(
        repository, query, is_pr=False, is_open=is_open
    )
    if not results:
        return "No issues found."
    filtered_results = [
        {
            "number": r["number"],
            "title": r["title"],
            "state": r["state"],
            "url": r["html_url"],
        }
        for r in results
    ]
    return json.dumps(filtered_results, indent=2)


@tool
async def search_github_pull_requests(
    repository: str, query: str, is_open: Optional[bool] = None
) -> str:
    """
    Searches for pull requests in a GitHub repository - ideal for understanding code changes and reviews!
    Use this when users ask about code reviews, merges, development workflow, or what changes were made.
    Can filter by state (open, closed, or all) to get the most relevant results.
    Excellent for tracking development progress and understanding code evolution.
    """
    results = await github_service.search_issues_and_prs(
        repository, query, is_pr=True, is_open=is_open
    )
    if not results:
        return "No pull requests found."
    filtered_results = [
        {
            "number": r["number"],
            "title": r["title"],
            "state": r["state"],
            "url": r["html_url"],
        }
        for r in results
    ]
    return json.dumps(filtered_results, indent=2)


@tool
async def get_github_file_content(repository: str, file_path: str) -> str:
    """
    Gets the actual content of a specific file in a GitHub repository - perfect for detailed code analysis!
    Use this when users want to see what's actually in a file, understand implementation details, or analyze code structure.
    Provides the complete, up-to-date file content for thorough examination.
    Essential for answering questions about specific code, configurations, or documentation.
    """
    content = await github_service.get_file_content(repository, file_path)
    return content if content else f"File '{file_path}' not found or is not a file."


@tool
async def get_commit_details(repository: str, sha: str) -> str:
    """
    Gets detailed information for a specific commit using its SHA.
    """
    commit = await github_service.get_commit_details(repository, sha)
    if commit:
        return commit.model_dump_json(indent=2)
    return "Commit not found."


@tool
async def get_issue_details(repository: str, issue_number: int) -> str:
    """
    Gets detailed information for a specific issue using its number.
    """
    issue = await github_service.get_issue_details(repository, str(issue_number))
    if issue:
        return issue.model_dump_json(indent=2)
    return "Issue not found."


@tool
async def get_pull_request_details(repository: str, pr_number: int) -> str:
    """
    Gets detailed information for a specific pull request using its number.
    """
    pr = await github_service.get_pull_request_details(repository, str(pr_number))
    if pr:
        return pr.model_dump_json(indent=2)
    return "Pull request not found."


def get_tool_descriptions(tools) -> str:
    """Return a formatted string containing all tool names and their descriptions."""
    tool_names = [t.name for t in tools]
    tool_descriptions = []

    for t in tools:
        description = getattr(t, "description", "").strip() or ""
        tool_descriptions.append(f"{t.name}:\n{description}")

    return f"Available tools: {', '.join(tool_names)}\n\n" + "\n\n".join(
        tool_descriptions
    )


all_tools = [
    search_github_code,
    search_github_issues,
    search_github_pull_requests,
    get_github_file_content,
    get_commit_details,
    get_issue_details,
    get_pull_request_details,
]
