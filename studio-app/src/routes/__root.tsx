import { createRootRoute, Outlet, Link } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools';

export const Route = createRootRoute({
  component: () => (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-950/90 backdrop-blur border-b border-gray-800">
        <nav className="max-w-[1440px] mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold text-amber-400 tracking-wide">BrandlyPoster Studio</h1>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span className="hidden sm:block">1440×900 Deck</span>
            <Link to="/studio" className="hover:text-amber-400 transition-colors">Studio</Link>
            <Link to="/projects" className="hover:text-amber-400 transition-colors">Projects</Link>
            <Link to="/settings" className="hover:text-amber-400 transition-colors">Settings</Link>
          </div>
        </nav>
      </header>
      <main className="pt-16 min-h-screen">
        <Outlet />
      </main>
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </>
  ),
});