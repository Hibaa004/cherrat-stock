import { useEffect, useState } from 'react';
import api, { errMsg } from '../api.js';
import { btn, card, fmt, input } from '../ui.js';

const VIDE = { medicament_id: '', numero_lot: '', date_expiration: '', quantite: '' };
// champ rempli par l'OCR : fond jaune « à vérifier » (on retire le fond blanc et la bordure grise par défaut)
const AUTO = input.replace('bg-white', 'bg-amber-50').replace('border-slate-300', 'border-amber-400');

function Detection({ label, valeur, detail }) {
  return (
    <li className='flex items-start gap-2'>
      <span className={valeur ? 'text-green-700' : 'text-slate-400'}>{valeur ? '✔' : '—'}</span>
      <span>
        <span className='text-slate-500'>{label} : </span>
        {valeur ? <b>{valeur}</b> : <span className='text-slate-500'>non détecté, à saisir</span>}
        {detail && <span className='text-xs text-slate-500'> ({detail})</span>}
      </span>
    </li>
  );
}

export default function Entree() {
  const [meds, setMeds] = useState([]);
  const [form, setForm] = useState(VIDE);
  const [auto, setAuto] = useState({}); // champs remplis automatiquement et pas encore modifiés
  const [unites, setUnites] = useState(''); // unités dans une boîte
  const [boites, setBoites] = useState('1');
  const [ocr, setOcr] = useState(null);
  const [imagePath, setImagePath] = useState(null);
  const [apercu, setApercu] = useState(null);
  const [scanEnCours, setScanEnCours] = useState(false);
  const [msg, setMsg] = useState(null);
  // date locale au format AAAA-MM-JJ (le format « sv-SE » l'écrit ainsi)
  const [aujourdhui] = useState(() => new Date().toLocaleDateString('sv-SE'));

  useEffect(() => {
    api.get('/medicaments').then((r) => setMeds(r.data));
  }, []);

  const champ = (k) => (e) => {
    setForm({ ...form, [k]: e.target.value });
    setAuto({ ...auto, [k]: false });
  };

  const calculerQuantite = (nbBoites, nbUnites) => {
    const q = Number(nbBoites) * Number(nbUnites);
    if (q > 0) setForm((f) => ({ ...f, quantite: String(q) }));
  };

  const scanner = async (e) => {
    const fichier = e.target.files[0];
    if (!fichier) return;
    setApercu(URL.createObjectURL(fichier));
    setScanEnCours(true);
    setOcr(null);
    setMsg(null);
    const data = new FormData();
    data.append('file', fichier);
    try {
      const { data: r } = await api.post('/ocr/scan', data);
      setOcr(r);
      setImagePath(r.image_path);
      const u = r.unites_par_boite ? String(r.unites_par_boite) : '';
      setUnites(u);
      setBoites('1');
      setForm({
        medicament_id: r.medicament_id ? String(r.medicament_id) : '',
        numero_lot: r.numero_lot || '',
        date_expiration: r.date_expiration || '',
        quantite: u,
      });
      setAuto({
        medicament_id: !!r.medicament_id,
        numero_lot: !!r.numero_lot,
        date_expiration: !!r.date_expiration,
        quantite: !!u,
      });
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
      setAuto({});
      setUnites('');
      setBoites('1');
      setOcr(null);
      setApercu(null);
      setImagePath(null);
    } catch (err) {
      setMsg({ ok: false, texte: errMsg(err) });
    }
  };

  const cls = (k) => (auto[k] ? AUTO : input);
  const expire = form.date_expiration && form.date_expiration < aujourdhui;
  const nbAuto = Object.values(auto).filter(Boolean).length;

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
            <div className='space-y-2 rounded bg-slate-50 p-3 text-sm'>
              <p className='font-medium'>Informations détectées</p>
              <ul className='space-y-1'>
                <Detection label='Médicament' valeur={ocr.medicament} detail={ocr.medicament ? `confiance ${ocr.medicament_confiance}` : null} />
                <Detection label='N° de lot' valeur={ocr.numero_lot} />
                <Detection label='Date d’expiration' valeur={ocr.date_expiration && fmt(ocr.date_expiration)} detail={ocr.date_expiration ? `confiance ${ocr.confiance}` : null} />
                <Detection label='Contenu d’une boîte' valeur={ocr.unites_par_boite && `${ocr.unites_par_boite} unité(s)`} />
              </ul>
              {ocr.avertissement && <p className='rounded bg-amber-100 p-2 text-amber-900'>⚠ {ocr.avertissement}</p>}
              <details className='text-xs text-slate-500'>
                <summary className='cursor-pointer'>Texte lu par l’OCR</summary>
                {ocr.texte_brut.join(' | ')}
              </details>
            </div>
          )}
        </div>

        <form onSubmit={valider} className={card + ' space-y-3'}>
          <h3 className='font-semibold'>2. Vérifier et enregistrer</h3>
          {nbAuto > 0 && (
            <p className='rounded border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900'>
              Les champs en jaune ont été remplis automatiquement : vérifiez-les avec la boîte avant d’enregistrer.
            </p>
          )}
          <label className='block text-xs text-slate-500'>Médicament</label>
          <select className={cls('medicament_id')} value={form.medicament_id} onChange={champ('medicament_id')} required>
            <option value=''>Choisir un médicament…</option>
            {meds.map((m) => (
              <option key={m.id} value={m.id}>{m.nom}</option>
            ))}
          </select>
          <label className='block text-xs text-slate-500'>Numéro de lot</label>
          <input className={cls('numero_lot')} placeholder='Numéro de lot' value={form.numero_lot} onChange={champ('numero_lot')} required />
          <label className='block text-xs text-slate-500'>Date d’expiration</label>
          <input className={cls('date_expiration')} type='date' value={form.date_expiration} onChange={champ('date_expiration')} required />
          {expire && <p className='text-sm font-semibold text-red-600'>⚠ Ce lot est déjà expiré : il ne doit pas être mis en stock.</p>}
          <div className='grid grid-cols-2 gap-3'>
            <div>
              <label className='block text-xs text-slate-500'>Nombre de boîtes reçues</label>
              <input
                className={input}
                type='number'
                min='1'
                value={boites}
                onChange={(e) => {
                  setBoites(e.target.value);
                  calculerQuantite(e.target.value, unites);
                }}
              />
            </div>
            <div>
              <label className='block text-xs text-slate-500'>Unités par boîte</label>
              <input
                className={auto.quantite && unites ? AUTO : input}
                type='number'
                min='1'
                placeholder='ex. 20'
                value={unites}
                onChange={(e) => {
                  setUnites(e.target.value);
                  calculerQuantite(boites, e.target.value);
                }}
              />
            </div>
          </div>
          <label className='block text-xs text-slate-500'>Quantité reçue (unités) = boîtes × unités par boîte</label>
          <input className={cls('quantite')} type='number' min='1' placeholder='Quantité reçue' value={form.quantite} onChange={champ('quantite')} required />
          <button className={btn}>Enregistrer l’entrée</button>
          {msg && <p className={msg.ok ? 'text-sm text-green-700' : 'text-sm text-red-600'}>{msg.texte}</p>}
        </form>
      </div>
    </div>
  );
}
