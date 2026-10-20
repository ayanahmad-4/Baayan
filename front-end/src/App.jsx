import './index.css';
import './App.css';
import { ChatPage } from './components/ChatPage';

/**
 * Root app — supports standalone and embedded modes.
 * Add ?embed=1 to the URL to use compact embed mode.
 */
function App() {
  const isEmbed = new URLSearchParams(window.location.search).get('embed') === '1';
  return <ChatPage embed={isEmbed} />;
}

export default App;
