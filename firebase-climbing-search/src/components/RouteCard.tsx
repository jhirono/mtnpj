import React from 'react';
import { Route } from '../types';
import './RouteCard.css';

interface RouteCardProps {
  route: Route;
}

const RouteCard: React.FC<RouteCardProps> = ({ route }) => {
  // Calculate star display
  const renderStars = () => {
    const stars = [];
    const fullStars = Math.floor(route.route_stars);
    const hasHalfStar = route.route_stars % 1 >= 0.5;
    
    for (let i = 0; i < fullStars; i++) {
      stars.push(<span key={`star-${i}`} className="star full-star">★</span>);
    }
    
    if (hasHalfStar) {
      stars.push(<span key="half-star" className="star half-star">★</span>);
    }
    
    const emptyStars = 4 - stars.length;
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<span key={`empty-${i}`} className="star empty-star">☆</span>);
    }
    
    return stars;
  };

  // Generate route type badges
  const renderTypeLabels = () => {
    const types = [];
    
    if (route.is_trad) {
      types.push(<span key="trad" className="type-badge trad">Trad</span>);
    }
    
    if (route.is_sport) {
      types.push(<span key="sport" className="type-badge sport">Sport</span>);
    }
    
    if (route.is_multipitch) {
      types.push(<span key="multipitch" className="type-badge multipitch">Multipitch</span>);
    }
    
    return types;
  };

  return (
    <div className="route-card">
      <div className="route-header">
        <h3 className="route-name">{route.route_name}</h3>
        <div className="route-grade">{route.route_grade}</div>
      </div>
      
      <div className="route-details">
        <div className="route-stars">
          {renderStars()}
          <span className="route-votes">({route.route_votes})</span>
        </div>
        
        <div className="route-type-badges">
          {renderTypeLabels()}
        </div>
      </div>
      
      <div className="route-location">
        <strong>Location:</strong> {route.area_name}
      </div>
      
      {route.route_description && (
        <div className="route-description">
          <p>{route.route_description.length > 150 
            ? `${route.route_description.substring(0, 150)}...` 
            : route.route_description}
          </p>
        </div>
      )}
    </div>
  );
};

export default RouteCard; 