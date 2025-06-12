
import { useAuth } from '@/elements/auth';
import React from 'react';




export function SummaryViewing() {
  const { user } = useAuth();
  return (
    <div>
      <h1>Summary viewing</h1>
    </div>
  );

}