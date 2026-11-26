import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { errMsg } from '../api.js';
import { useAuth } from '../auth.jsx';
import { btn, input } from '../ui.js';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(errMsg(err));
    }
  };

  return (
    <div className='flex min-h-screen items-center justify-center bg-slate-100'>
      <form onSubmit={submit} className='w-96 space-y-4 rounded-lg bg-white p-8 shadow'>
        <h1 className='text-xl font-bold text-teal-800'>Centre de Santé Cherrat</h1>
        <p className='text-sm text-slate-500'>Gestion du stock de médicaments</p>
        {error && <p className='rounded bg-red-50 p-2 text-sm text-red-700'>{error}</p>}
        <input className={input} type='email' placeholder='Email' value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className={input} type='password' placeholder='Mot de passe' value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button className={btn + ' w-full'}>Se connecter</button>
      </form>
    </div>
  );
}