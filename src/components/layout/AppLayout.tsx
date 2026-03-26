import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppLayout() {
  return (
    <div className="h-screen grid grid-cols-[260px_1fr]">
      <Sidebar />
      <main className="grid grid-rows-[auto_1fr] min-w-0">
        <Topbar />
        <section className="p-[18px] overflow-hidden">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
