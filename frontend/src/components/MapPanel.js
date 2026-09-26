import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function MapPanel({ center = [0, 20], markers = [], route = null, height = 420 }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layersRef = useRef([]);
  const initialViewRef = useRef({ center, zoom: markers.length ? 8 : 3 });

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined;

    const initialView = initialViewRef.current;
    const map = L.map(containerRef.current, { scrollWheelZoom: false })
      .setView([Number(initialView.center[1]), Number(initialView.center[0])], initialView.zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);
    L.control.scale({ imperial: false }).addTo(map);
    mapRef.current = map;
    map.whenReady(() => map.invalidateSize());

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    layersRef.current.forEach(layer => layer.remove());
    layersRef.current = [];
    const bounds = [];

    markers.forEach(marker => {
      const latitude = Number(marker.lat);
      const longitude = Number(marker.lng);
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return;
      const icon = L.divIcon({
        className: '',
        html: '<span style="display:block;width:14px;height:14px;border:2px solid white;border-radius:50%;background:#087f8c;box-shadow:0 1px 4px #222"></span>',
        iconSize: [18, 18],
        iconAnchor: [9, 9],
      });
      const popup = document.createElement('span');
      popup.textContent = marker.label || 'Saved place';
      const layer = L.marker([latitude, longitude], { icon }).bindPopup(popup).addTo(map);
      layersRef.current.push(layer);
      bounds.push([latitude, longitude]);
    });

    if (route?.coordinates?.length > 1) {
      const coordinates = route.coordinates
        .filter(point => Array.isArray(point) && Number.isFinite(Number(point[0])) && Number.isFinite(Number(point[1])))
        .map(([longitude, latitude]) => [Number(latitude), Number(longitude)]);
      if (coordinates.length > 1) {
        const layer = L.polyline(coordinates, { color: '#d1495b', weight: 4, opacity: 0.8 }).addTo(map);
        layersRef.current.push(layer);
        bounds.push(...coordinates);
      }
    }

    if (bounds.length) map.fitBounds(bounds, { padding: [32, 32], maxZoom: 12 });
  }, [markers, route]);

  return <div ref={containerRef} style={{ width: '100%', height, borderRadius: 12, overflow: 'hidden', border: '1px solid var(--border)', background: '#e8f1ed' }} />;
}
