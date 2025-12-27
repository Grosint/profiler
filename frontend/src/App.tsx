import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ProfileCreate from './pages/ProfileCreate';
import ProfileDetail from './pages/ProfileDetail';
import PostDetail from './pages/PostDetail';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<ProfileCreate />} />
          <Route path="/profiles/:profileId" element={<ProfileDetail />} />
          <Route path="/posts/:postId" element={<PostDetail />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
