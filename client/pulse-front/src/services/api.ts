

export class ApiService {
  async fetchUser(uuid: string) {
    const response = await fetch(`/api/user/${uuid}`);
    return response.json();
  }

  // Add other API calls here
}