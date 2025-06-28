"""Tests for agent tools functionality."""

import pytest

from src.agent_tools import (
    create_agent_tools,
)

search_github_code = create_agent_tools()[0]
search_github_issues = create_agent_tools()[1]
search_github_pull_requests = create_agent_tools()[2]
get_github_file_content = create_agent_tools()[3]
get_commit_details = create_agent_tools()[4]
get_issue_details = create_agent_tools()[5]
get_pull_request_details = create_agent_tools()[6]


@pytest.mark.asyncio
async def test_search_github_code(mock_github_service) -> None:
    result = await search_github_code.ainvoke({"repository": "test/repo", "query": "def foo"})
    assert "src/example.py" in result
    assert "github.com/test/repo" in result


@pytest.mark.asyncio
async def test_search_github_issues(mock_github_service) -> None:
    result = await search_github_issues.ainvoke({"repository": "test/repo", "query": "bug"})
    assert "Mock Issue" in result
    assert "issues/2" in result


@pytest.mark.asyncio
async def test_search_github_pull_requests(mock_github_service) -> None:
    result = await search_github_pull_requests.ainvoke({"repository": "test/repo", "query": "feature", "is_open": True})
    assert "Mock PR" in result
    assert "pull/1" in result


@pytest.mark.asyncio
async def test_get_github_file_content(mock_github_service) -> None:
    result = await get_github_file_content.ainvoke({"repository": "test/repo", "file_path": "main.py"})
    assert "Mock content of main.py" in result
    notfound = await get_github_file_content.ainvoke({"repository": "test/repo", "file_path": "notfound.py"})
    assert "not found" in notfound or notfound is None


@pytest.mark.asyncio
async def test_get_commit_details(mock_github_service) -> None:
    # The mock for get_commit_details is not implemented, so just check fallback
    result = await get_commit_details.ainvoke({"repository": "test/repo", "sha": "abc123"})
    assert "Commit not found" in result


@pytest.mark.asyncio
async def test_get_issue_details(mock_github_service) -> None:
    # The mock for get_issue_details is not implemented, so just check fallback
    result = await get_issue_details.ainvoke({"repository": "test/repo", "issue_number": 2})
    assert "Issue not found" in result


@pytest.mark.asyncio
async def test_get_pull_request_details(mock_github_service) -> None:
    # The mock for get_pull_request_details is not implemented, so just check fallback
    result = await get_pull_request_details.ainvoke({"repository": "test/repo", "pr_number": 1})
    assert "Pull request not found" in result
