"""
Test data for GenAI API tests

This module provides properly structured test data that matches the GitHub API models.
"""


def get_test_commit_contribution():
    """Get a properly structured commit contribution for testing"""
    return {
        "id": "commit-123",
        "type": "commit",
        "repository": "test/repo",
        "author": "testuser",
        "created_at": "2024-05-20T10:00:00Z",
        "url": "https://api.github.com/repos/test/repo/commits/abc123",
        "sha": "abc123def456",
        "message": "Fix authentication bug",
        "tree": {
            "sha": "tree123",
            "url": "https://api.github.com/repos/test/repo/git/trees/tree123"
        },
        "parents": [
            {
                "sha": "parent123",
                "url": "https://api.github.com/repos/test/repo/commits/parent123"
            }
        ],
        "author_info": {
            "name": "Test User",
            "email": "testuser@example.com",
            "date": "2024-05-20T10:00:00Z"
        },
        "committer": {
            "name": "Test User",
            "email": "testuser@example.com",
            "date": "2024-05-20T10:00:00Z"
        },
        "stats": {
            "total": 15,
            "additions": 10,
            "deletions": 5
        },
        "files": [
            {
                "filename": "auth.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "changes": 15,
                "blob_url": "https://github.com/test/repo/blob/abc123/auth.py",
                "raw_url": "https://github.com/test/repo/raw/abc123/auth.py",
                "contents_url": "https://api.github.com/repos/test/repo/contents/auth.py?ref=abc123",
                "patch": "@@ -1,5 +1,10 @@\n def authenticate():\n+    # Fixed validation\n     return True"
            }
        ]
    }


def get_test_pull_request_contribution():
    """Get a properly structured pull request contribution for testing"""
    return {
        "id": "pr-456",
        "type": "pull_request",
        "repository": "test/repo",
        "author": "testuser",
        "created_at": "2024-05-21T14:30:00Z",
        "url": "https://api.github.com/repos/test/repo/pulls/42",
        "number": 42,
        "title": "Add user management feature",
        "body": "This PR adds comprehensive user management functionality",
        "state": "open",
        "locked": False,
        "user": {
            "login": "testuser",
            "id": 12345,
            "type": "User"
        },
        "head": {
            "label": "testuser:feature-branch",
            "ref": "feature-branch",
            "sha": "def456ghi789",
            "repo": {
                "name": "repo",
                "full_name": "test/repo"
            }
        },
        "base": {
            "label": "test:main",
            "ref": "main",
            "sha": "ghi789jkl012",
            "repo": {
                "name": "repo",
                "full_name": "test/repo"
            }
        },
        "merged": False,
        "comments": 0,
        "review_comments": 0,
        "commits": 1,
        "additions": 50,
        "deletions": 10,
        "changed_files": 3,
        "comments_data": [],
        "reviews_data": [],
        "commits_data": [],
        "files_data": []
    }


def get_test_issue_contribution():
    """Get a properly structured issue contribution for testing"""
    return {
        "id": "issue-789",
        "type": "issue",
        "repository": "test/repo",
        "author": "testuser",
        "created_at": "2024-05-22T09:15:00Z",
        "url": "https://api.github.com/repos/test/repo/issues/15",
        "number": 15,
        "title": "Performance optimization needed",
        "body": "The application is running slowly with large datasets",
        "state": "open",
        "locked": False,
        "user": {
            "login": "testuser",
            "id": 12345,
            "type": "User"
        },
        "comments": 0,
        "comments_data": [],
        "events_data": []
    }


def get_test_release_contribution():
    """Get a properly structured release contribution for testing"""
    return {
        "id": "release-101",
        "type": "release",
        "repository": "test/repo",
        "author": "testuser",
        "created_at": "2024-05-23T16:00:00Z",
        "url": "https://api.github.com/repos/test/repo/releases/101",
        "tag_name": "v1.2.0",
        "target_commitish": "main",
        "name": "Version 1.2.0",
        "body": "## What's New\n- Added user management\n- Fixed authentication bugs",
        "draft": False,
        "prerelease": False,
        "published_at": "2024-05-23T16:00:00Z",
        "author_info": {
            "login": "testuser",
            "id": 12345,
            "type": "User"
        },
        "assets": []
    }

def get_test_commit_metadata(selected=True):
    """Get commit contribution metadata for the new API"""
    return {
        "type": "commit",
        "id": "abc123def456",
        "selected": selected
    }


def get_test_pull_request_metadata(selected=True):
    """Get pull request contribution metadata for the new API"""
    return {
        "type": "pull_request", 
        "id": "42",
        "selected": selected
    }


def get_test_issue_metadata(selected=True):
    """Get issue contribution metadata for the new API"""
    return {
        "type": "issue",
        "id": "15", 
        "selected": selected
    }


def get_test_release_metadata(selected=True):
    """Get release contribution metadata for the new API"""
    return {
        "type": "release",
        "id": "101",
        "selected": selected
    }


def get_test_contributions_metadata_request(user="testuser", week="2024-W21", repository="test/repo", contribution_types=None, selected=True):
    """Get a complete contributions request with metadata-only format (NEW API)"""
    if contribution_types is None:
        contribution_types = ["commit", "pull_request"]
    
    contributions = []
    
    if "commit" in contribution_types:
        contributions.append(get_test_commit_metadata(selected=selected))
    
    if "pull_request" in contribution_types:
        contributions.append(get_test_pull_request_metadata(selected=selected))
    
    if "issue" in contribution_types:
        contributions.append(get_test_issue_metadata(selected=selected))
    
    if "release" in contribution_types:
        contributions.append(get_test_release_metadata(selected=selected))
    
    return {
        "user": user,
        "week": week,
        "repository": repository,
        "contributions": contributions
    }


def get_test_contributions_request(user="testuser", week="2024-W21", contribution_types=None):
    """Get a complete contributions request with full contribution data (LEGACY - for backward compatibility)"""
    if contribution_types is None:
        contribution_types = ["commit", "pull_request"]
    
    contributions = []
    
    if "commit" in contribution_types:
        contributions.append(get_test_commit_contribution())
    
    if "pull_request" in contribution_types:
        contributions.append(get_test_pull_request_contribution())
    
    if "issue" in contribution_types:
        contributions.append(get_test_issue_contribution())
    
    if "release" in contribution_types:
        contributions.append(get_test_release_contribution())
    
    return {
        "user": user,
        "week": week,
        "contributions": contributions
    }


def get_minimal_commit_contribution():
    """Get a minimal commit contribution for simple tests"""
    return {
        "id": "commit-simple",
        "type": "commit",
        "repository": "test/repo",
        "author": "testuser",
        "created_at": "2024-05-20T10:00:00Z",
        "url": "https://api.github.com/repos/test/repo/commits/simple123",
        "sha": "simple123",
        "message": "Simple test commit",
        "tree": {
            "sha": "tree123",
            "url": "https://api.github.com/repos/test/repo/git/trees/tree123"
        },
        "parents": [],
        "author_info": {
            "name": "Test User",
            "email": "testuser@example.com",
            "date": "2024-05-20T10:00:00Z"
        },
        "committer": {
            "name": "Test User", 
            "email": "testuser@example.com",
            "date": "2024-05-20T10:00:00Z"
        },
        "stats": {
            "total": 5,
            "additions": 3,
            "deletions": 2
        },
        "files": []
    }

def get_minimal_commit_metadata(selected=True):
    """Get minimal commit metadata for simple tests (NEW API)"""
    return {
        "type": "commit",
        "id": "simple123",
        "selected": selected
    } 