import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getRecommendations, getLocationSuggestions } from '../api';

const STEPS = [
  {
    id: 'user_name',
    icon: '👋',
    title: "What's your name?",
    sub: "We'll personalize your trip recommendations just for you.",
    type: 'text',
    placeholder: 'Enter your name...',
  },
  {
    id: 'budget',
    icon: '💰',
    title: 'What is your budget?',
    sub: 'Select your total travel budget for this trip.',
    type: 'budget',
    choices: ['Under 20,000', '20,000 – 50,000', '50,000 – 1,00,000', '1,00,000 – 3,00,000', '3,00,000+'],
    currencies: ['INR', 'USD', 'EUR', 'GBP', 'AED'],
  },
  {
    id: 'group_type',
    icon: '👥',
    title: 'Solo or Group?',
    sub: 'Tell us who will be joining you on this adventure.',
    type: 'choice',
    choices: [
      { icon: '🧍', label: 'Solo' },
      { icon: '💑', label: 'Couple' },
      { icon: '👨‍👩‍👧‍👦', label: 'Family' },
      { icon: '👫', label: 'Friends Group' },
    ],
  },
  {
    id: 'travel_scope',
    icon: '🌍',
    title: 'Domestic or International?',
    sub: 'Are you looking to explore within your country or venture abroad?',
    type: 'choice',
    choices: [
      { icon: '🇮🇳', label: 'Domestic Only' },
      { icon: '✈️', label: 'International' },
      { icon: '🌐', label: 'Both are fine' },
      { icon: '🎲', label: 'Surprise Me!' },
    ],
  },
  {
    id: 'num_days',
    icon: '📅',
    title: 'How many days?',
    sub: 'How long do you plan to travel?',
    type: 'number',
    min: 1,
    max: 60,
    default: 7,
  },
  {
    id: 'food_accommodation',
    icon: '🏨',
    title: 'Food & Accommodation?',
    sub: 'What are your food and stay preferences?',
    type: 'multi',
    choices: [
      { icon: '🍛', label: 'Vegetarian' },
      { icon: '🥩', label: 'Non-Vegetarian' },
      { icon: '🌮', label: 'Local Street Food' },
      { icon: '🍽️', label: 'Restaurant Dining' },
      { icon: '🏕️', label: 'Budget Hostel' },
      { icon: '🏨', label: 'Mid-Range Hotel' },
      { icon: '🏖️', label: 'Luxury Resort' },
      { icon: '🏠', label: 'Airbnb / Homestay' },
    ],
  },
  {
    id: 'departure_location',
    icon: '📍',
    title: 'Where are you departing from?',
    sub: 'Enter your city or location for accurate travel options.',
    type: 'autocomplete',
    placeholder: 'e.g. Mumbai, Delhi, Bangalore...',
  },
  {
    id: 'travel_medium',
    icon: '🚀',
    title: 'How do you prefer to travel?',
    sub: 'Select your preferred mode of transport.',
    type: 'choice',
    choices: [
      { icon: '✈️', label: 'Flight' },
      { icon: '🚂', label: 'Train' },
      { icon: '🚗', label: 'Road Trip' },
      { icon: '🚌', label: 'Bus' },
      { icon: '🚢', label: 'Cruise / Ship' },
      { icon: '🔀', label: 'Any / Mix' },
    ],
  },
  {
    id: 'destination_style',
    icon: '🎨',
    title: 'What kind of trip excites you?',
    sub: 'Select all travel styles that appeal to you (multiple allowed).',
    type: 'multi',
    choices: [
      { icon: '🏖️', label: 'Beach & Relaxation' },
      { icon: '🧗', label: 'Adventure & Trekking' },
      { icon: '🏛️', label: 'Culture & Heritage' },
      { icon: '🍜', label: 'Food & Nightlife' },
      { icon: '🌿', label: 'Nature & Wildlife' },
      { icon: '💎', label: 'Luxury & Spa' },
      { icon: '🎭', label: 'Festivals & Events' },
      { icon: '📸', label: 'Photography' },
      { icon: '🏔️', label: 'Himalayan / Snow' },
      { icon: '🏜️', label: 'Desert & Dunes' },
      { icon: '🌊', label: 'Water Sports' },
      { icon: '🙏', label: 'Spiritual & Wellness' },
    ],
  },
];

function TripPlanner() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({
    user_name: '',
    budget: '',
    currency: 'INR',
    group_type: '',
    travel_scope: '',
    num_days: 7,
    food_preference: [],
    accommodation: [],
    departure_location: '',
    travel_medium: '',
    destination_style: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const autocompleteTimer = useRef(null);
  const currentStep = STEPS[step];

  const updateAnswer = (key, value) => {
    setAnswers(prev => ({ ...prev, [key]: value }));
    setError('');
  };

  const handleAutocomplete = (query) => {
    updateAnswer('departure_location', query);
    clearTimeout(autocompleteTimer.current);
    if (query.length > 1) {
      autocompleteTimer.current = setTimeout(async () => {
        try {
          const results = await getLocationSuggestions(query);
          setSuggestions(results);
          setShowSuggestions(true);
        } catch {
          setSuggestions([]);
        }
      }, 400);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const validateStep = () => {
    const s = currentStep;
    if (s.id === 'user_name' && !answers.user_name.trim()) return 'Please enter your name.';
    if (s.id === 'budget' && !answers.budget) return 'Please select a budget range.';
    if (s.id === 'group_type' && !answers.group_type) return 'Please select group type.';
    if (s.id === 'travel_scope' && !answers.travel_scope) return 'Please select travel scope.';
    if (s.id === 'departure_location' && !answers.departure_location.trim()) return 'Please enter your departure location.';
    if (s.id === 'travel_medium' && !answers.travel_medium) return 'Please select a travel medium.';
    if (s.id === 'destination_style' && answers.destination_style.length === 0) return 'Please select at least one travel style.';
    return '';
  };

  const nextStep = async () => {
    const err = validateStep();
    if (err) { setError(err); return; }

    if (step < STEPS.length - 1) {
      setStep(step + 1);
      setError('');
    } else {
      // Submit
      await handleSubmit();
    }
  };

  const prevStep = () => {
    if (step > 0) { setStep(step - 1); setError(''); }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const tripData = {
        user_name: answers.user_name,
        budget: answers.budget,
        currency: answers.currency,
        group_type: answers.group_type,
        travel_scope: answers.travel_scope,
        num_days: answers.num_days,
        food_preference: answers.food_preference.join(', '),
        accommodation: answers.accommodation.join(', '),
        departure_location: answers.departure_location,
        travel_medium: answers.travel_medium,
        destination_style: answers.destination_style.join(', '),
      };
      const result = await getRecommendations(tripData);
      navigate('/results', { state: { result, tripData } });
    } catch (err) {
      setError('Something went wrong. Please check your connection and try again.');
      setLoading(false);
    }
  };

  const toggleMulti = (key, value) => {
    setAnswers(prev => {
      const arr = prev[key] || [];
      return {
        ...prev,
        [key]: arr.includes(value) ? arr.filter(v => v !== value) : [...arr, value]
      };
    });
  };

  const renderStepContent = () => {
    const s = currentStep;

    if (s.type === 'text') {
      return (
        <input
          type="text"
          className="step-input"
          placeholder={s.placeholder}
          value={answers[s.id] || ''}
          onChange={e => updateAnswer(s.id, e.target.value)}
          onKeyDown={e => e.key === 'Enter' && nextStep()}
          autoFocus
        />
      );
    }

    if (s.type === 'budget') {
      return (
        <div>
          <div className="budget-row" style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 13, color: 'var(--text-secondary)', marginRight: 8 }}>Currency:</label>
            <select
              className="currency-select"
              value={answers.currency}
              onChange={e => updateAnswer('currency', e.target.value)}
            >
              {s.currencies.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div className="choices-grid cols-1">
            {s.choices.map((c, i) => (
              <button
                key={i}
                className={`choice-btn ${answers.budget === c ? 'selected' : ''}`}
                onClick={() => updateAnswer('budget', c)}
              >
                <span className="choice-icon">💵</span>
                <span className="choice-label">{answers.currency} {c}</span>
                <span className="choice-check">{answers.budget === c ? '✓' : ''}</span>
              </button>
            ))}
          </div>
        </div>
      );
    }

    if (s.type === 'choice') {
      const colClass = s.choices.length === 6 ? 'cols-3' : '';
      return (
        <div className={`choices-grid ${colClass}`}>
          {s.choices.map((c, i) => {
            const label = typeof c === 'string' ? c : c.label;
            const icon = typeof c === 'object' ? c.icon : '';
            const val = label;
            return (
              <button
                key={i}
                className={`choice-btn ${answers[s.id] === val ? 'selected' : ''}`}
                onClick={() => updateAnswer(s.id, val)}
              >
                {icon && <span className="choice-icon">{icon}</span>}
                <span className="choice-label">{label}</span>
                <span className="choice-check">{answers[s.id] === val ? '✓' : ''}</span>
              </button>
            );
          })}
        </div>
      );
    }

    if (s.type === 'number') {
      return (
        <div>
          <div className="num-input-wrapper">
            <button className="num-btn" onClick={() => updateAnswer('num_days', Math.max(s.min, answers.num_days - 1))}>−</button>
            <div className="num-display">{answers.num_days}</div>
            <button className="num-btn" onClick={() => updateAnswer('num_days', Math.min(s.max, answers.num_days + 1))}>+</button>
          </div>
          <p style={{ marginTop: 12, fontSize: 13, color: 'var(--text-secondary)' }}>
            {answers.num_days} day{answers.num_days !== 1 ? 's' : ''} trip planned
          </p>
        </div>
      );
    }

    if (s.type === 'multi') {
      // Split food/accommodation
      const isFoodAccom = s.id === 'food_accommodation';
      const selectedFood = answers.food_preference || [];
      const selectedAccom = answers.accommodation || [];

      return (
        <div>
          <div className="multi-hint">💡 Select all that apply</div>
          <div className="choices-grid cols-3" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            {s.choices.map((c, i) => {
              const label = typeof c === 'object' ? c.label : c;
              const icon = typeof c === 'object' ? c.icon : '';
              let isSelected;
              let toggleFn;
              if (isFoodAccom) {
                const isFood = ['Vegetarian','Non-Vegetarian','Local Street Food','Restaurant Dining'].includes(label);
                isSelected = isFood ? selectedFood.includes(label) : selectedAccom.includes(label);
                toggleFn = () => toggleMulti(isFood ? 'food_preference' : 'accommodation', label);
              } else {
                isSelected = (answers[s.id] || []).includes(label);
                toggleFn = () => toggleMulti(s.id, label);
              }
              return (
                <button
                  key={i}
                  className={`choice-btn ${isSelected ? 'selected' : ''}`}
                  onClick={toggleFn}
                  style={{ flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 6 }}
                >
                  <span style={{ fontSize: 22 }}>{icon}</span>
                  <span style={{ fontSize: 12 }}>{label}</span>
                </button>
              );
            })}
          </div>
        </div>
      );
    }

    if (s.type === 'autocomplete') {
      return (
        <div className="autocomplete-wrapper">
          <input
            type="text"
            className="step-input"
            placeholder={s.placeholder}
            value={answers.departure_location}
            onChange={e => handleAutocomplete(e.target.value)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            autoFocus
          />
          {showSuggestions && suggestions.length > 0 && (
            <div className="autocomplete-dropdown">
              {suggestions.map((s, i) => (
                <div
                  key={i}
                  className="autocomplete-item"
                  onClick={() => {
                    updateAnswer('departure_location', s);
                    setShowSuggestions(false);
                  }}
                >
                  📍 {s}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <div className="loading-overlay">
        <div className="loading-spinner" />
        <div className="loading-title">Finding your perfect destinations<span className="loading-dots"><span>.</span><span>.</span><span>.</span></span></div>
        <div className="loading-sub">Google Gemini AI is analyzing your preferences</div>
      </div>
    );
  }

  return (
    <div className="planner-wrapper">
      <div className="planner-container">
        {/* Header */}
        <div className="planner-header">
          <Link to="/" style={{ textDecoration: 'none', color: 'var(--primary)', fontSize: 14, fontWeight: 600 }}>
            ← Back to Home
          </Link>
          <h1 style={{ marginTop: 12 }}>🧭 Plan Your Trip</h1>
          <p>Answer a few questions and let AI find your perfect destination</p>
        </div>

        {/* Progress bar */}
        <div className="progress-bar-wrapper">
          <div className="progress-steps">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`progress-step ${i === step ? 'active' : i < step ? 'done' : ''}`}
              />
            ))}
          </div>
          <div className="progress-info">
            <span>Step {step + 1} of {STEPS.length}</span>
            <span>{Math.round(((step + 1) / STEPS.length) * 100)}% complete</span>
          </div>
        </div>

        {/* Step card */}
        <div className="step-card">
          <div className="step-icon">{currentStep.icon}</div>
          <h2>{currentStep.title}</h2>
          <p className="step-sub">{currentStep.sub}</p>
          {renderStepContent()}
          {error && <div className="error-msg" style={{ marginTop: 16 }}>⚠️ {error}</div>}
          <div className="step-nav">
            <button
              className="btn btn-ghost"
              onClick={prevStep}
              style={{ visibility: step === 0 ? 'hidden' : 'visible' }}
            >
              ← Back
            </button>
            <button className="btn btn-primary" onClick={nextStep}>
              {step === STEPS.length - 1 ? 'Get My AI Recommendations ✨' : 'Continue →'}
            </button>
          </div>
        </div>

        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: 'var(--text-light)' }}>
          Powered by Google Gemini AI · Smart Trip AI by Arman Ansari
        </p>
      </div>
    </div>
  );
}

export default TripPlanner;
