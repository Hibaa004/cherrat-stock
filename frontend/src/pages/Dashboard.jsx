import { useEffect, useState } from 'react';
import api from '../api.js';
import { card, fmt, td, th } from '../ui.js';

const Stat = ({ titre, valeur, couleur }) => (
  <div className={card}>
    <p className='text-sm text-slate-500'>{titre}</p>
    <p className={`text-3xl font-bold ${couleur}`}>{valeur}</p>
  </div>
);

const SOURCES = {
  ia: (m) => `Actions rédigées par l'IA locale (${m}). Vérifiez-les avec les données calculées avant d'agir.`,
  repli: () => "L'assistant IA (Ollama) n'a pas répondu : seules les données calculées sont affichées.",
  sans_alerte: () => 'Aucune alerte : rien à faire aujourd’hui.',
};

function RapportDuJour({ rapport }) {
  const [details, setDetails] = useState(false);
  if (!rapport) {
    return (
      <div className={card + ' border-l-4 border-slate-300'}>
        <h3 className='font-semibold'>Rapport du jour (IA)</h3>
        <p className='mt-1 text-sm text-slate-500'>Aucun rapport reçu. Il est publié chaque matin à 8 h 15 par le workflow n8n.</p>
      </div>
    );
  }
  const couleur = rapport.nb_alertes === 0 ? 'border-green-500' : rapport.source === 'repli' ? 'border-orange-400' : 'border-teal-600';
  return (
    <div className={`${card} border-l-4 ${couleur} space-y-3`}>
      <div className='flex flex-wrap items-baseline justify-between gap-2'>
        <h3 className='font-semibold'>Rapport du jour (IA)</h3>
        <span className={`text-xs ${rapport.du_jour ? 'text-slate-500' : 'font-semibold text-orange-600'}`}>
          {rapport.du_jour ? '' : 'Pas de rapport aujourd’hui — dernier rapport : '}
          {fmt(rapport.date)} · mis à jour à {new Date(rapport.mis_a_jour).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      <p className='font-semibold'>{rapport.synthese}</p>
      {rapport.actions && (
        <div>
          <p className='text-sm font-medium text-slate-600'>Actions prioritaires</p>
          <p className='mt-1 whitespace-pre-wrap text-sm'>{rapport.actions}</p>
        </div>
      )}
      <p className='text-xs text-slate-500'>{(SOURCES[rapport.source] || SOURCES.repli)(rapport.modele)}</p>
      {rapport.faits && (
        <div>
          <button className='text-xs text-teal-700 underline' onClick={() => setDetails(!details)}>
            {details ? 'Masquer' : 'Afficher'} les données calculées par l’application
          </button>
          {details && <pre className='mt-2 whitespace-pre-wrap rounded bg-slate-50 p-3 text-xs'>{rapport.faits}</pre>}
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [notifs, setNotifs] = useState([]);
  const [rapport, setRapport] = useState(null);

  const charger = () => {
    api.get('/stock/dashboard').then((r) => setStats(r.data));
    api.get('/notifications').then((r) => setNotifs(r.data));
    api.get('/automation/dernier-rapport').then((r) => setRapport(r.data)).catch(() => {});
  };
  useEffect(() => {
    charger();
  }, []);

  const lue = (id) => api.post(`/notifications/${id}/lue`).then(charger);

  if (!stats) return <p>Chargement…</p>;
  return (
    <div className='space-y-6'>
      <h2 className='text-2xl font-bold'>Tableau de bord</h2>
      <RapportDuJour rapport={rapport} />
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