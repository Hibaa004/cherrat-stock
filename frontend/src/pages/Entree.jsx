import { useEffect, useState } from 'react';
import api, { errMsg } from '../api.js';
import { btn, card, input } from '../ui.js';

const VIDE = { medicament_id: '', numero_lot: '', date_expiration: '', quantite: '' };

export default function Entree() {
  const [meds, setMeds] = useState([]);
  const [form, setForm] = useState(VIDE);
  const [ocr, setOcr] = useState(null);
  const [imagePath, setImagePath] = useState(null);
  const [apercu, setApercu] = useState(null);
  const [scanEnCours, setScanEnCours] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    api.get('/medicaments').then((r) => setMeds(r.data));
  }, []);

  const champ = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const scanner = async (e) => {
    const fichier = e.target.files[0];
    if (!fichier) return;
    setApercu(URL.createObjectURL(fichier));
    setScanEnCours(true);
    setMsg(null);
    const data = new FormData();
    data.append('file', fichier);
    try {
      const r = await api.post('/ocr/scan', data);
      setOcr(r.data);
      setImagePath(r.data.image_path);
      if (r.data.date_expiration) setForm((f) => ({ ...f, date_expiration: r.data.date_expiration }));
    } catch (err) {
      setMsg({ ok: false, texte: errMsg(err) });
    } finally {
      setScanEnCours(false);
    }
  };

  const valider = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api.post('/stock/entree', {
        medicament_id: Number(form.medicament_id),
        numero_lot: form.numero_lot,
        date_expiration: form.date_expiration,
        quantite: Number(form.quantite),
        image_path: imagePath,
      });
      setMsg({ ok: true, texte: 'Entrée enregistrée.' });
      setForm(VIDE);
      setOcr(null);
      setApercu(null);
      setImagePath(null);
    } catch (err) {
      setMsg({ ok: false, texte: errMsg(err) });
    }
  };

  return (
    <div className='space-y-6'>
      <h2 className='text-2xl font-bold'>Entrée de stock</h2>
      <div className='grid gap-6 lg:grid-cols-2'>
        <div className={card + ' space-y-3'}>
          <h3 className='font-semibold'>1. Photographier la boîte (facultatif)</h3>
          <input type='file' accept='image/*' capture='environment' onChange={scanner} />
          {apercu && <img src={apercu} alt='Aperçu' className='max-h-64 rounded' />}
          {scanEnCours && <p className='text-sm text-slate-500'>Lecture de l’image en cours…</p>}
          {ocr && (
            <div className='rounded bg-slate-50 p-3 text-sm'>
              <p>
                Date détectée : <b>{ocr.date_expiration || 'aucune'}</b> (confiance : {ocr.confiance})
              </p>
              <p className='mt-1 text-xs text-slate-500'>Texte lu : {ocr.texte_brut.join(' | ')}</p>
            </div>
          )}
        </div>

        <form onSubmit={valider} className={card + ' space-y-3'}>
          <h3 className='font-semibold'>2. Vérifier et enregistrer</h3>
          <select className={input} value={form.medicament_id} onChange={champ('medicament_id')} required>
            <option value=''>Choisir un médicament…</option>
            {meds.map((m) => (
              <option key={m.id} value={m.id}>{m.nom}</option>
            ))}
          </select>
          <input className={input} placeholder='Numéro de lot' value={form.numero_lot} onChange={champ('numero_lot')} required />
          <label className='block text-xs text-slate-500'>Date d’expiration</label>
          <input className={input} type='date' value={form.date_expiration} onChange={champ('date_expiration')} required />
          <input className={input} type='number' min='1' placeholder='Quantité reçue' value={form.quantite} onChange={champ('quantite')} required />
          <button className={btn}>Enregistrer l’entrée</button>
          {msg && <p className={msg.ok ? 'text-sm text-green-700' : 'text-sm text-red-600'}>{msg.texte}</p>}
        </form>
      </div>
    </div>
  );
}