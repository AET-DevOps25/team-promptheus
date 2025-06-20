import type {operations as serverOps} from "./server"
import type {operations as genaiOps} from "./genai"

type NewRepoResponse = serverOps["createFromPAT"]["responses"][200]["content"]["application/json"];
export async function createFromPAT(repoLink:string,pat:string):Promise<NewRepoResponse>{
    type Req = serverOps["createFromPAT"]["requestBody"]["content"]["application/json"];
    const body: Req= {repolink:repoLink,pat};
    const resp = await fetch("/api/repositories/PAT", { method: "POST", body: JSON.stringify(body)});
    return await resp.json();
}

type GitRepoResponse = serverOps["getGitRepository"]["responses"][200]["content"]["application/json"];
export async function getGitRepoContent(uuid: string): Promise<GitRepoResponse> {
    return await (await fetch("/api/repositories/" + uuid)).json();
}

type SearchRepoResponse = serverOps["createFromPAT"]["responses"][200]["content"]["application/json"];
export async function searchRepo(uuid: string, query: string):Promise<SearchRepoResponse> {
    const resp = await fetch(`/api/repositories/${uuid}/search?query=${query}`);
    return await resp.json();
}

export async function createSelection(uuid: string, selection: string[]):Promise<void> {
    type Req = serverOps["createCommitSelectionForSummary"]["requestBody"]["content"]["application/json"];
    const body: Req = {selection};
    const resp = await fetch(`/api/repositories/${uuid}/selection`, {method: "POST", body: JSON.stringify(body)});
    return await resp.json();
}

export async function createQuestion(uuid: string, question: string):Promise<void> {
    type Req = serverOps["createQuestion"]["requestBody"]["content"]["application/json"];
    const body: Req = {question};
    const resp = await fetch(`/api/repositories/${uuid}/question`, {method: "POST", body: JSON.stringify(body)});
    await resp.text();
}

// Add other API calls here
