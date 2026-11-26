import { useEffect, useState } from 'react';
import api from '../api.js';
import { card, fmt, td, th } from '../ui.js';

const Stat = ({ titre, valeur, couleur }) => (
  <div className={card}>
    <p className='text-sm text-slate-500'>{titre}</p>
    <p className={`text-3xl font-bold ${couleur}`}>{valeur}</p>
  </div>
);

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [notifs, setNotifs] = useState([]);

  const charger = () => {
    api.get('/stock/dashboard').then((r) => setStats(r.data));
    api.get('/notifications').then((r) => setNotifs(r.data));
  };
  useEffect(() => {
    charger();
  }, []);

  const lue = (id) => api.post(`/notifications/${id}/lue`).then(charger);

  if (!stats) return <p>Chargement…</p>;
  return (
    <div className='space-y-6'>
      <h2 className='text-2xl font-bold'>Tableau de bord</h2>
      <div className='grid grid-cols-2 gap-4 lg:grid-cols-4'>
        <Stat titre='Médicaments' valeur={stats.total_medicaments} couleur='text-teal-700' />
        <Stat titre='Ruptures' valeur={stats.ruptures.length} couleur='text-red-600' />
        <Stat titre='Stock bas' valeur={stats.stock_bas.length} couleur='text-orange-500' />
        <Stat titre='Lots expirés' valeur={stats.nb_expires} couleur='text-red-700' />
      </div>

      <div className={card}>
        <h3 className='mb-2 font-semibold'>Lots expirés ou expirant sous 90 jours</h3>
        <table className='w-full text-sm'>
          <thead className='bg-slate-100'>
            <tr><th className={th}>Médicament</th><th className={th}>Lot</th><th className={th}>Quantité</th><th className={th}>Expiration</th><th className={th}>Jours</th></tr>
          </thead>
          <tbody>
            {stats.lots_a_surveiller.map((l) => (
              <tr key={l.lot_id} className='border-t'>
                <td className={td}>{l.medicament}</td>
                <td className={td}>{l.numero_lot}</td>
                <td className={td}>{l.quantite}</td>
                <td className={td}>{fmt(l.date_expiration)}</td>
                <td className={td + (l.jours_restants < 0 ? ' font-bold text-red-700' : l.jours_restants <= 30 ? ' font-bold text-orange-600' : '')}>
                  {l.jours_restants < 0 ? 'Expiré' : l.jours_restants}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {stats.lots_a_surveiller.length === 0 && <p className='p-3 text-sm text-slate-500'>Aucun lot à surveiller.</p>}
      </div>

      <div className={card}>
        <h3 className='mb-2 font-semibold'>Notifications</h3>
        <ul className='space-y-2'>
          {notifs.map((n) => (
            <li key={n.id} className={`flex items-center justify-between rounded p-2 text-sm ${n.lue ? 'bg-slate-50 text-slate-400' : 'bg-amber-50'}`}>
              <span>{n.message}</span>
              {!n.lue && <button className='text-xs text-teal-700 underline' onClick={() => lue(n.id)}>Marquer lue</button>}
            </li>
          ))}
        </ul>
        {notifs.length === 0 && <p className='text-sm text-slate-500'>Aucune notification.</p>}
      </div>
    </div>
  );
}