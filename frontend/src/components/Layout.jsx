import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import api from '../api.js';
import { useAuth } from '../auth.jsx';

const TOUS = ['docteur', 'major', 'infirmier'];
const MENU = [
  { to: '/', label: 'Tableau de bord', roles: TOUS },
  { to: '/medicaments', label: 'Médicaments', roles: TOUS },
  { to: '/entree', label: 'Entrée de stock (OCR)', roles: ['major', 'infirmier'] },
  { to: '/sortie', label: 'Sortie de stock', roles: ['major', 'infirmier'] },
  { to: '/assistant', label: 'Assistant IA', roles: TOUS },
  { to: '/utilisateurs', label: 'Utilisateurs', roles: ['major'] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const [nb, setNb] = useState(0);

  useEffect(() => {
    const charger = () =>
      api
        .get('/notifications?non_lues=true')
        .then((r) => setNb(r.data.length))
        .catch(() => {});
    charger();
    const t = setInterval(charger, 60000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className='flex min-h-screen bg-slate-50 text-slate-800'>
      <aside className='flex w-64 flex-col bg-teal-800 p-4 text-white'>
        <h1 className='text-lg font-bold'>Centre de Santé Cherrat</h1>
        <p className='mb-6 text-xs text-teal-200'>{user.nom} · {user.role}</p>
        <nav className='flex-1 space-y-1'>
          {MENU.filter((m) => m.roles.includes(user.role)).map((m) => (
            <NavLink
              key={m.to}
              to={m.to}
              end
              className={({ isActive }) => `block rounded px-3 py-2 text-sm ${isActive ? 'bg-teal-600' : 'hover:bg-teal-700'}`}
            >
              {m.label}
              {m.to === '/' && nb > 0 && (
                <span className='ml-2 rounded-full bg-red-500 px-2 py-0.5 text-xs'>{nb}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <button onClick={logout} className='rounded bg-teal-900 px-3 py-2 text-sm hover:bg-teal-950'>Déconnexion</button>
      </aside>
      <main className='flex-1 overflow-auto p-6'>
        <Outlet />
      </main>
    </div>
  );
}