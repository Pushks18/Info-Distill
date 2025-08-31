import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [prompt, setPrompt] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [articles, setArticles] = useState([]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!prompt || !recipientEmail) {
      setStatus('Please enter a prompt and a recipient email.');
      return;
    }
    
    setIsLoading(true);
    setArticles([]);
    setStatus('Processing your request...');

    try {
      // Call the new single endpoint with all necessary info
      const response = await axios.post('http://localhost:8000/api/process', {
        prompt,
        recipient_email: recipientEmail
      });

      if (response.data.status === 'success') {
        setArticles(response.data.articles);
        setStatus(response.data.message);
      } else {
        setStatus(response.data.message);
      }
    } catch (error) {
      setStatus('An error occurred. Please check the backend console.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>AI Article Intelligence Service</h1>
      <p>Enter a prompt to find relevant articles and automatically receive an AI-generated report via email.</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="prompt">Your Prompt</label>
          <input
            type="text" id="prompt" value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., latest AI breakthroughs"
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Recipient's Email</label>
          <input
            type="email" id="email" value={recipientEmail}
            onChange={(e) => setRecipientEmail(e.target.value)}
            placeholder="e.g., colleague@example.com"
          />
        </div>
        
        <button type="submit" disabled={isLoading}>
          {isLoading ? <><div className="spinner"></div> Processing...</> : 'Find & Send Report'}
        </button>
      </form>

      {status && <div className="status">{status}</div>}

      {articles.length > 0 && (
        <div className="results-container">
          <h2>Relevant Articles Found</h2>
          {articles.map((article, index) => (
            <div className="article-card" key={index}>
              <div className="article-header">
                <h3><a href={article.link} target="_blank" rel="noopener noreferrer">{article.title}</a></h3>
                <span className="relevance-score">
                  {Math.round(article.relevance_score * 100)}% Relevant
                </span>
              </div>
              <p className="article-source">Source: {article.source} | Published: {article.date}</p>
              <p className="article-snippet">{article.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;