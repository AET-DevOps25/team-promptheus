
export interface GitHubContributor {
  login: string
  id: number
  avatar_url: string
  contributions: number
  html_url: string
}

export interface GitHubUser {
  login: string
  avatar_url: string
  name?: string
}

export interface GitHubData {
  user: GitHubUser
  contributions: GitHubContribution[]
}

export interface GitHubRepo {
  name: string
  full_name: string
  description: string
  html_url: string
}

export interface GitHubCommit {
  sha: string
  commit: {
    message: string
    author: {
      name: string
      date: string
    }
  }
  html_url: string
}

export interface GitHubIssue {
  id: number
  number: number
  title: string
  created_at: string
  html_url: string
  pull_request?: {
    url: string
  }
}



export interface GitHubContribution {
  id: string
  type: "commit" | "issue" | "pull_request"
  repo: string
  repoFullName: string
  title: string
  date: string
  url: string
}





////////////////////////////// MOCKING ///////////////////77

// Mock data
const mockUsers = [
  { login: "alice_dev", name: "Alice Johnson", id: 1 },
  { login: "bob_coder", name: "Bob Smith", id: 2 },
  { login: "charlie_tech", name: "Charlie Brown", id: 3 },
  { login: "diana_prog", name: "Diana Wilson", id: 4 },
  { login: "eve_script", name: "Eve Davis", id: 5 },
]

const mockRepos = [
  {
    name: "awesome-project",
    full_name: "mockorg/awesome-project",
    description: "An awesome project for demonstration",
    html_url: "https://github.com/mockorg/awesome-project",
  },
  {
    name: "web-app",
    full_name: "mockorg/web-app",
    description: "A modern web application",
    html_url: "https://github.com/mockorg/web-app",
  },
  {
    name: "api-service",
    full_name: "mockorg/api-service",
    description: "RESTful API service",
    html_url: "https://github.com/mockorg/api-service",
  },
]

// Generate mock commits for each user
const generateMockCommits = (startDate: Date, endDate: Date): GitHubCommit[] => {
  const commits: GitHubCommit[] = []
  const commitMessages = [
    "Fix authentication bug",
    "Add new feature for user management",
    "Update documentation",
    "Refactor database queries",
    "Implement error handling",
    "Add unit tests",
    "Optimize performance",
    "Update dependencies",
    "Fix responsive design",
    "Add logging functionality",
  ]

  mockUsers.forEach((user, userIndex) => {
    for (let i = 0; i < 5; i++) {
      const commitDate = new Date(startDate.getTime() + Math.random() * (endDate.getTime() - startDate.getTime()))
      commits.push({
        sha: `${userIndex}${i}${Math.random().toString(36).substr(2, 9)}`,
        commit: {
          message: commitMessages[Math.floor(Math.random() * commitMessages.length)],
          author: {
            name: user.name,
            date: commitDate.toISOString(),
          },
        },
        html_url: `https://github.com/mockorg/awesome-project/commit/${userIndex}${i}${Math.random().toString(36).substr(2, 9)}`,
      })
    }
  })

  return commits.sort((a, b) => new Date(b.commit.author.date).getTime() - new Date(a.commit.author.date).getTime())
}

// Generate mock issues and PRs
const generateMockIssuesAndPRs = (startDate: Date, endDate: Date): GitHubIssue[] => {
  const issues: GitHubIssue[] = []
  const issueTitles = [
    "Bug: Login form validation not working",
    "Feature: Add dark mode support",
    "Enhancement: Improve loading performance",
    "Bug: Mobile responsive issues",
    "Feature: Add export functionality",
  ]

  mockUsers.forEach((user, userIndex) => {
    // Add some issues
    for (let i = 0; i < 2; i++) {
      const issueDate = new Date(startDate.getTime() + Math.random() * (endDate.getTime() - startDate.getTime()))
      issues.push({
        id: userIndex * 100 + i,
        number: userIndex * 10 + i + 1,
        title: issueTitles[Math.floor(Math.random() * issueTitles.length)],
        created_at: issueDate.toISOString(),
        html_url: `https://github.com/mockorg/awesome-project/issues/${userIndex * 10 + i + 1}`,
      })
    }

    // Add some PRs
    for (let i = 0; i < 1; i++) {
      const prDate = new Date(startDate.getTime() + Math.random() * (endDate.getTime() - startDate.getTime()))
      issues.push({
        id: userIndex * 100 + i + 50,
        number: userIndex * 10 + i + 20,
        title: `PR: ${issueTitles[Math.floor(Math.random() * issueTitles.length)]}`,
        created_at: prDate.toISOString(),
        html_url: `https://github.com/mockorg/awesome-project/pull/${userIndex * 10 + i + 20}`,
        pull_request: {
          url: `https://api.github.com/repos/mockorg/awesome-project/pulls/${userIndex * 10 + i + 20}`,
        },
      })
    }
  })

  return issues.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}



///////////////////////////////////////////////////////////////

export async function fetchRepoContributors( repoFullName: string): Promise<GitHubContributor[]> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 600))

  return mockUsers.map((user, index) => ({
    login: user.login,
    id: user.id,
    avatar_url: `https://avatars.githubusercontent.com/u/${user.id}?v=4`,
    contributions: 25 - index * 3, // Varying contribution counts
    html_url: `https://github.com/${user.login}`,
  }))
}

export async function fetchRepoCommits(
  repoFullName: string,
  since: string,
  until: string,
): Promise<GitHubCommit[]> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 400))

  const startDate = new Date(since)
  const endDate = new Date(until)

  return generateMockCommits(startDate, endDate)
}

//sign-up for a repository
export async function signupWithPat(pack: any){

    /* const response = await fetch('http://localhost:8090/api/providePAT' , 
      {
          method: "POST",
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(pack)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      } */

    let response = ['firstlink', 'secondlink'];
    return response //.json();
    
    
}



// fetches general user information for provided 'code' user link
export async function fetchUser(uuid: string) {
  const response = await fetch("/"+{uuid}+"" , {
      method: "GET"
    }
  )
  
  if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
  
}



// fetches all contributions which have been posted 
export async function fetchContributionsOverview(startDate: Date, endDate: Date): Promise<GitHubData> {

  // dummy
  let v = new Array<GitHubContribution>();
  v.push({
          id: 'asdf',
          type: "commit",
          repo: 'therepo',
          repoFullName: 'therepo',
          title: 'thetitle',
          date: 'dateformata',
          url: 'https://stackoverflow.com/questions/23412033/typescript-interface-initialization'
        });
  v.push({
          id: 'asdf2',
          type: "commit",
          repo: 'therepo',
          repoFullName: 'therepo',
          title: 'thetitle',
          date: 'dateformata',
          url: 'https://stackoverflow.com/questions/23412033/typescript-interface-initialization'
        });
  
  let ghuser = {
        login: "loginstring",
        avatar_url: "https://avatars.githubusercontent.com/u/15800240?s=48&v=4",
        name: "asdfasfd"
  }
  return {
            user: ghuser,
            contributions: v
          }
}

export async function searchRepo(uuid: string, query: string) {
  const response = await fetch("/"+{uuid}+"/search" , {
      method: "GET",
      body: JSON.stringify(query)
    }
  )
  if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();

}

  // Add other API calls here


// Helper function to format date for GitHub API
export function formatDateForGitHub(date: Date): string {
  return date.toISOString()
}

// Helper function to check if a date is within a range
export function isDateInRange(dateStr: string, start: Date, end: Date): boolean {
  const date = new Date(dateStr)
  return date >= start && date <= end
}



