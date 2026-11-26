import { useEffect, useState } from 'react';
import api, { errMsg } from '../api.js';
import { btn, card, input, td, th } from '../ui.js';

const VIDE = { nom: '', email: '', password: '', role: 'infirmier' };

export default function Users() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(VIDE);
  const [erreur, setErreur] = useState('');

  const charger = () => api.get('/users').then((r) => setUsers(r.data));
  useEffect(() => {
    charger();
  }, []);

  const creer = async (e) => {
    e.preventDefault();
    setErreur('');
    try {
      await api.post('/users', form);
      setForm(VIDE);
      charger();
    } catch (err) {
      setErreur(errMsg(err));
    }
  };

  const basculer = (id) => api.patch(`/users/${id}/actif`).then(charger);

  return (
    <div className='space-y-6'>
      <h2 className='text-2xl font-bold'>Utilisateurs</h2>
      <form onSubmit={creer} className={card + ' grid grid-cols-2 gap-3 lg:grid-cols-5'}>
        <input className={input} placeholder='Nom' value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} required />
        <input className={input} type='email' placeholder='Email' value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input className={input} type='password' placeholder='Mot de passe (8 car. min.)' value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} />
        <select className={input} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          <option value='infirmier'>Infirmier</option>
          <option value='docteur'>Docteur</option>
          <option value='major'>Major</option>
        </select>
        <button className={btn}>Créer</button>
        {erreur && <p className='col-span-full text-sm text-red-600'>{erreur}</p>}
      </form>
      <div className={card}>
        <table className='w-full text-sm'>
          <thead className='bg-slate-100'>
            <tr><th className={th}>Nom</th><th className={th}>Email</th><th className={th}>Rôle</th><th className={th}>Actif</th><th className={th}></th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className='border-t'>
                <td className={td}>{u.nom}</td>
                <td className={td}>{u.email}</td>
                <td className={td}>{u.role}</td>
                <td className={td}>{u.actif ? 'Oui' : 'Non'}</td>
                <td className={td}><button className='text-teal-700 underline' onClick={() => basculer(u.id)}>{u.actif ? 'Désactiver' : 'Activer'}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}