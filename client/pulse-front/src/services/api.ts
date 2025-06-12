

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



