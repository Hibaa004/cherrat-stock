import { useEffect, useState } from 'react';
import api, { errMsg } from '../api.js';
import { useAuth } from '../auth.jsx';
import { btn, card, fmt, input, td, th } from '../ui.js';

const VIDE = { nom: '', dci: '', forme: '', dosage: '', categorie: '', seuil_alerte: 10 };

export default function Medicaments() {
  const { user } = useAuth();
  const [meds, setMeds] = useState([]);
  const [q, setQ] = useState('');
  const [form, setForm] = useState(VIDE);
  const [erreur, setErreur] = useState('');

  const charger = () => api.get('/medicaments', { params: { q: q || undefined } }).then((r) => setMeds(r.data));
  useEffect(() => {
    charger();
  }, [q]);

  const creer = async (e) => {
    e.preventDefault();
    setErreur('');
    try {
      await api.post('/medicaments', { ...form, seuil_alerte: Number(form.seuil_alerte) });
      setForm(VIDE);
      charger();
    } catch (err) {
      setErreur(errMsg(err));
    }
  };

  return (
    <div className='space-y-6'>
      <h2 className='text-2xl font-bold'>Médicaments</h2>
      <input className={input + ' max-w-sm'} placeholder='Rechercher (nom ou DCI)…' value={q} onChange={(e) => setQ(e.target.value)} />

      {user.role === 'major' && (
        <form onSubmit={creer} className={card + ' grid grid-cols-2 gap-3 lg:grid-cols-6'}>
          {['nom', 'dci', 'forme', 'dosage', 'categorie'].map((c) => (
            <input key={c} className={input} placeholder={c} value={form[c]} onChange={(e) => setForm({ ...form, [c]: e.target.value })} required={c === 'nom'} />
          ))}
          <input className={input} type='number' min='0' placeholder='Seuil' value={form.seuil_alerte} onChange={(e) => setForm({ ...form, seuil_alerte: e.target.value })} />
          <button className={btn + ' col-span-2 lg:col-span-6'}>Ajouter le médicament</button>
          {erreur && <p className='col-span-full text-sm text-red-600'>{erreur}</p>}
        </form>
      )}

      <div className={card}>
        <table className='w-full text-sm'>
          <thead className='bg-slate-100'>
            <tr><th className={th}>Nom</th><th className={th}>DCI</th><th className={th}>Forme</th><th className={th}>Stock</th><th className={th}>Prochaine expiration</th></tr>
          </thead>
          <tbody>
            {meds.map((m) => (
              <tr key={m.id} className='border-t'>
                <td className={td + ' font-medium'}>{m.nom}</td>
                <td className={td}>{m.dci}</td>
                <td className={td}>{m.forme} {m.dosage}</td>
                <td className={td + (m.stock_total === 0 ? ' font-bold text-red-600' : m.stock_total <= m.seuil_alerte ? ' font-bold text-orange-500' : '')}>{m.stock_total}</td>
                <td className={td}>{fmt(m.prochaine_expiration)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}