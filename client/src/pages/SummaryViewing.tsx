
import { useAuth } from '@/contextproviders/authprovider';
import React from 'react';




export function SummaryViewing() {
  const { user } = useAuth();
  const { selectedUser ,setSelectedUser} = useContext(GithubUserProviderContext);

  console.log("Summary viewing for user:")
  console.log(selectedUser)

  return (
    <div>
      <h1>Summary viewing</h1>
    </div>
  );

}