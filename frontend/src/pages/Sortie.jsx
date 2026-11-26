import { useEffect, useState } from 'react';
import api, { errMsg } from '../api.js';
import { btn, card, input, td, th } from '../ui.js';

export default function Sortie() {
  const [meds, setMeds] = useState([]);
  const [mouvements, setMouvements] = useState([]);
  const [form, setForm] = useState({ medicament_id: '', quantite: '', motif: '' });
  const [msg, setMsg] = useState(null);

  const charger = () => {
    api.get('/medicaments').then((r) => setMeds(r.data));
    api.get('/stock/mouvements').then((r) => setMouvements(r.data));
  };
  useEffect(() => {
    charger();
  }, []);

  const valider = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api.post('/stock/sortie', { medicament_id: Number(form.medicament_id), quantite: Number(form.quantite), motif: form.motif });
      setMsg({ ok: true, texte: 'Sortie enregistrée.' });
      setForm({ medicament_id: '', quantite: '', motif: '' });
      charger();
    } catch (err) {
      setMsg({ ok: false, texte: errMsg(err) });
    }
  };

  return (
    <div className='space-y-6'>
      <h2 className='text-2xl font-bold'>Sortie de stock</h2>
      <form onSubmit={valider} className={card + ' grid max-w-2xl gap-3'}>
        <select className={input} value={form.medicament_id} onChange={(e) => setForm({ ...form, medicament_id: e.target.value })} required>
          <option value=''>Choisir un médicament…</option>
          {meds.map((m) => (
            <option key={m.id} value={m.id}>{m.nom} (stock : {m.stock_total})</option>
          ))}
        </select>
        <input className={input} type='number' min='1' placeholder='Quantité' value={form.quantite} onChange={(e) => setForm({ ...form, quantite: e.target.value })} required />
        <input className={input} placeholder='Motif (ex. dispensation, service urgences)' value={form.motif} onChange={(e) => setForm({ ...form, motif: e.target.value })} />
        <button className={btn}>Valider la sortie</button>
        {msg && <p className={msg.ok ? 'text-sm text-green-700' : 'text-sm text-red-600'}>{msg.texte}</p>}
      </form>

      <div className={card}>
        <h3 className='mb-2 font-semibold'>Derniers mouvements</h3>
        <table className='w-full text-sm'>
          <thead className='bg-slate-100'>
            <tr><th className={th}>Date</th><th className={th}>Type</th><th className={th}>Médicament</th><th className={th}>Lot</th><th className={th}>Qté</th><th className={th}>Par</th></tr>
          </thead>
          <tbody>
            {mouvements.map((m) => (
              <tr key={m.id} className='border-t'>
                <td className={td}>{new Date(m.date).toLocaleString('fr-FR')}</td>
                <td className={td}>{m.type}</td>
                <td className={td}>{m.medicament}</td>
                <td className={td}>{m.lot}</td>
                <td className={td}>{m.quantite}</td>
                <td className={td}>{m.utilisateur}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}