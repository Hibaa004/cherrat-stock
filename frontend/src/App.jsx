import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './auth.jsx';
import Layout from './components/Layout.jsx';
import Login from './pages/Login.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Medicaments from './pages/Medicaments.jsx';
import Entree from './pages/Entree.jsx';
import Sortie from './pages/Sortie.jsx';
import Assistant from './pages/Assistant.jsx';
import Users from './pages/Users.jsx';

function Protected({ roles, children }) {
  const { user, loading } = useAuth();
  if (loading) return <p className='p-6'>Chargement…</p>;
  if (!user) return <Navigate to='/login' replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to='/' replace />;
  return children;
}

const EDITEURS = ['major', 'infirmier'];

export default function App() {
  return (
    <Routes>
      <Route path='/login' element={<Login />} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path='medicaments' element={<Medicaments />} />
        <Route path='entree' element={<Protected roles={EDITEURS}><Entree /></Protected>} />
        <Route path='sortie' element={<Protected roles={EDITEURS}><Sortie /></Protected>} />
        <Route path='assistant' element={<Assistant />} />
        <Route path='utilisateurs' element={<Protected roles={['major']}><Users /></Protected>} />
      </Route>
    </Routes>
  );
}