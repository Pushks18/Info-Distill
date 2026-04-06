import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ArticleDetail from './ArticleDetail';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [prompt, setPrompt] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [articles, setArticles] = useState([]);
  const [streamedText, setStreamedText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedArticles, setSelectedArticles] = useState([]);
  const [isCreatingDoc, setIsCreatingDoc] = useState(false);
  const [docUrl, setDocUrl] = useState('');
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedArticleDetail, setSelectedArticleDetail] = useState(null);

  useEffect(() => {
    if (docUrl) {
      setCurrentStep(3);
      return;
    }
    if (articles.length > 0) {
      setCurrentStep(2);
      return;
    }
    setCurrentStep(1);
  }, [articles, docUrl]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!prompt) {
      setStatus('Enter a topic to start discovery.');
      return;
    }

    setIsLoading(true);
    setCurrentStep(1);
    setArticles([]);
    setStreamedText('');
    setSelectedArticles([]);
    setDocUrl('');
    setStatus('Discovering and ranking articles...');

    try {
      const response = await axios.post(`${API_URL}/api/process`, {
        prompt,
        recipient_email: ''
      });

      if (response.data.status === 'success') {
        setArticles(response.data.articles);
        setStatus(`Found ${response.data.articles.length} ranked articles.`);
        startStreaming();
      } else {
        setStatus(response.data.message);
      }
    } catch {
      setStatus('Request failed. Check backend logs and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const startStreaming = () => {
    setIsStreaming(true);
    setStatus('Generating newsletter brief...');
    const eventSource = new EventSource(`${API_URL}/api/stream-newsletter?prompt=${encodeURIComponent(prompt)}`);
    eventSource.onmessage = (event) => {
      setStreamedText(prev => prev + event.data);
    };
    eventSource.onerror = () => {
      setIsStreaming(false);
      setStatus('Newsletter brief complete.');
      eventSource.close();
    };
    eventSource.onopen = () => {
      setStreamedText('');
    };
  };

  const handleArticleSelect = (article, isSelected) => {
    if (isSelected) {
      setSelectedArticles(prev => [...prev, article]);
    } else {
      setSelectedArticles(prev => prev.filter(a => a.link !== article.link));
    }
  };

  const handleArticleClick = (article) => {
    setSelectedArticleDetail(article);
  };

  const handleCreateDoc = async () => {
    if (selectedArticles.length === 0) {
      setStatus('Select at least one article to continue.');
      return;
    }
    if (!recipientEmail) {
      setStatus('Enter recipient email in the final send panel.');
      return;
    }

    setIsCreatingDoc(true);
    setStatus('Generating and sending report...');

    try {
      const response = await axios.post(`${API_URL}/api/create-doc`, {
        selected_articles: selectedArticles,
        recipient_email: recipientEmail
      });

      if (response.data.status === 'success') {
        setDocUrl(response.data.doc_url);
        setStatus('Report generated and sent successfully.');
      } else {
        setStatus(response.data.message);
      }
    } catch {
      setStatus('Failed to create report. Please retry.');
    } finally {
      setIsCreatingDoc(false);
    }
  };

  const resetApp = () => {
    setPrompt('');
    setRecipientEmail('');
    setStatus('');
    setArticles([]);
    setStreamedText('');
    setIsStreaming(false);
    setSelectedArticles([]);
    setIsCreatingDoc(false);
    setDocUrl('');
    setSelectedArticleDetail(null);
    setCurrentStep(1);
  };

  return (
    <div className="App">
      {selectedArticleDetail ? (
        <ArticleDetail
          article={selectedArticleDetail}
          onBack={() => setSelectedArticleDetail(null)}
        />
      ) : (
        <>
          <header className="app-header">
            <div className="header-content">
              <h1>Info Distill</h1>
              <p>Discover, rank, and curate industry intelligence reports.</p>
            </div>
            {currentStep > 1 && (
              <button onClick={resetApp} className="reset-btn" title="Start new search">
                New Search
              </button>
            )}
          </header>

          <main className="app-main">
            <section className="stepper">
              <span className={`step-pill ${currentStep >= 1 ? 'active' : ''}`}>1. Topic</span>
              <span className={`step-pill ${currentStep >= 2 ? 'active' : ''}`}>2. Select Articles</span>
              <span className={`step-pill ${currentStep >= 3 ? 'active' : ''}`}>3. Send Report</span>
            </section>

            {currentStep === 1 && (
              <form onSubmit={handleSubmit} className="search-form card">
                <div className="form-group">
                  <label htmlFor="prompt">Research Topic</label>
                  <input
                    type="text"
                    id="prompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="e.g. computer vision for manufacturing quality control"
                    required
                  />
                </div>
                <button type="submit" disabled={isLoading} className="submit-btn">
                  {isLoading ? <><div className="spinner"></div>Analyzing...</> : 'Discover Articles'}
                </button>
              </form>
            )}

            {status && (
              <div className={`status ${status.toLowerCase().includes('success') ? 'success' : 'info'}`}>
                {status}
              </div>
            )}

            {isStreaming && (
              <section className="streaming-section card">
                <h2>Newsletter Brief</h2>
                <div className="streamed-text">{streamedText || 'Preparing brief...'}</div>
              </section>
            )}

            {articles.length > 0 && (
              <section className="results-section">
                <div className="section-top">
                  <h2>Ranked Articles</h2>
                  <p>{selectedArticles.length} selected</p>
                </div>
                <div className="articles-grid">
                  {articles.map((article, index) => {
                    const selected = selectedArticles.some(a => a.link === article.link);
                    return (
                      <article
                        className={`article-card ${selected ? 'selected' : ''}`}
                        key={index}
                        onClick={() => handleArticleClick(article)}
                      >
                        <div className="article-header">
                          <div className="checkbox-container" onClick={(e) => e.stopPropagation()}>
                            <input
                              type="checkbox"
                              id={`article-${index}`}
                              checked={selected}
                              onChange={(e) => handleArticleSelect(article, e.target.checked)}
                            />
                            <label htmlFor={`article-${index}`}>Include</label>
                          </div>
                          <span className="confidence-score">
                            {Math.round((article.relevance_confidence || 0) * 100)}% keyword-match confidence
                          </span>
                        </div>
                        <h3>
                          <a
                            href={article.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {article.title}
                          </a>
                        </h3>
                        <p className="article-meta">
                          <span>{article.source}</span>
                          <span>{article.date}</span>
                        </p>
                        <p className="article-snippet">{article.snippet}</p>
                        {article.matched_terms?.length > 0 && (
                          <p className="match-debug">
                            Terms: {article.matched_terms.slice(0, 5).join(', ')}
                          </p>
                        )}
                      </article>
                    );
                  })}
                </div>
              </section>
            )}

            {articles.length > 0 && (
              <section className="send-panel card">
                <h2>Send Report</h2>
                <p>Enter recipient after finalizing selected articles.</p>
                <div className="send-row">
                  <input
                    type="email"
                    value={recipientEmail}
                    onChange={(e) => setRecipientEmail(e.target.value)}
                    placeholder="recipient@company.com"
                  />
                  <button
                    onClick={handleCreateDoc}
                    disabled={isCreatingDoc || selectedArticles.length === 0 || !recipientEmail}
                    className="create-doc-btn"
                  >
                    {isCreatingDoc ? <><div className="spinner"></div>Sending...</> : `Generate & Send Report (${selectedArticles.length})`}
                  </button>
                </div>
              </section>
            )}

            {docUrl && (
              <section className="doc-section card">
                <h2>Report Ready</h2>
                <a href={docUrl} target="_blank" rel="noopener noreferrer" className="doc-link-btn">
                  Open Google Doc
                </a>
                <p className="doc-info">Sent to {recipientEmail}</p>
              </section>
            )}
          </main>
        </>
      )}
    </div>
  );
}

export default App;