"""
Phase 6: Geo-Temporal Patterning

DBSCAN/HDBSCAN, Isolation Forest, HMMs for geo-temporal patterns.
"""

import logging
from typing import Any, Dict, List

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.models.scraped_data import ScrapedData

logger = logging.getLogger(__name__)


class Phase6Geospatial:
    """Handles geo-temporal patterning analysis."""

    async def execute(self, scraped_items: List[ScrapedData]) -> Dict[str, Any]:
        """DBSCAN/HDBSCAN, Isolation Forest, HMMs for geo-temporal patterns."""
        # Extract location data from metadata with timestamps
        location_data = []  # List of (lat, lon, timestamp) tuples

        for item in scraped_items:
            if item.metadata:
                coords = None
                # Try to extract coordinates
                if "coordinates" in item.metadata:
                    coords = item.metadata.get("coordinates")
                    if isinstance(coords, dict):
                        lat = coords.get("lat") or coords.get("latitude")
                        lon = coords.get("lon") or coords.get("lng") or coords.get("longitude")
                        if lat is not None and lon is not None:
                            location_data.append((float(lat), float(lon), item.scrapedAt))
                    elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
                        location_data.append((float(coords[0]), float(coords[1]), item.scrapedAt))
                elif "geo" in item.metadata:
                    geo = item.metadata.get("geo")
                    if isinstance(geo, dict):
                        lat = geo.get("lat") or geo.get("latitude")
                        lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")
                        if lat is not None and lon is not None:
                            location_data.append((float(lat), float(lon), item.scrapedAt))

        if len(location_data) < 3:
            return {
                "hasGeospatialData": len(location_data) > 0,
                "routineZones": [],
                "anomalies": [],
                "locationCount": len(location_data),
            }

        # Extract coordinates and timestamps
        coordinates = np.array([[lat, lon] for lat, lon, _ in location_data])
        timestamps = [ts for _, _, ts in location_data]

        # Normalize coordinates for clustering
        scaler = StandardScaler()
        coordinates_scaled = scaler.fit_transform(coordinates)

        routine_zones = []
        anomalies = []

        # 1. DBSCAN Clustering for routine zones
        try:
            # Use DBSCAN to find clusters (routine zones)
            dbscan = DBSCAN(eps=0.5, min_samples=2)
            cluster_labels = dbscan.fit_predict(coordinates_scaled)

            # Group locations by cluster
            clusters = {}
            for idx, label in enumerate(cluster_labels):
                if label != -1:  # -1 is noise in DBSCAN
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append((coordinates[idx][0], coordinates[idx][1], timestamps[idx]))

            # Create routine zones from clusters
            for cluster_id, points in clusters.items():
                if len(points) >= 2:
                    # Calculate cluster center
                    lats = [p[0] for p in points]
                    lons = [p[1] for p in points]
                    center_lat = np.mean(lats)
                    center_lon = np.mean(lons)
                    # Calculate radius (max distance from center)
                    distances = [
                        np.sqrt((lat - center_lat) ** 2 + (lon - center_lon) ** 2) for lat, lon, _ in points
                    ]
                    radius = max(distances) if distances else 0.0

                    routine_zones.append({
                        "center": {"lat": float(center_lat), "lon": float(center_lon)},
                        "radius": float(radius),
                        "visitCount": len(points),
                        "firstVisit": min(ts for _, _, ts in points).isoformat(),
                        "lastVisit": max(ts for _, _, ts in points).isoformat(),
                    })

            # Anomalies are points labeled as -1 (noise) by DBSCAN
            anomaly_indices = [idx for idx, label in enumerate(cluster_labels) if label == -1]
            for idx in anomaly_indices:
                anomalies.append({
                    "lat": float(coordinates[idx][0]),
                    "lon": float(coordinates[idx][1]),
                    "timestamp": timestamps[idx].isoformat(),
                })

        except Exception as e:
            logger.warning(f"DBSCAN clustering failed: {e}")

        # 2. Isolation Forest for additional anomaly detection
        try:
            if len(coordinates_scaled) >= 4:
                iso_forest = IsolationForest(contamination=0.2, random_state=42)
                anomaly_labels = iso_forest.fit_predict(coordinates_scaled)

                # Add additional anomalies detected by Isolation Forest
                for idx, label in enumerate(anomaly_labels):
                    if label == -1:  # Anomaly
                        # Check if not already in anomalies list
                        point = {
                            "lat": float(coordinates[idx][0]),
                            "lon": float(coordinates[idx][1]),
                            "timestamp": timestamps[idx].isoformat(),
                        }
                        # Avoid duplicates
                        if not any(
                            abs(a["lat"] - point["lat"]) < 0.001 and abs(a["lon"] - point["lon"]) < 0.001
                            for a in anomalies
                        ):
                            anomalies.append(point)
        except Exception as e:
            logger.warning(f"Isolation Forest failed: {e}")

        # 3. HMM for Pattern-of-Life analysis
        pattern_of_life = None
        try:
            from hmmlearn import hmm

            if len(location_data) >= 5 and len(routine_zones) >= 2:
                # Prepare sequence: map locations to zone IDs
                zone_sequence = []
                for lat, lon, _ in location_data:
                    # Find closest routine zone
                    min_dist = float("inf")
                    closest_zone = -1
                    for zone_idx, zone in enumerate(routine_zones):
                        center = zone["center"]
                        dist = np.sqrt((lat - center["lat"]) ** 2 + (lon - center["lon"]) ** 2)
                        if dist < min_dist:
                            min_dist = dist
                            closest_zone = zone_idx
                    zone_sequence.append(closest_zone)

                # Train HMM
                n_states = min(3, len(routine_zones))
                model = hmm.GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=100)
                # Reshape for HMM (needs 2D array)
                observations = np.array([[lat, lon] for lat, lon, _ in location_data])
                model.fit(observations)

                # Get transition probabilities
                transition_matrix = model.transmat_
                # Calculate pattern regularity (lower entropy = more regular)
                entropy = 0.0
                for row in transition_matrix:
                    for prob in row:
                        if prob > 0:
                            entropy -= prob * np.log2(prob + 1e-10)

                pattern_of_life = {
                    "regularity": float(1.0 / (1.0 + entropy)),  # Normalize to 0-1
                    "stateCount": n_states,
                    "transitionMatrix": transition_matrix.tolist(),
                }
        except ImportError:
            logger.debug("hmmlearn not available, skipping HMM analysis")
        except Exception as e:
            logger.warning(f"HMM analysis failed: {e}")

        return {
            "hasGeospatialData": True,
            "routineZones": routine_zones[:10],  # Limit to top 10 zones
            "anomalies": anomalies[:20],  # Limit to top 20 anomalies
            "locationCount": len(location_data),
            "patternOfLife": pattern_of_life,
        }
