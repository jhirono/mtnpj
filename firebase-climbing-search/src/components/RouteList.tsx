import React, { useState, useEffect } from 'react';
import { Route, RouteFilters, SortConfig, PaginationState } from '../types';
import { getRoutesForAreas } from '../firebase.js';
import RouteCard from './RouteCard';
import './RouteList.css';

interface RouteListProps {
  selectedAreaIds: string[];
  filters: RouteFilters;
  sortConfig: SortConfig;
}

const RouteList: React.FC<RouteListProps> = ({ selectedAreaIds, filters, sortConfig }) => {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [pagination, setPagination] = useState<PaginationState>({
    lastVisible: null,
    hasMore: false,
    loading: false
  });
  const [error, setError] = useState<string | null>(null);

  // Load routes when selection or filters change
  useEffect(() => {
    const loadRoutes = async () => {
      if (selectedAreaIds.length === 0) {
        setRoutes([]);
        setPagination({ lastVisible: null, hasMore: false, loading: false });
        return;
      }

      try {
        setPagination(prev => ({ ...prev, loading: true }));
        setError(null);
        
        console.log("Loading routes for areas:", selectedAreaIds);
        console.log("With filters:", filters);
        console.log("And sort config:", sortConfig);

        const routesData = await getRoutesForAreas(
          { ...filters, areaIds: selectedAreaIds },
          sortConfig
        );

        console.log("Routes loaded:", routesData.routes.length);
        setRoutes(routesData.routes);
        setPagination({
          lastVisible: routesData.lastVisible,
          hasMore: routesData.hasMore,
          loading: false
        });
      } catch (error) {
        console.error('Error loading routes:', error);
        setError('Failed to load routes. Please try again.');
        setPagination(prev => ({ ...prev, loading: false }));
      }
    };

    loadRoutes();
  }, [selectedAreaIds, filters, sortConfig]);

  // Load more routes
  const handleLoadMore = async () => {
    if (!pagination.hasMore || pagination.loading) return;

    try {
      setPagination(prev => ({ ...prev, loading: true }));

      const routesData = await getRoutesForAreas(
        { ...filters, areaIds: selectedAreaIds },
        sortConfig,
        pagination.lastVisible
      );

      setRoutes(prev => [...prev, ...routesData.routes]);
      setPagination({
        lastVisible: routesData.lastVisible,
        hasMore: routesData.hasMore,
        loading: false
      });
    } catch (error) {
      console.error('Error loading more routes:', error);
      setError('Failed to load more routes. Please try again.');
      setPagination(prev => ({ ...prev, loading: false }));
    }
  };

  if (selectedAreaIds.length === 0) {
    return (
      <div className="route-list-container">
        <h2>Routes</h2>
        <div className="route-list-empty">
          <p>Please select an area to see routes</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="route-list-container">
        <h2>Routes</h2>
        <div className="route-list-error">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="route-list-container">
      <h2>Routes {routes.length > 0 && `(${routes.length})`}</h2>
      
      {pagination.loading && routes.length === 0 ? (
        <div className="route-list-loading">
          <p>Loading routes...</p>
        </div>
      ) : routes.length === 0 ? (
        <div className="route-list-empty">
          <p>No routes found for this area</p>
          <p>Try selecting a different area or adjusting your filters</p>
        </div>
      ) : (
        <>
          <div className="route-list">
            {routes.map(route => (
              <RouteCard key={route.id} route={route} />
            ))}
          </div>
          
          {pagination.hasMore && (
            <div className="load-more">
              <button 
                onClick={handleLoadMore}
                disabled={pagination.loading}
                className="load-more-button"
              >
                {pagination.loading ? 'Loading...' : 'Load More Routes'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RouteList; 