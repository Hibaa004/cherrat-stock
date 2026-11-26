import { useRef, useEffect, useState } from 'react';
import api, { errMsg } from '../api.js';
import { useAuth } from '../auth.jsx';
import { btn, card, input } from '../ui.js';

export default function Assistant() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([
    { role: 'ia', texte: 'Bonjour ! Posez-moi une question sur le stock (ex. Quels lots expirent bientôt ?).' },
  ]);
  const [question, setQuestion] = useState('');
  const [attente, setAttente] = useState(false);
  const bas = useRef(null);

  useEffect(() => {
    bas.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const envoyer = async (e) => {
    e.preventDefault();
    const q = question.trim();
    if (q.length < 3) return;
    setMessages((m) => [...m, { role: 'user', texte: q }]);
    setQuestion('');
    setAttente(true);
    try {
      const r = await api.post('/chat', { question: q });
      setMessages((m) => [...m, { role: 'ia', texte: r.data.reponse, sources: r.data.sources }]);
    } catch (err) {
      setMessages((m) => [...m, { role: 'ia', texte: 'Erreur : ' + errMsg(err) }]);
    } finally {
      setAttente(false);
    }
  };

  const reindexer = async () => {
    try {
      const r = await api.post('/chat/reindex');
      alert(r.data.fiches_indexees + ' fiche(s) indexée(s)');
    } catch (err) {
      alert(errMsg(err));
    }
  };

  return (
    <div className='mx-auto max-w-3xl space-y-4'>
      <div className='flex items-center justify-between'>
        <h2 className='text-2xl font-bold'>Assistant IA</h2>
        {user.role === 'major' && <button className={btn} onClick={reindexer}>Réindexer le stock</button>}
      </div>
      <div className={card + ' h-[60vh] space-y-3 overflow-auto'}>
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : ''}>
            <p className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${m.role === 'user' ? 'bg-teal-700 text-white' : 'bg-slate-100'}`}>{m.texte}</p>
            {m.sources?.length > 0 && <p className='mt-1 text-xs text-slate-400'>Sources : {m.sources.join(', ')}</p>}
          </div>
        ))}
        {attente && <p className='text-sm text-slate-400'>L’assistant réfléchit…</p>}
        <div ref={bas} />
      </div>
      <form onSubmit={envoyer} className='flex gap-2'>
        <input className={input} placeholder='Votre question…' value={question} onChange={(e) => setQuestion(e.target.value)} />
        <button className={btn} disabled={attente}>Envoyer</button>
      </form>
      <p className='text-xs text-slate-400'>L’assistant consulte le stock ; il ne remplace ni le médecin ni le pharmacien.</p>
    </div>
  );
}