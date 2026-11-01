import { createRouter, createRootRoute, Outlet } from '@tanstack/react-router';
import { routeTree } from './routeTree.gen';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrandlyPosterProvider } from './components/BrandlyPosterProvider';

// Create query client
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
        refetchOnWindowFocus: false,
        retry: 1,
        gcTime: 1000 * 60 * 30,
      },
      mutations: {
        retry: 0,
      },
    },
  });
}

createRootRoute({
  component: () => (
    <QueryClientProvider client={queryClient}>
      <BrandlyPosterProvider>
        <Outlet />
      </BrandlyPosterProvider>
    </QueryClientProvider>
  ),
});

export const queryClient = makeQueryClient();

export const router = createRouter({ routeTree });

// Register router for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

// App wrapper component
export function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Outlet />
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </div>
  );
}