import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function ArticleDetail({ article, onBack }) {
  const [detail, setDetail] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchArticleDetail = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_URL}/api/article-detail`, article);
      if (response.data.status === 'success') {
        setDetail(response.data);
      } else {
        setError('Failed to load article details');
      }
    } catch {
      setError('Error fetching article details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [article]);

  useEffect(() => {
    fetchArticleDetail();
  }, [fetchArticleDetail]);

  return (
    <section className="article-detail-section">
      <button onClick={onBack} className="back-btn">
        ← Back to Articles
      </button>

      {isLoading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading article details...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {detail && !isLoading && (
        <div className="article-detail-content">
          <h1>{detail.title}</h1>

          <div className="article-meta-detail">
            <span className="source">{detail.source}</span>
            <span className="date">{detail.date}</span>
            <span className="relevance">{Math.round(detail.relevance_score * 100)}% Relevant</span>
          </div>

          <div className="article-links">
            <a href={detail.link} target="_blank" rel="noopener noreferrer" className="read-full-btn">
              Read Full Article
            </a>
          </div>

          <div className="article-section">
            <h2>Summary</h2>
            <p>{detail.snippet}</p>
          </div>

          <div className="article-section">
            <h2>Key Points</h2>
            <ol className="five-points">
              {detail.five_point_summary && detail.five_point_summary.map((point, index) => (
                <li key={index}>
                  {/* Remove numbering from the point if it already has it */}
                  {point.replace(/^\d+\.\s*/, '')}
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </section>
  );
}

export default ArticleDetail;
