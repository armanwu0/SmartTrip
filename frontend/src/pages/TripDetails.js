import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import {
  getTrip,
  getTripConversations,
  getTripExpenses,
  getTripItinerary,
  getTripRoutes,
  getPersistentSavedTrips,
  savePersistentTrip,
} from '../api';
import MapPanel from '../components/MapPanel';

function TripDetails() {
  const { tripId } = useParams();
  const { isLoggedIn, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [trip, setTrip] = useState(null);
  const [itinerary, setItinerary] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      navigate('/auth');
      return;
    }

    let active = true;
    Promise.all([
      getTrip(tripId),
      getTripItinerary(tripId),
      getTripRoutes(tripId),
      getTripExpenses(tripId),
      getTripConversations(),
      getPersistentSavedTrips(),
    ])
      .then(([tripData, days, routeData, expenseData, conversationData, savedData]) => {
        if (!active) return;
        setTrip(tripData);
        setItinerary(days);
        setRoutes(routeData);
        setExpenses(expenseData);
        setConversations(conversationData.filter(item => String(item.trip) === String(tripId)));
        setSaved((savedData.results || []).some(item => String(item.trip?.id) === String(tripId)));
      })
      .catch(() => {
        if (active) setError('This trip could not be loaded. It may not belong to your account.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [tripId, isLoggedIn, authLoading, navigate]);

  const handleSave = async () => {
    try {
      const result = await savePersistentTrip(tripId);
      setSaved(Boolean(result.saved));
    } catch {
      setError('The trip could not be saved.');
    }
  };

  if (authLoading || loading) return <main style={{ maxWidth: 1080, margin: '40px auto', padding: 20 }}>Loading trip…</main>;
  if (error || !trip) {
    return (
      <main style={{ maxWidth: 1080, margin: '40px auto', padding: 20 }}>
        <p role="alert">{error || 'Trip not found.'}</p>
        <Link to="/dashboard" className="btn btn-ghost">Back to My Trips</Link>
      </main>
    );
  }

  const items = itinerary.flatMap(day => day.items || []);
  const markers = items
    .filter(item => item.place && item.place.latitude != null && item.place.longitude != null)
    .map(item => ({
      lat: item.place.latitude,
      lng: item.place.longitude,
      label: item.place.name,
    }));
  const route = routes.find(item => item.route_data?.coordinates?.length > 1);
  const center = markers.length ? [Number(markers[0].lng), Number(markers[0].lat)] : [0, 20];
  const spent = expenses.reduce((total, expense) => total + Number(expense.amount || 0), 0);
  const remaining = Number(trip.total_budget || 0) - spent;
  const currency = trip.currency || 'INR';
  const money = value => `${currency} ${Number(value || 0).toLocaleString('en-IN')}`;

  return (
    <main style={{ maxWidth: 1080, margin: '0 auto', padding: '28px 20px 56px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
        <Link to="/dashboard" className="btn btn-ghost">← My Trips</Link>
        <button type="button" className="btn btn-primary" onClick={handleSave} disabled={saved}>
          {saved ? '✓ Saved' : 'Save Trip'}
        </button>
      </div>

      <header style={{ borderBottom: '1px solid var(--border)', paddingBottom: 20, marginBottom: 24 }}>
        <h1 style={{ fontSize: 30, margin: '0 0 8px' }}>{trip.trip_name}</h1>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
          {trip.source || 'Origin not specified'} → {trip.destination} · {trip.number_of_travelers} travelers · {trip.start_date} to {trip.end_date}
        </p>
      </header>

      <section aria-label="Trip budget" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 30 }}>
        <div><strong>Planned budget</strong><div>{money(trip.total_budget)}</div></div>
        <div><strong>Estimated expenses</strong><div>{money(spent)}</div></div>
        <div><strong>{remaining < 0 ? 'Over budget' : 'Remaining'}</strong><div>{money(Math.abs(remaining))}</div></div>
        <div><strong>Provider-verified places</strong><div>{new Set(markers.map(item => `${item.lat},${item.lng}`)).size}</div></div>
      </section>

      <section style={{ marginBottom: 34 }}>
        <h2>Map</h2>
        <MapPanel center={center} markers={markers} route={route ? { coordinates: route.route_data.coordinates } : null} height={380} />
      </section>

      <section style={{ marginBottom: 34 }}>
        <h2>Routes</h2>
        {routes.length ? routes.map(item => (
          <div key={item.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
            <strong>{item.origin} → {item.destination}</strong>
            <div>{item.distance || 'Distance unavailable'} · {item.duration || 'Duration unavailable'} · {item.transport_mode} · {item.provider || 'Provider unavailable'}</div>
          </div>
        )) : <p>No verified route was available for this trip.</p>}
      </section>

      <section style={{ marginBottom: 34 }}>
        <h2>Itinerary</h2>
        {itinerary.length ? itinerary.map(day => (
          <article key={day.id} style={{ padding: '16px 0', borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ margin: '0 0 8px' }}>Day {day.day_number}{day.date ? ` · ${day.date}` : ''}</h3>
            {day.title && <p>{day.title}</p>}
            {day.items?.length ? <ol>
              {day.items.map(item => (
                <li key={item.id} style={{ marginBottom: 10 }}>
                  <strong>{item.start_time && `${item.start_time} · `}{item.activity_name}</strong>
                  {item.place && <div>
                    {item.place.name} · {item.place.source || 'Place provider unavailable'}
                    {item.place.external_place_id && ` · ${item.place.external_place_id}`}
                    {item.place.rating != null && ` · Rating ${item.place.rating}`}
                  </div>}
                  {Number(item.estimated_cost) > 0 && <div>{money(item.estimated_cost)}</div>}
                </li>
              ))}
            </ol> : <p>No activities stored for this day.</p>}
          </article>
        )) : <p>No itinerary has been saved.</p>}
      </section>

      <section style={{ marginBottom: 34 }}>
        <h2>Expenses</h2>
        {expenses.length ? expenses.map(expense => (
          <div key={expense.id} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
            <span>{expense.category} · {expense.description} · {expense.status} · {expense.source}</span>
            <strong>{money(expense.amount)}</strong>
          </div>
        )) : <p>No expense rows have been saved.</p>}
      </section>

      <section>
        <h2>AI Conversation</h2>
        {conversations.length ? conversations.map(item => (
          <article key={item.id} style={{ padding: '14px 0', borderBottom: '1px solid var(--border)' }}>
            <p><strong>You</strong><br />{item.user_message}</p>
            <p><strong>SmartTrip AI</strong><br />{item.ai_response}</p>
            <small>{item.provider} · {item.model} · {new Date(item.created_at).toLocaleString()}</small>
          </article>
        )) : <p>No AI conversation is linked to this trip.</p>}
      </section>
    </main>
  );
}

export default TripDetails;
