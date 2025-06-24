# TanStack Query API Integration

This directory contains the TanStack Query setup and API hooks for the application. TanStack Query provides powerful data fetching, caching, and synchronization capabilities.

## Setup

The TanStack Query client is configured in `lib/react-query.tsx` and wrapped around the entire application in `app/layout.tsx`.

## Available API Hooks

### QA Hooks (`lib/api/qa.ts`)

#### `useQAItems()`
Fetches all QA items with automatic caching and background refetching.

```tsx
import { useQAItems } from '@/lib/api';

function QAComponent() {
  const { data, isLoading, error } = useQAItems();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data?.items.map(item => (
        <div key={item.id}>{item.question}</div>
      ))}
    </div>
  );
}
```

#### `useCreateQA()`
Creates a new QA item with optimistic updates.

```tsx
import { useCreateQA } from '@/lib/api';

function CreateQAForm() {
  const createQA = useCreateQA();

  const handleSubmit = async (question: string) => {
    try {
      await createQA.mutateAsync({ question });
      // Success! The cache will be automatically updated
    } catch (error) {
      // Handle error
    }
  };

  return (
    <button
      disabled={createQA.isPending}
      onClick={() => handleSubmit("My question")}
    >
      {createQA.isPending ? 'Creating...' : 'Create QA'}
    </button>
  );
}
```

#### `useUpdateQAStatus()`
Updates the status of a QA item (approve/reject).

```tsx
import { useUpdateQAStatus } from '@/lib/api';

function QAStatusButtons({ id }: { id: string }) {
  const updateStatus = useUpdateQAStatus();

  return (
    <div>
      <button
        disabled={updateStatus.isPending}
        onClick={() => updateStatus.mutate({ id, status: 'approved' })}
      >
        Approve
      </button>
      <button
        disabled={updateStatus.isPending}
        onClick={() => updateStatus.mutate({ id, status: 'rejected' })}
      >
        Reject
      </button>
    </div>
  );
}
```

#### `useVoteQA()`
Vote on a QA item (upvote/downvote).

```tsx
import { useVoteQA } from '@/lib/api';

function VoteButtons({ id }: { id: string }) {
  const vote = useVoteQA();

  return (
    <div>
      <button
        disabled={vote.isPending}
        onClick={() => vote.mutate({ id, type: 'up' })}
      >
        👍
      </button>
      <button
        disabled={vote.isPending}
        onClick={() => vote.mutate({ id, type: 'down' })}
      >
        👎
      </button>
    </div>
  );
}
```

### Search Hooks (`lib/api/search.ts`)

#### `useSearch(params, enabled)`
Performs search with automatic caching and debouncing.

```tsx
import { useSearch } from '@/lib/api';

function SearchComponent() {
  const [searchParams, setSearchParams] = useState({
    query: '',
    filterContributionType: ['pr', 'commit'],
    repositories: [],
    authors: []
  });

  const { data, isLoading, error } = useSearch(searchParams, !!searchParams.query);

  return (
    <div>
      <input
        value={searchParams.query}
        onChange={(e) => setSearchParams(prev => ({
          ...prev,
          query: e.target.value
        }))}
        placeholder="Search..."
      />

      {isLoading && <div>Searching...</div>}
      {data?.results.map(result => (
        <div key={result.id}>{result.title}</div>
      ))}
    </div>
  );
}
```

#### `useDebouncedSearch(params, debounceMs, enabled)`
Same as `useSearch` but with built-in debouncing for better UX.

```tsx
import { useDebouncedSearch } from '@/lib/api';

function SearchAsYouType() {
  const [params, setParams] = useState({ query: '' });

  // Will automatically debounce searches by 500ms
  const { data, isLoading } = useDebouncedSearch(params, 500);

  return (
    <input
      onChange={(e) => setParams({ query: e.target.value })}
      placeholder="Search as you type..."
    />
  );
}
```

## API Client (`lib/api/client.ts`)

The base API client handles:
- Automatic JSON parsing
- Consistent error handling
- Request/response interceptors
- TypeScript support

### Custom API Calls

You can use the API client directly for custom endpoints:

```tsx
import { apiClient } from '@/lib/api';

// GET request
const response = await apiClient.get<MyType>('/custom-endpoint');
console.log(response.data);

// POST request
const response = await apiClient.post<ResponseType>('/create', {
  name: 'example'
});

// Error handling
try {
  const response = await apiClient.get('/might-fail');
} catch (error) {
  if (error instanceof ApiError) {
    console.log('API Error:', error.message, error.status);
  }
}
```

## Types (`lib/api/types.ts`)

All API response types are defined here. Import them for type safety:

```tsx
import type { QAItem, SearchResult, SearchParams } from '@/lib/api/types';
```

## Best Practices

### 1. Use Query Keys Consistently
Always use the exported query keys for invalidation:

```tsx
import { QA_KEYS, useQueryClient } from '@/lib/api';

const queryClient = useQueryClient();

// Invalidate all QA queries
queryClient.invalidateQueries({ queryKey: QA_KEYS.all });

// Invalidate specific item
queryClient.invalidateQueries({ queryKey: QA_KEYS.item('123') });
```

### 2. Handle Loading States
Always provide loading feedback:

```tsx
const { data, isLoading, error } = useQAItems();

if (isLoading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
if (!data) return <EmptyState />;

return <DataComponent data={data} />;
```

### 3. Optimistic Updates
Mutations automatically update the cache, but you can add optimistic updates:

```tsx
const createQA = useCreateQA();

const handleCreate = async (question: string) => {
  // The mutation will handle cache updates automatically
  await createQA.mutateAsync({ question });
};
```

### 4. Error Handling
Handle errors at the component level:

```tsx
const mutation = useCreateQA();

const handleSubmit = async () => {
  try {
    await mutation.mutateAsync(data);
    toast.success('Created successfully!');
  } catch (error) {
    toast.error('Failed to create item');
  }
};
```

## Configuration

The React Query client is configured with:
- 1-minute stale time for better UX
- Smart retry logic (no retries on 4xx, up to 3 retries on 5xx)
- Automatic background refetching
- DevTools in development

## DevTools

In development, the React Query DevTools are available. Press the TanStack Query button in the bottom corner to inspect cache, queries, and mutations.

## Migration from Fetch

Old fetch-based code:
```tsx
const [data, setData] = useState();
const [loading, setLoading] = useState(false);

useEffect(() => {
  setLoading(true);
  fetch('/api/qa')
    .then(res => res.json())
    .then(setData)
    .finally(() => setLoading(false));
}, []);
```

New TanStack Query code:
```tsx
const { data, isLoading } = useQAItems();
```

Much simpler and with built-in caching, error handling, and revalidation!
